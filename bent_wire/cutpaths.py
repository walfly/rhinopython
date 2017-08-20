
import rhinoscriptsyntax as rs
import math
import re
import json
import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

POINTS_ON_CROSS_SECTION = rs.GetReal("Set nodes per cross section", 10) * 2
should_spiral = rs.GetBoolean('Spiral Pattern?',('spiral', 'no', 'yes'), (True))

def size_vector(vector, number):
    return rs.VectorScale(rs.VectorUnitize(vector), number)

def square_pipe(curve, plane, point, index):
    c1 = rs.CopyObject(curve)
    c2 = rs.CopyObject(curve)
    s = rs.CurveStartPoint(curve)
    dblParam = rs.CurveClosestPoint(curve, s)
    pp = rs.CurvePerpFrame(curve, dblParam)
    inter = rs.PlanePlaneIntersection(plane, pp)
    vec = rs.VectorCreate(inter[0], inter[1])
    uvz = rs.VectorUnitize(plane.ZAxis)
    uvz = rs.VectorScale(uvz, 0.125)
    if index % 2 == 0:
        uvz = rs.VectorReverse(uvz)
    uvy = rs.VectorUnitize(vec)
    uvy = rs.VectorScale(uvy, 0.0625)
    rs.MoveObject(c1, uvy)
    rs.MoveObject(c2, rs.VectorReverse(uvy))
    s1 = rs.CurveStartPoint(c1)
    s2 = rs.CurveStartPoint(c2)

    p1 = rs.PointAdd(s1, uvz)
    p2 = rs.PointAdd(s2, uvz)

    l1 = rs.AddLine(s1, p1)
    l2 = rs.AddLine(s2, p2)
    s1 = rs.ExtrudeCurve(c1, l1)
    s2 = rs.ExtrudeCurve(c2, l2)

    return [s1, s2, c1,c2]


def receiverSrf(nextpartpoint, c1, c2):
    ps1 = rs.PolylineVertices(c1)
    ps2 = rs.PolylineVertices(c2)
    len1 = len(ps1)
    len2 = len(ps2)
    p = rs.PlaneFromPoints(ps1[len1-1], ps1[len1-2], ps2[len2-1])
    point = rs.PlaneClosestPoint(p, nextpartpoint, return_point=True)
    pl = rs.PlaneFromFrame(point, p.XAxis, p.YAxis)
    return pl


