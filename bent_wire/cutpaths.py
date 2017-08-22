
import rhinoscriptsyntax as rs
import math
import re
import json
import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

POINTS_ON_CROSS_SECTION = rs.GetReal("Set nodes per cross section", 10) * 2
should_spiral = rs.GetBoolean('Spiral Pattern?',('spiral', 'no', 'yes'), (True))
DISC_RADIUS = 0.125
MATERIAL_THICKNESS = 0.125

def size_vector(vector, number):
    return rs.VectorScale(rs.VectorUnitize(vector), number)

def perp_to_two(vector1, vector2):
    return rs.VectorCrossProduct(vector1, vector2)

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
    self.c1 = rs.AddCircle(self.p1, DISC_RADIUS)
    self.c2 = rs.AddCircle(self.p2, DISC_RADIUS)
    self.c3 = rs.AddCircle(self.p3, DISC_RADIUS)
    self.c4 = rs.AddCircle(self.p4, DISC_RADIUS)


  def createRec(self, p1, p2):
    perpVec = size_vector(perp_to_two(p1.ZAxis, rs.VectorCreate(p2.Origin, p1.Origin)), DISC_RADIUS)
    perpVec2 = rs.VectorReverse(perpVec)
    corner1 = rs.VectorAdd(p1.Origin, perpVec)
    corner2 = rs.VectorAdd(p1.Origin, perpVec2)
    corner3 = rs.VectorAdd(p2.Origin, perpVec2)
    corner4 = rs.VectorAdd(p2.Origin, perpVec)
    return [corner1, corner2, corner3, corner4];

  def createArcs(self, rec1, rec2):
    tan = rs.CurveTangent(self.c1, rs.CurveClosestPoint(self.c1, rec1[1]))
    arc1 = rs.AddArcPtTanPt(rec1[1], tan, rec2[1])
    tan = rs.CurveTangent(self.c1, rs.CurveClosestPoint(self.c1, rec1[0]))
    arc2 = rs.AddArcPtTanPt(rec1[0], rs.VectorReverse(tan), rec2[2])
    tan = rs.CurveTangent(self.c4, rs.CurveClosestPoint(self.c4, rec1[2]))
    arc3 = rs.AddArcPtTanPt(rec1[2], tan, rec2[0])
    tan = rs.CurveTangent(self.c4, rs.CurveClosestPoint(self.c4, rec1[3]))
    arc4 = rs.AddArcPtTanPt(rec1[3], rs.VectorReverse(tan), rec2[3])
    return [arc1, arc2, arc3, arc4]

  def cutSlots(self, circ, inter, p, rev):
    perpVec = size_vector(perp_to_two(p.ZAxis, rs.VectorCreate(p.Origin, inter)), MATERIAL_THICKNESS/2)
    perpVec2 = rs.VectorReverse(perpVec)
    vec = size_vector(rs.VectorCreate(p.Origin, inter), DISC_RADIUS)
    if rev:
        inter = rs.VectorAdd(p.Origin, vec)
        vec = rs.VectorReverse(vec)
    p1 = rs.VectorAdd(inter, perpVec)
    p2 = rs.VectorAdd(p1, vec)
    p3 = rs.VectorAdd(inter, perpVec2)
    p4 = rs.VectorAdd(p3, vec)
    arc = rs.AddArcPtTanPt(p2, rs.VectorCreate(p2,p1), p4)
    l1 = rs.AddLine(p1, p2)
    l2 = rs.AddLine(p3, p4)
    inter1 = rs.CurveCurveIntersection(l1, circ)[0]
    inter2 = rs.CurveCurveIntersection(l2, circ)[0]
    if rev:
        circ = rs.TrimCurve(circ, (inter1[7], inter2[7]))
    else:
        circ = rs.TrimCurve(circ, (inter2[7], inter1[7]))
    l1 = rs.TrimCurve(l1, (inter1[5], 0))
    l2 = rs.TrimCurve(l2, (inter2[5], 0))
    return rs.JoinCurves([circ, l1, l2, arc], delete_input=True)

  def connectToNext(self, p, pv, cv, np, npv, ncv):
    vec1 = size_vector(rs.VectorCreate(np.Origin, p.Origin), 0.4)
    perpVec1 = size_vector(perp_to_two(vec1, pv.ZAxis), DISC_RADIUS)
    sp1 = rs.VectorAdd(pv.Origin, perpVec1);
    sp2 = rs.VectorAdd(pv.Origin, rs.VectorReverse(perpVec1));
    sp3 = rs.VectorAdd(sp1, vec1)
    sp4 = rs.VectorAdd(sp2, vec1)
    sp5 = rs.VectorAdd(sp4, size_vector(perpVec1, DISC_RADIUS - (MATERIAL_THICKNESS/2)))
    sp6 = rs.VectorAdd(sp3, size_vector(rs.VectorReverse(perpVec1), DISC_RADIUS - (MATERIAL_THICKNESS/2)))
    sp7 = rs.VectorAdd(sp5, size_vector(rs.VectorReverse(vec1), 0.2))
    sp8 = rs.VectorAdd(sp6, size_vector(rs.VectorReverse(vec1), 0.2))
    basePoint = rs.VectorAdd(sp7, size_vector(perpVec1, MATERIAL_THICKNESS/2))
    basePoint = rs.AddPoint(basePoint)
    dom1 = rs.CurveClosestPoint(cv, sp1)
    dom2 = rs.CurveClosestPoint(cv, sp2)
    conn = rs.JoinCurves([
        rs.TrimCurve(cv, (dom2, dom1)),
        rs.AddArcPtTanPt(sp7, rs.VectorReverse(vec1), sp8),
        rs.AddPolyline([sp1, sp3, sp6, sp8]),
        rs.AddPolyline([sp7, sp5, sp4, sp2])
    ], delete_input=True)

    vec1 = size_vector(rs.VectorCreate(p.Origin, np.Origin), 0.4)
    perpVec1 = size_vector(perp_to_two(vec1, npv.ZAxis), DISC_RADIUS)
    nsp1 = rs.VectorAdd(npv.Origin, perpVec1);
    nsp2 = rs.VectorAdd(npv.Origin, rs.VectorReverse(perpVec1));
    nsp3 = rs.VectorAdd(nsp1, vec1)
    nsp4 = rs.VectorAdd(nsp2, vec1)
    nsp5 = rs.VectorAdd(nsp4, size_vector(perpVec1, DISC_RADIUS - (MATERIAL_THICKNESS/2)))
    nsp6 = rs.VectorAdd(nsp3, size_vector(rs.VectorReverse(perpVec1), DISC_RADIUS - (MATERIAL_THICKNESS/2)))
    nsp7 = rs.VectorAdd(nsp5, size_vector(rs.VectorReverse(vec1), 0.2))
    nsp8 = rs.VectorAdd(nsp6, size_vector(rs.VectorReverse(vec1), 0.2))
    nbasePoint =  rs.VectorAdd(nsp7, size_vector(perpVec1, MATERIAL_THICKNESS/2))
    nbasePoint = rs.AddPoint(nbasePoint)
    dom1 = rs.CurveClosestPoint(ncv, nsp1)
    dom2 = rs.CurveClosestPoint(ncv, nsp2)
    nconn = rs.JoinCurves([
        rs.TrimCurve(ncv, (dom2, dom1)),
        rs.AddArcPtTanPt(nsp7, rs.VectorReverse(vec1), nsp8),
        rs.AddPolyline([nsp1, nsp3, nsp6, nsp8]),
        rs.AddPolyline([nsp7, nsp5, nsp4, nsp2])
    ], delete_input=True)
    return [conn, nconn, basePoint, nbasePoint]

  def trimCircle(self, c, p1, p2):
    dom1 = rs.CurveClosestPoint(c, p1)
    dom2 = rs.CurveClosestPoint(c, p2)
    return rs.TrimCurve(c, (dom2, dom1))

  def extrudeSrf(self, p, c):
    sp = p.Origin
    ep = rs.VectorAdd(sp, size_vector(p.ZAxis, MATERIAL_THICKNESS/2))
    srf1 = rs.ExtrudeCurveStraight(c, sp, ep)
    ep = rs.VectorAdd(sp, size_vector(rs.VectorReverse(p.ZAxis), MATERIAL_THICKNESS/2))
    srf2 = rs.ExtrudeCurveStraight(c, sp, ep)
    return rs.CapPlanarHoles(rs.JoinSurfaces([srf1, srf2], delete_input=True))

  def addPipe(self, p1, p2):
    l = rs.AddLine(p1, p2)
    rs.AddPipe(l, 0, MATERIAL_THICKNESS/2)
    return l

  def buildSolids(self):
    self.baseSolid = self.extrudeSrf(self.p1, self.base)
    if hasattr(self, 'pv1'):
        self.cv1Sold = self.extrudeSrf(self.pv1, self.cv1)
    if hasattr(self, 'pv2'):
        self.cv2Sold = self.extrudeSrf(self.pv2, self.cv2)
    if hasattr(self, 'pv3'):
        self.cv3Sold = self.extrudeSrf(self.pv3, self.cv3)
    if hasattr(self, 'pv4'):
        self.cv4Sold = self.extrudeSrf(self.pv4, self.cv4)

  def createArcFirst(self, rec1, rec2):
    tan = rs.CurveTangent(self.c1, rs.CurveClosestPoint(self.c1, rec1[1]))
    arc1 = rs.AddArcPtTanPt(rec1[1], tan, rec2[0])
    tan = rs.CurveTangent(self.c1, rs.CurveClosestPoint(self.c1, rec1[0]))
    arc2 = rs.AddArcPtTanPt(rec1[0], rs.VectorReverse(tan), rec2[3])
    tan = rs.CurveTangent(self.c2, rs.CurveClosestPoint(self.c2, rec1[2]))
    arc3 = rs.AddArcPtTanPt(rec1[2], tan, rec2[1])
    tan = rs.CurveTangent(self.c2, rs.CurveClosestPoint(self.c2, rec1[3]))
    arc4 = rs.AddArcPtTanPt(rec1[3], rs.VectorReverse(tan), rec2[2])
    return [arc1, arc2, arc3, arc4]

  def cutBaseSlots(self, base, inter, p):
    perpVec = size_vector(perp_to_two(p.ZAxis, rs.VectorCreate(p.Origin, inter)), MATERIAL_THICKNESS/2)
    perpVec2 = rs.VectorReverse(perpVec)
    vec = size_vector(rs.VectorCreate(p.Origin, inter), DISC_RADIUS)
    p1 = rs.VectorAdd(inter, perpVec)
    p2 = rs.VectorAdd(p1, vec)
    p3 = rs.VectorAdd(inter, perpVec2)
    p4 = rs.VectorAdd(p3, vec)
    arc = rs.AddArcPtTanPt(p2, rs.VectorCreate(p2,p1), p4)
    l1 = rs.AddLine(p1, p2)
    l2 = rs.AddLine(p3, p4)
    inter1 = rs.CurveCurveIntersection(l1, base)[0]
    inter2 = rs.CurveCurveIntersection(l2, base)[0]
    baseint1 = inter1[7] if inter1[7] < inter2[7] else inter2[7]
    baseint2 = inter2[7] if inter1[7] < inter2[7] else inter1[7]
    base = rs.TrimCurve(base, (baseint2, baseint1))
    l1 = rs.TrimCurve(l1, (inter1[5], 0))
    l2 = rs.TrimCurve(l2, (inter2[5], 0))
    return rs.JoinCurves([base, l1, l2, arc], delete_input=True)


  def buildBase(self):
    rec1 = self.createRec(self.p1, self.p4)
    rec2 = self.createRec(self.p2, self.p3)
    if self.index == 0:
        rec2 = self.createRec(self.p4, self.p3)
        rec1 = self.createRec(self.p1, self.p2)
    arcs = self.createArcs(rec1, rec2) if self.index != 0 else self.createArcFirst(rec1,rec2)
    self.c1 = self.trimCircle(self.c1, rec1[1], rec1[0])
    self.c4 = self.trimCircle(self.c4, rec1[2], rec1[3]) if self.index != 0 else self.trimCircle(self.c4, rec2[1], rec2[0])
    self.c3 = self.trimCircle(self.c3, rec2[2], rec2[3])
    self.c2 = self.trimCircle(self.c2, rec2[1], rec2[0]) if self.index != 0 else self.trimCircle(self.c2, rec1[2], rec1[3])
    self.base = rs.JoinCurves([self.c1, self.c2, self.c3, self.c4] + arcs, delete_input=True)
    if hasattr(self, 'inter1'):
        self.base = self.cutBaseSlots(self.base, self.inter1, self.p1)
        self.cv1 = self.cutSlots(self.cv1, self.inter1, self.pv1, True)
    if hasattr(self, 'inter2'):
        self.base = self.cutBaseSlots(self.base, self.inter2, self.p2)
        self.cv2 = self.cutSlots(self.cv2, self.inter2, self.pv2, True)
    if hasattr(self, 'inter3'):
        self.base = self.cutBaseSlots(self.base, self.inter3, self.p3)
        self.cv3 = self.cutSlots(self.cv3, self.inter3, self.pv3, True)
    if hasattr(self, 'inter4'):
        self.base = self.cutBaseSlots(self.base, self.inter4, self.p4)
        self.cv4 = self.cutSlots(self.cv4, self.inter4, self.pv4, True)
    self.buildSolids()

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
    self.inter2 = intera
    next1.inter1 = interb
    self.inter4 = interc
    next2.inter3 = interd
    pla = rs.PlaneFromPoints(self.p2.Origin, rs.VectorAdd(self.p2.Origin, self.p2.ZAxis), intera)
    plb = rs.PlaneFromPoints(next1.p1.Origin, rs.VectorAdd(next1.p1.Origin, next1.p1.ZAxis), interb)
    plc = rs.PlaneFromPoints(self.p4.Origin, rs.VectorAdd(self.p4.Origin, self.p4.ZAxis), interc)
    pld = rs.PlaneFromPoints(next2.p3.Origin, rs.VectorAdd(next2.p3.Origin, next2.p3.ZAxis), interd)
    self.pv2 = pla
    next1.pv1 = plb
    self.pv4 = plc
    next2.pv3 = pld
    self.cv2 = rs.AddCircle(pla, DISC_RADIUS)
    next1.cv1 = rs.AddCircle(plb, DISC_RADIUS)
    self.cv4 = rs.AddCircle(plc, DISC_RADIUS)
    next2.cv3 = rs.AddCircle(pld, DISC_RADIUS)
    rs.DeleteObjects([la, lb, lc, ld])
    [self.cv2, self.next1.cv1, self.basePoint2, self.next1.basePoint1] = self.connectToNext(self.p2, self.pv2, self.cv2, self.next1.p1, self.next1.pv1, self.next1.cv1)
    [self.cv4, self.next2.cv3, self.basePoint4, self.next2.basePoint3] = self.connectToNext(self.p4, self.pv4, self.cv4, self.next2.p3, self.next2.pv3, self.next2.cv3)
    self.l2 = self.addPipe(self.basePoint2, self.next1.basePoint1)
    self.l4 = self.addPipe(self.basePoint4, self.next2.basePoint3)

  def layout_for_cut(self):
    pass
    # wintera ldXY = rs.WorldXYPlane()
    # pointinterd= self.base[1].Origin
    # point2 =intercs.PointAdd(point1, size_vector(self.base[1].XAxis, 1))
    # point3 = rs.PointAdd(point1, size_vector(self.base[1].YAxis, 1))
    # base = rs.OrientObject(rs.CopyObject(self.base[0]), [point1, point2, point3], [rs.AddPoint(0,0,0), rs.AddPoint(1,0,0), rs.AddPoint(0,1,0)])
    # rs.MoveObject(base, size_vector(worldXY.YAxis, (self.flat_length * 1.5) * (self.index + 1)))
    # rs.MoveObject(base, size_vector(worldXY.XAxis, (self.distance_apart * 2.25) * ((self.count/POINTS_ON_CROSS_SECTION) + 1)))

class PathLattice:

  POINTS_ON_CROSS_SECTION = 20

  def __init__(self):
    self.joints = []
    self.midpoints = []
    self.partsHash = {}
    self.curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
    self.SAMPLES = rs.GetInteger("Set number of cross sections", 7)
    self.flat_length = rs.GetReal('Set flat length', 0.50)
    self.BEND_RADIUS = rs.GetReal('set x radius', 2)
    self.PERP_RADIUS = rs.GetReal('set y radius', 2.5)
    self.RADIUS_SCALAR = rs.GetReal('Set radius scale', 2.5)
    self.distance_apart = rs.GetReal('Set distance apart for flats', 0.35)
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
        self.joints[i].buildBase()
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
