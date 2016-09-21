import rhinoscriptsyntax as rs
import math


class PathLattice:
  SAMPLES = 20

  BEND_RADIUS = 2

  PERP_RADIUS = 2

  POINTS_ON_CROSS_SECTION = 20

  FLAT_LENGTH = 0.5

  RADIUS_SCALAR = 2

  def __init__(self):
    self.curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
    self.create_cross_sections()
    self.brep = rs.AddLoftSrf(self.cross_sections)
    self.points_from_cross()
    # self.add_text()
    self.points_for_lines()
    self.create_lines()
    self.create_jigs()
    self.delete_cross_sections()
    rs.DeleteObjects(self.brep)

  def create_jigs(self):
    for i in range(0, len(self.line_lists), 1):
      jigs = self.create_jig(self.line_lists[i])
      self.create_jig_connectors(jigs)
      self.join_jigs(jigs)

  def create_jig(self, list):
    jigs = []
    for i in range(0, len(list), 2):
      domain = rs.CurveDomain(list[i])
      start_point = rs.EvaluateCurve(list[i], domain[0])
      end_point = rs.EvaluateCurve(list[i], domain[1])
      start_plane = rs.PlaneFromNormal(start_point, rs.VectorUnitize(end_point - start_point))
      end_plane = rs.PlaneFromNormal(end_point, rs.VectorUnitize(start_point - end_point))
      start_curve_point = self.closest_intersection(rs.PlaneCurveIntersection(start_plane, self.curve_object), start_point)
      end_curve_point = self.closest_intersection(rs.PlaneCurveIntersection(end_plane, self.curve_object), end_point)
      start_vector = rs.VectorUnitize(rs.VectorCreate(start_point, start_curve_point))
      end_vector = rs.VectorUnitize(rs.VectorCreate(end_point, end_curve_point))
      start_vector_scale = rs.VectorScale(start_vector, -5)
      end_vector_scale = rs.VectorScale(end_vector, -5)
      start_square = self.create_square(rs.PointAdd(start_point, start_vector_scale), rs.PointAdd(end_point, end_vector_scale), start_vector)
      end_square = self.create_square(rs.PointAdd(end_point, end_vector_scale), rs.PointAdd(start_point, start_vector_scale), end_vector)
      jigs.append(self.create_jig_section(start_square, end_square))
    return jigs

  def create_jig_section(self, start_square, end_square):
    poly_line_1 = rs.AddPolyline([start_square[1][0], end_square[1][1], end_square[1][0], start_square[1][1], start_square[1][0]])
    poly_line_2 = rs.AddPolyline([start_square[1][0], end_square[1][1], end_square[1][2], start_square[1][3], start_square[1][0]])
    poly_line_3 = rs.AddPolyline([start_square[1][2], end_square[1][3], end_square[1][2], start_square[1][3], start_square[1][2]])
    poly_line_4 = rs.AddPolyline([start_square[1][1], end_square[1][0], end_square[1][3], start_square[1][2], start_square[1][1]])
    poly_line_5 = rs.AddPolyline([start_square[0][1], start_square[1][1], start_square[1][0], start_square[0][0], start_square[0][1]])
    poly_line_6 = rs.AddPolyline([start_square[0][1], start_square[1][1], start_square[1][2], start_square[0][2], start_square[0][1]])
    poly_line_7 = rs.AddPolyline([start_square[0][2], start_square[1][2], start_square[1][3], start_square[0][3], start_square[0][2]])
    poly_line_8 = rs.AddPolyline([start_square[0][3], start_square[1][3], start_square[1][0], start_square[0][0], start_square[0][3]])
    poly_line_9 = rs.AddPolyline([end_square[0][1], end_square[1][1], end_square[1][0], end_square[0][0], end_square[0][1]])
    poly_line_10 = rs.AddPolyline([end_square[0][1], end_square[1][1], end_square[1][2], end_square[0][2], end_square[0][1]])
    poly_line_11 = rs.AddPolyline([end_square[0][2], end_square[1][2], end_square[1][3], end_square[0][3], end_square[0][2]])
    poly_line_12 = rs.AddPolyline([end_square[0][3], end_square[1][3], end_square[1][0], end_square[0][0], end_square[0][3]])
    srf = rs.JoinSurfaces([
      rs.AddPlanarSrf(poly_line_1),
      rs.AddPlanarSrf(poly_line_2),
      rs.AddPlanarSrf(poly_line_3),
      rs.AddPlanarSrf(poly_line_4),
      rs.AddPlanarSrf(poly_line_5),
      rs.AddPlanarSrf(poly_line_6),
      rs.AddPlanarSrf(poly_line_7),
      rs.AddPlanarSrf(poly_line_8),
      rs.AddPlanarSrf(poly_line_9),
      rs.AddPlanarSrf(poly_line_10),
      rs.AddPlanarSrf(poly_line_11),
      rs.AddPlanarSrf(poly_line_12)
    ], True)
    return JigPiece(srf, start_square[0], end_square[0], start_square[2])

  def create_square(self, start_point, end_point, start_vector):
    across = rs.VectorUnitize(end_point - start_point)
    up = rs.VectorScale(start_vector, 0.5)
    over_unit = rs.VectorUnitize(rs.VectorCrossProduct(up, across))
    over = rs.VectorScale((over_unit), 0.5)
    points_inner = []
    points_inner.append(rs.PointAdd(start_point, rs.VectorAdd(up, over)))
    points_inner.append(rs.PointAdd(points_inner[0], rs.VectorReverse(over_unit)))
    points_inner.append(rs.PointAdd(points_inner[1], rs.VectorReverse(start_vector)))
    points_inner.append(rs.PointAdd(points_inner[2], over_unit))
    points_outer = []
    points_outer.append(rs.PointAdd(start_point, rs.VectorAdd(start_vector, over_unit)))
    points_outer.append(rs.PointAdd(points_outer[0], rs.VectorScale(rs.VectorReverse(over_unit), 2)))
    points_outer.append(rs.PointAdd(points_outer[1], rs.VectorScale(rs.VectorReverse(start_vector), 2)))
    points_outer.append(rs.PointAdd(points_outer[2], rs.VectorScale(over_unit, 2)))
    return [points_outer, points_inner, across]

  def create_jig_connectors(self, jigs):
    for i in range(0, len(jigs) -1, 1):
      poly_line_1 = rs.AddPolyline([jigs[i].end_corners[0], jigs[i+1].start_corners[1], jigs[i+1].start_corners[0], jigs[i].end_corners[0]])
      poly_line_2 = rs.AddPolyline([jigs[i].end_corners[1], jigs[i+1].start_corners[0], jigs[i].end_corners[0], jigs[i].end_corners[1]])
      poly_line_3 = rs.AddPolyline([jigs[i].end_corners[1], jigs[i+1].start_corners[0], jigs[i+1].start_corners[3], jigs[i].end_corners[1]])
      poly_line_4 = rs.AddPolyline([jigs[i].end_corners[2], jigs[i+1].start_corners[3], jigs[i].end_corners[1], jigs[i].end_corners[2]])
      poly_line_5 = rs.AddPolyline([jigs[i].end_corners[2], jigs[i+1].start_corners[3], jigs[i+1].start_corners[2], jigs[i].end_corners[2]])
      poly_line_6 = rs.AddPolyline([jigs[i].end_corners[3], jigs[i+1].start_corners[2], jigs[i].end_corners[2], jigs[i].end_corners[3]])
      poly_line_7 = rs.AddPolyline([jigs[i].end_corners[3], jigs[i+1].start_corners[2], jigs[i].end_corners[0], jigs[i].end_corners[3]])
      poly_line_8 = rs.AddPolyline([jigs[i].end_corners[0], jigs[i+1].start_corners[1], jigs[i+1].start_corners[2], jigs[i].end_corners[0]])
      srf = rs.JoinSurfaces([
        rs.AddPlanarSrf(poly_line_1),
        rs.AddPlanarSrf(poly_line_2),
        rs.AddPlanarSrf(poly_line_3),
        rs.AddPlanarSrf(poly_line_4),
        rs.AddPlanarSrf(poly_line_5),
        rs.AddPlanarSrf(poly_line_6),
        rs.AddPlanarSrf(poly_line_7),
        rs.AddPlanarSrf(poly_line_8),
      ], True)
      jigs[i].addConnector(srf)
      
  def create_end_caps(self, corners, vector):
    srf = rs.AddPolyline([
      corners[0],
      corners[1],
      corners[2],
      corners[3],
      corners[0]
    ])
    curve = rs.AddCurve([corners[0], rs.PointAdd(corners[0], rs.VectorScale(vector, 3))])
    return rs.AddSweep1(curve, [srf])

  def join_jigs(self, jigs):
    start_end = self.create_end_caps(jigs[0].start_corners, rs.VectorReverse(jigs[0].across))
    end_end = self.create_end_caps(jigs[len(jigs) - 1].end_corners, jigs[len(jigs) - 1].across)
    surfaces = [start_end]
    for i in range(0, len(jigs), 1):
      surfaces.append(jigs[i].srf)
      if(i < len(jigs) - 1):
        surfaces.append(jigs[i].connector)
    surfaces.append(end_end)
    surface = rs.JoinSurfaces(surfaces, True)
    rs.CapPlanarHoles(surface)
    print rs.IsObjectSolid(surface)


  def closest_intersection(self, intersections, point):
    closest_intersection = intersections[0][1]
    length = rs.VectorLength(rs.VectorCreate(point, closest_intersection))
    for i in range(0, len(intersections), 1):
      new_length = rs.VectorLength(rs.VectorCreate(point, intersections[i][1]))
      if length > new_length:
        length = new_length
        closest_intersection = intersections[i][1]
    return closest_intersection

  def points_from_ellipse(self, index):
    ellipse = self.cross_sections[index]
    even = index % 2 == 0

    ellipse_domain = rs.CurveDomain(ellipse)
    ellipse_step = (ellipse_domain[1] - ellipse_domain[0])/self.POINTS_ON_CROSS_SECTION
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

  def add_text(self):
    for i in range(0, len(self.point_lists)):
      rs.AddText(str(i), self.cross_section_planes[i].Origin, 5)
      for j in range(0, len(self.point_lists[i])):
        rs.AddText(str(j), self.point_lists[i][j], 2)

  def points_for_lines(self):
    self.line_points = []
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
        else:
          point_1_index = (j) % modulo
          point_2_index = ((j) - 1) % modulo
          offset_points_1 = self.move_point_down(self.point_lists[i][point_1_index], i, point_1_index)
          offset_points_2 = self.move_point_up(self.point_lists[i][point_2_index], i, point_2_index)
          points_1.append(offset_points_1[0])
          points_1.append(offset_points_1[1])
          points_2.append(offset_points_2[0])
          points_2.append(offset_points_2[1])
      self.line_points.append(points_1)
      self.line_points.append(points_2)

  def offset_vector(self, point, cross_section_index, point_index):
      modulo = len(self.point_lists[cross_section_index])
      closest_point = rs.CurveClosestPoint(self.cross_sections[cross_section_index], point)
      crv = rs.CurveCurvature(self.cross_sections[cross_section_index], closest_point)
      crvTangent = crv[1]
      crvPerp = rs.VectorUnitize(crv[4])
      unit_vector = rs.VectorUnitize(crvTangent)
      return [rs.VectorScale(unit_vector, 0.35), rs.VectorReverse(rs.VectorCrossProduct(crvTangent, crvPerp))]

  def move_point_up(self, point, cross_section_index, point_index):
    offset_vectors = self.offset_vector(point, cross_section_index, point_index)
    normal = offset_vectors[0]
    scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.FLAT_LENGTH/2)
    new_point = rs.PointAdd(point, normal)
    return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]

  def move_point_down(self, point, cross_section_index, point_index):
    offset_vectors = self.offset_vector(point, cross_section_index, point_index)
    normal = rs.VectorReverse(offset_vectors[0])
    scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.FLAT_LENGTH/2)
    new_point = rs.PointAdd(point, normal)
    return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]

  def create_lines(self):
    self.line_lists = []
    for i in range(0, len(self.line_points)):
      line_list = []
      for j in range(0, len(self.line_points[i]) - 1):
        line_list.append(rs.AddLine(self.line_points[i][j], self.line_points[i][j + 1]))
      self.line_lists.append(line_list)

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
    t = crvdomain[0] + (t_step/2)
    while t < crvdomain[1]:
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

class JigPiece:
  def __init__(self, srf, start_corners, end_corners, across):
    self.srf = srf
    self.start_corners = start_corners
    self.end_corners = end_corners
    self.across = across

  def addConnector(self, connector):
    self.connector = connector



rs.EnableRedraw(False)
PathLattice()
rs.EnableRedraw(True)