class JointPiece:

  def __init__(self, point1, point2, point3, point4, cp, index, indexes, curve_object, flat_length, distance_apart, count):
    self.point1 = point1
    self.point2 = point2
    self.point3 = point3
    self.point4 = point4
    if should_spiral[0] and index == 0:
        self.point1 = point2
        self.point2 = point3
        self.point3 = point4
        self.point4 = point1
    self.curve_object = curve_object
    self.flat_length = flat_length + 0.15
    self.distance_apart = distance_apart + 0.15
    self.index = index
    self.indexes = indexes
    self.count = count
    self.cp = cp
    self.p1 = rs.PlaneFromPoints(self.point1, self.point2, self.point3)
    self.p2 = rs.PlaneFromPoints(self.point2, self.point1, self.point3)
    self.p3 = rs.PlaneFromPoints(self.point3, self.point2, self.point4)
    self.p4 = rs.PlaneFromPoints(self.point4, self.point2, self.point3)
    rs.AddText("point1", self.point1, 0.25)
    rs.AddText("point2", self.point2, 0.25)
    rs.AddText("point3", self.point3, 0.25)
    rs.AddText("point4", self.point4, 0.25)
    self.c1 = rs.AddCircle(self.p1, 0.25)
    self.c2 = rs.AddCircle(self.p2, 0.25)
    self.c3 = rs.AddCircle(self.p3, 0.25)
    self.c4 = rs.AddCircle(self.p4, 0.25)

  def buildDiscs(self, p1, c1, forward, three):
    w = -0.25
    h = -0.25
    if forward:
        w = 0.25
        h = 0.25
    if three:
        w = -0.25
        h = 0.25
    rect = rs.AddRectangle(p1, w, h)
    points = rs.PolylineVertices(rect)
    sp = points[0]
    fp = points[3]
    ep = points[1]
    if forward:
        sp = points[2]
    if three:
        sp = points[3]
        fp = points[0]
        ep = points[2]
    l1 = rs.AddLine(sp, ep)
    l2 = rs.AddLine(sp, fp)
    inter1 = rs.CurveCurveIntersection(c1, l1)[0][5]
    inter2 = rs.CurveCurveIntersection(c1, l2)[0][5]
    if forward or three:
        tmp = inter1
        inter1 = inter2
        inter2 = tmp
    c1 = rs.TrimCurve(c1, (inter1, inter2))
    fill = rs.AddFilletCurve(l1, l2, radius=0.125)
    inter1 = rs.CurveCurveIntersection(l1, fill)[0][5]
    inter2 = rs.CurveCurveIntersection(l2, fill)[0][5]
    l1 = rs.TrimCurve(l1, (inter1, 0))
    l2 = rs.TrimCurve(l2, (inter2, 0))
    rs.DeleteObjects(rect)
    fillet = rs.JoinCurves([l1, fill, l2])
    filletc = rs.CopyObject(fillet)
    return [rs.JoinCurves([fillet, c1], delete_input=True), filletc]

  def cutJoints(self, c, srf, forward):
    inter1 = rs.CurveCurveIntersection(c, srf[2])[0]
    inter2 = rs.CurveCurveIntersection(c, srf[3])[0]
    cc = rs.CopyObject(c)
    c = rs.TrimCurve(c, (inter1[5], inter2[5]))
    if rs.CurveLength(c) < 0.15:
        rs.DeleteObjects([c])
        c = rs.TrimCurve(cc, (inter2[5], inter1[5]))
    poly1 = rs.PolylineVertices(srf[2])
    poly2 = rs.PolylineVertices(srf[3])
    point1 = inter1[1]
    point4 = inter2[1]
    point2 = poly1[len(poly1) - 1]
    point3 = poly2[len(poly2) - 1]
    if forward:
        point2 = poly1[0]
        point3 = poly2[0]
    vec = rs.VectorCreate(point2, point1)
    l1 = rs.AddLine(point1, point2)
    arc = rs.AddArcPtTanPt(point2, vec, point3)
    l2 = rs.AddLine(point3, point4)
    return rs.JoinCurves([c, l1, arc, l2])

  def extrudeJoint(self, c, p, forward):
    point = p.Origin
    v = rs.VectorUnitize(p.ZAxis)
    v = rs.VectorScale(v, 0.125)
    if self.index % 2 == 0:
        if forward:
            v = rs.VectorReverse(v)
    else:
        if not forward:
            v = rs.VectorReverse(v)
    p2 = rs.PointAdd(point, v)
    l = rs.AddLine(point, p2)
    srf = rs.CapPlanarHoles(rs.ExtrudeCurve(c, l))
    return srf

  def buildConnector(self):
    [self.c1, self.fillet1] = self.buildDiscs(self.p1, self.c1, False, False)
    [self.c2, self.fillet2] = self.buildDiscs(self.p2, self.c2, True, False)
    [self.c3, self.fillet3] = self.buildDiscs(self.p3, self.c3, False, True)
    [self.c4, self.fillet4] = self.buildDiscs(self.p4, self.c4, True, False)
    self.blank1 = rs.CopyObject(self.c1)
    self.blank2 = rs.CopyObject(self.c2)
    self.blank3 = rs.CopyObject(self.c3)
    self.blank4 = rs.CopyObject(self.c4)
    if hasattr(self, 'srf1'):
        self.c1 = self.cutJoints(self.c1, self.srf1, False)
    if hasattr(self, 'srf3'):
        self.c3 = self.cutJoints(self.c3, self.srf3, False)
    if hasattr(self, 'srf2'):
        self.c2 = self.cutJoints(self.c2, self.srf2, True)
    if hasattr(self, 'srf4'):
        self.c4 = self.cutJoints(self.c4, self.srf4, True)
    self.jointsrf1 = self.extrudeJoint(self.c1, self.p1, False)
    self.jointsrf2 = self.extrudeJoint(self.c2, self.p2, True)
    self.jointsrf3 = self.extrudeJoint(self.c3, self.p3, False)
    self.jointsrf4 = self.extrudeJoint(self.c4, self.p4, True)
    self.base = self.buildBase()

  def nextMid(self):
    l = rs.AddLine(self.next1.cp, self.next2.cp)
    p = rs.CurveMidPoint(l)
    rs.DeleteObjects(l)
    return rs.PlaneClosestPoint(self.p2, p)

  def subtractionPiece(self, pl, crv, cpl):
    point = cpl.Origin
    vec = size_vector(pl.ZAxis, 0.5)
    point2 = rs.PointAdd(point, vec)
    crv = rs.ExtendCurveLength(crv, 0, 2, 1)
    s = rs.CurveStartPoint(crv)
    e = rs.CurveEndPoint(crv)
    l = rs.AddLine(s,e)
    crv = rs.JoinCurves([crv, l], delete_input=True)
    srf = rs.ExtrudeCurve(crv, rs.AddLine(point, point2))
    rs.CapPlanarHoles(srf)
    rs.DeleteObjects(crv)
    return srf

  def buildBase(self):
    vec = rs.VectorScale(rs.VectorUnitize(self.p2.ZAxis), 0.2)
    if self.index % 2 != 0 or self.index == 0:
        vec = rs.VectorReverse(vec)
    p = rs.PointAdd(self.cp, vec)

    yvec = rs.VectorCreate(self.cp, self.nextMid())
    xvec = rs.VectorCrossProduct(vec, yvec)
    pl = rs.PlaneFromFrame(p, xvec, yvec)
    w = self.distance_apart
    h = self.flat_length
    srf = rs.AddPlaneSurface(pl, w, h)
    rs.MoveObject(srf, rs.VectorReverse(size_vector(pl.XAxis, w/2)))
    rs.MoveObject(srf, rs.VectorReverse(size_vector(pl.YAxis, h/2)))
    np = rs.PointAdd(p, size_vector(pl.ZAxis, 0.40))
    l = rs.AddLine(p, np)
    base = rs.ExtrudeSurface(srf, l)
    rs.DeleteObjects(srf)
    base = rs.BooleanDifference(base, self.subtractionPiece(pl, self.fillet1, self.p1))
    base = rs.BooleanDifference(base, self.subtractionPiece(pl, self.fillet2, self.p2))
    base = rs.BooleanDifference(base, self.subtractionPiece(pl, self.fillet3, self.p3))
    base = rs.BooleanDifference(base, self.subtractionPiece(pl, self.fillet4, self.p4))
    return [base, pl]

  def link(self, next1, next2):
    self.next1 = next1
    self.next2 = next2
    if self.index == self.indexes - 1:
        return
    pa = rs.PlaneClosestPoint(self.p2, next1.point1)
    pb = rs.PlaneClosestPoint(next1.p1, self.point2)
    pc = rs.PlaneClosestPoint(self.p4, next2.point3)
    pd = rs.PlaneClosestPoint(next2.p3, self.point4)
    la = rs.AddLine(self.point2, pa)
    lb = rs.AddLine(next1.point1, pb)
    lc = rs.AddLine(self.point4, pc)
    ld = rs.AddLine(next2.point3, pd)
    intera = rs.CurveCurveIntersection(self.c2, la)[0][1]
    interb = rs.CurveCurveIntersection(next1.c1, lb)[0][1]
    interc = rs.CurveCurveIntersection(self.c4, lc)[0][1]
    interd = rs.CurveCurveIntersection(next2.c3, ld)[0][1]
    rs.DeleteObjects([la, lb, lc, ld])
    pla = rs.AddPolyline([self.point2, intera, interb, next1.point1])
    plb = rs.AddPolyline([self.point4, interc, interd, next2.point3])
    [srf1, srf2, crv1, crv2] = square_pipe(pla, self.p2, self.point2, self.index)
    [srf3, srf4, crv3, crv4] = square_pipe(plb, self.p4, self.point4, self.index)
    self.srf2 = [srf1, srf2, crv1, crv2] 
    self.srf4 = [srf3, srf4, crv3, crv4]
    next1.srf1 = self.srf2
    next2.srf3 = self.srf4
    next1.p1 = receiverSrf(next1.point1, crv1, crv2)
    next2.p3 = receiverSrf(next2.point3, crv3, crv4)
    rs.DeleteObjects([next1.c1, next2.c3])
    next1.c1 = rs.AddCircle(next1.p1, 0.25)
    next2.c3 = rs.AddCircle(next2.p3, 0.25)

  def layout_for_cut(self):
    worldXY = rs.WorldXYPlane()
    point1 = self.base[1].Origin
    point2 = rs.PointAdd(point1, size_vector(self.base[1].XAxis, 1))
    point3 = rs.PointAdd(point1, size_vector(self.base[1].YAxis, 1))
    base = rs.OrientObject(rs.CopyObject(self.base[0]), [point1, point2, point3], [rs.AddPoint(0,0,0), rs.AddPoint(1,0,0), rs.AddPoint(0,1,0)])
    rs.MoveObject(base, size_vector(worldXY.YAxis, (self.flat_length * 1.5) * (self.index + 1)))
    rs.MoveObject(base, size_vector(worldXY.XAxis, (self.distance_apart * 2.25) * ((self.count/POINTS_ON_CROSS_SECTION) + 1)))

class PathLattice:

  POINTS_ON_CROSS_SECTION = 20

  def __init__(self):
    self.joints = []
    self.midpoints = []
    self.partsHash = {}
    self.curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
    self.SAMPLES = rs.GetInteger("Set number of cross sections", 10)
    self.flat_length = rs.GetReal('Set flat length', 0.75)
    self.BEND_RADIUS = rs.GetReal('set x radius', 2)
    self.PERP_RADIUS = rs.GetReal('set y radius', 2.5)
    self.RADIUS_SCALAR = rs.GetReal('Set radius scale', 2.5)
    self.distance_apart = rs.GetReal('Set distance apart for flats', 0.65)
    self.create_cross_sections()
    self.brep = rs.AddLoftSrf(self.cross_sections)
    self.points_from_cross()
    if should_spiral[0] == False:
      self.points_for_lines()
    else:
      self.points_for_lines_sp()
    self.linkJoints()
    rs.DeleteObjects(self.brep)
    for i in range(0, len(self.cross_sections)):
        rs.DeleteObjects(self.cross_sections[i])


  def linkJoints(self):
    jlen = len(self.joints)
    for i in range(0, jlen):
        if self.SAMPLES % 2 == 0:
            if i == jlen - 1:
                self.joints[i].link(self.joints[(i - 1) % jlen], self.joints[(i - (self.SAMPLES - 1)) % jlen])
            elif self.joints[i].index % 2 == 0:
                self.joints[i].link(self.joints[(i + 1) % jlen], self.joints[(i - (self.SAMPLES - 1)) % jlen])
            else:
                self.joints[i].link(self.joints[(i + 1) % jlen], self.joints[(i + (self.SAMPLES + 1)) % jlen])
        else:
            if i == jlen - 1:
                self.joints[i].link(self.joints[(i - 1) % jlen], self.joints[(i - self.SAMPLES) % jlen])
            elif self.joints[i].index % 2 == 0:
                self.joints[i].link(self.joints[(i + 1) % jlen], self.joints[(i - (self.SAMPLES)) % jlen])
            else:
                self.joints[i].link(self.joints[(i + 1) % jlen], self.joints[(i + self.SAMPLES + 2) % jlen])
    for i in range(0, jlen):
        self.joints[i].buildConnector()
        self.joints[i].layout_for_cut()


  def add_text(self):
    for i in range(0, len(self.point_lists)):
      rs.AddText(str(i), self.cross_section_planes[i].Origin, 5)
      for j in range(0, len(self.point_lists[i])):
        rs.AddText(str(j), self.point_lists[i][j], 2)

  def points_from_ellipse(self, index):
    ellipse = self.cross_sections[index]
    even = index % 2 == 0

    ellipse_domain = rs.CurveDomain(ellipse)
    ellipse_step = (ellipse_domain[1] - ellipse_domain[0])/POINTS_ON_CROSS_SECTION
    points = []

    j = 0
    for i in rs.frange(ellipse_domain[0], ellipse_domain[1] - ellipse_step, ellipse_step):
      if even:
        if j % 2 == 0:
          points.append(rs.EvaluateCurve(ellipse, i))
      else:
        if (j + 1) % 2 == 0:
          points.append(rs.EvaluateCurve(ellipse, i))
      j += 1
    return points

  def points_from_cross(self):
    self.point_lists = []
    for i in range(0, len(self.cross_sections)):
      points = self.points_from_ellipse(i)
      self.point_lists.append(points)


  def points_for_lines(self):
    self.line_points = []
    count = 0
    for j in range(0, len(self.point_lists[0])):
      points_1 = []
      points_2 = []
      for i in range(0, len(self.point_lists)):
        modulo = len(self.point_lists[i])
        if(i % 2 == 0):
          point_index = (j) % modulo
          offset_points_1 = self.move_point_up(self.point_lists[i][point_index], i, point_index)
          offset_points_2 = self.move_point_down(self.point_lists[i][point_index], i, point_index)
          points_1.append(offset_points_1[0])
          points_2.append(offset_points_2[0])
          if len(offset_points_1) == 2: points_1.append(offset_points_1[1])
          if len(offset_points_2) == 2: points_2.append(offset_points_2[1])
          if len(offset_points_1) == 2 and len(offset_points_2) == 2:
            self.add_joint_piece(offset_points_1[0], offset_points_1[1], offset_points_2[0], offset_points_2[1], self.point_lists[i][point_index], count, i, len(self.point_lists))
        else:
          point_1_index = (j) % modulo
          point_2_index = ((j) - 1) % modulo
          offset_points_1 = self.move_point_down(self.point_lists[i][point_1_index], i, point_1_index)
          offset_points_1u = self.move_point_up(self.point_lists[i][point_1_index], i, point_1_index)
          offset_points_2 = self.move_point_up(self.point_lists[i][point_2_index], i, point_2_index)
          points_1.append(offset_points_1[0])
          points_1.append(offset_points_1[1])
          points_2.append(offset_points_2[0])
          points_2.append(offset_points_2[1])
          self.add_joint_piece(offset_points_1[0], offset_points_1[1], offset_points_1u[0], offset_points_1u[1], self.point_lists[i][point_index], count, i, len(self.point_lists))
        count = count + 1
      self.line_points.append(points_1)
      self.line_points.append(points_2)

  def add_joint_piece(self, point1, point2, point3, point4, cp, count, index, indexes):
    rs.AddText(str(count), cp)
    self.joints.append(JointPiece(
        point1,
        point2,
        point3,
        point4,
        cp,
        index,
        indexes,
        self.curve_object,
        self.flat_length,
        self.distance_apart,
        count))

  def points_for_lines_sp(self):
    self.line_points = []
    count = 0
    for j in range(0, len(self.point_lists[0])):
      points_1 = []
      points_2 = []
      for i in range(0, len(self.point_lists)):
        modulo = len(self.point_lists[i])
        if(i % 2 == 0):
          point_index = (j+i) % modulo
          offset_points_1 = self.move_point_up_sp(self.point_lists[i][point_index], i, point_index)
          offset_points_2 = self.move_point_down_sp(self.point_lists[i][point_index], i, point_index)
          points_1.append(offset_points_1[0])
          points_2.append(offset_points_2[0])
          if len(offset_points_1) == 2: points_1.append(offset_points_1[1])
          if len(offset_points_2) == 2: points_2.append(offset_points_2[1])
          if len(offset_points_1) == 2 and len(offset_points_2) == 2:
            self.add_joint_piece(offset_points_1[0], offset_points_1[1], offset_points_2[0], offset_points_2[1], self.point_lists[i][point_index], count, i, len(self.point_lists))
        else:
          point_1_index = (j+i) % modulo
          point_2_index = ((j+i) - 1) % modulo
          offset_points_1 = self.move_point_down_sp(self.point_lists[i][point_1_index], i, point_1_index)
          offset_points_1u = self.move_point_up_sp(self.point_lists[i][point_1_index], i, point_1_index)
          offset_points_2 = self.move_point_up_sp(self.point_lists[i][point_2_index], i, point_2_index)
          points_1.append(offset_points_1[0])
          points_1.append(offset_points_1[1])
          points_2.append(offset_points_2[0])
          points_2.append(offset_points_2[1])
          self.add_joint_piece(offset_points_1[0], offset_points_1[1], offset_points_1u[0], offset_points_1u[1], self.point_lists[i][point_1_index], count, i, len(self.point_lists))
        count = count + 1
      self.line_points.append(points_1)
      self.line_points.append(points_2)

  def offset_vector(self, point, cross_section_index, point_index):
      modulo = len(self.point_lists[cross_section_index])
      closest_point = rs.CurveClosestPoint(self.cross_sections[cross_section_index], point)
      crv = rs.CurveCurvature(self.cross_sections[cross_section_index], closest_point)
      crvTangent = crv[1]
      crvPerp = rs.VectorUnitize(crv[4])
      unit_vector = rs.VectorUnitize(crvTangent)
      return [rs.VectorScale(unit_vector, self.distance_apart/2), rs.VectorReverse(rs.VectorCrossProduct(crvTangent, crvPerp))]

  def move_point_up(self, point, cross_section_index, point_index):
    offset_vectors = self.offset_vector(point, cross_section_index, point_index)
    normal = offset_vectors[0]
    scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.flat_length/2)
    new_point = rs.PointAdd(point, normal)
    self.midpoints.append(new_point)
    return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]

  def move_point_down(self, point, cross_section_index, point_index):
    offset_vectors = self.offset_vector(point, cross_section_index, point_index)
    normal = rs.VectorReverse(offset_vectors[0])
    scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.flat_length/2)
    new_point = rs.PointAdd(point, normal)
    self.midpoints.append(new_point)
    return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]

  def offset_vector_sp(self, point, cross_section_index, point_index):
      modulo = len(self.point_lists[cross_section_index - 1])
      prev_point_1 = self.point_lists[cross_section_index - 1][(point_index - 2) % modulo] if cross_section_index % 2 == 0 else self.point_lists[cross_section_index - 1][(point_index - 1) % modulo]
      prev_point_2 = self.point_lists[cross_section_index - 1][(point_index - 1) % modulo] if cross_section_index % 2 == 0 else self.point_lists[cross_section_index - 1][point_index]
      in_between_vector = rs.VectorAdd(rs.VectorCreate(prev_point_1, point), rs.VectorCreate(prev_point_2, point))
      normal_vector = rs.SurfaceNormal(self.brep, rs.SurfaceClosestPoint(self.brep, point))
      plane = rs.PlaneFromFrame(point, in_between_vector, normal_vector)
      vector = rs.SurfaceNormal(rs.AddPlaneSurface(plane, 1, 1), [0,0])
      unit_vector = rs.VectorUnitize(vector)
      return [rs.VectorScale(unit_vector, self.distance_apart/2), in_between_vector]

  def move_point_up_sp(self, point, cross_section_index, point_index):
      offset_vectors = self.offset_vector_sp(point, cross_section_index, point_index)
      normal = offset_vectors[0]
      scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.flat_length/2)
      new_point = rs.PointAdd(point, normal)
      return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]

  def move_point_down_sp(self, point, cross_section_index, point_index):
      offset_vectors = self.offset_vector_sp(point, cross_section_index, point_index)
      normal = rs.VectorReverse(offset_vectors[0])
      scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.flat_length/2)
      new_point = rs.PointAdd(point, normal)
      return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]



  def get_curve_from_segments(self, lines):
    curves = rs.JoinCurves(lines);
    index = 0
    length = 0
    for i in range(0, len(curves)):
      new_length = rs.CurveLength(curves[i])
      if(new_length > length):
        index = i
        length = new_length
    return curves[index]


  def reverse_if_needed(self, current, previous):
    dot_product = rs.VectorDotProduct(current, previous)
    if (dot_product < 0):
      return rs.VectorReverse(current)
    else:
      return current

  def cross_section_plane_no_curvature(self, t, prev_normal = None, prev_perp = None):
    crvPoint = rs.EvaluateCurve(self.curve_object, t)
    crvTangent = rs.CurveTangent(self.curve_object, t)
    crvPerp = (0,0,1)
    crvNormal = rs.VectorCrossProduct(crvTangent, crvPerp)
    if prev_normal:
      crvNormal = self.reverse_if_needed(crvNormal, prev_normal)
    if prev_perp:
      crvPerp = self.reverse_if_needed(crvPerp, prev_perp)
    return rs.PlaneFromFrame(crvPoint, crvPerp, crvNormal)

  def cross_section_plane_curvature(self, curvature, prev_normal, prev_perp):
    crvPoint = curvature[0]
    crvTangent = curvature[1]
    crvPerp = rs.VectorUnitize(curvature[4])
    crvNormal = rs.VectorCrossProduct(crvTangent, crvPerp)
    if prev_normal:
      crvNormal = self.reverse_if_needed(crvNormal, prev_normal)
    if prev_perp:
      crvPerp = self.reverse_if_needed(crvPerp, prev_perp)
    return rs.PlaneFromFrame(crvPoint, crvPerp, crvNormal)

  def ellipse_radii(self, scalar):
    return [self.BEND_RADIUS * scalar, self.PERP_RADIUS * scalar]

  def delete_cross_sections(self):
    rs.DeleteObjects(self.cross_sections)

  def calc_step(self, t_step, pi_step):
    squared = math.sin(pi_step) * math.sin(pi_step)
    return t_step * ((squared * 1) + 0.5)

  def create_scalar(self, step):
    squared = math.sin(step) * math.sin(step)
    return self.RADIUS_SCALAR * (squared + 1)

  def create_cross_sections(self):
    crvdomain = rs.CurveDomain(self.curve_object)
    self.cross_sections = []
    self.cross_section_planes = []

    t_step = (crvdomain[1]-crvdomain[0])/self.SAMPLES
    pi_step_size = math.pi/self.SAMPLES
    pi_step = 0

    prev_normal = None
    prev_perp = None
    t = crvdomain[0]
    while t <= crvdomain[1]:
      crvcurvature = rs.CurveCurvature(self.curve_object, t)
      crosssectionplane = None

      if not crvcurvature:
        crosssectionplane = self.cross_section_plane_no_curvature(t, prev_normal, prev_perp)
      else:
        crosssectionplane = self.cross_section_plane_curvature(crvcurvature, prev_normal, prev_perp)

      if crosssectionplane:
        prev_perp = crosssectionplane.XAxis
        prev_normal = crosssectionplane.YAxis
        pi_scalar = self.create_scalar(pi_step)
        radii = self.ellipse_radii(pi_scalar)
        csec = rs.AddEllipse(crosssectionplane, radii[0], radii[1])
        self.cross_sections.append(csec)
        self.cross_section_planes.append(crosssectionplane)
      t +=  t_step#self.calc_step(t_step, pi_step)
      pi_step += pi_step_size

rs.EnableRedraw(False)
PathLattice()
rs.EnableRedraw(True)
