import rhinoscriptsyntax as rs
import math


class PathLattice:
  SAMPLES = 25

  BEND_RADIUS = 2

  PERP_RADIUS = 2

  POINTS_ON_CROSS_SECTION = 20

  FLAT_LENGTH = 1

  RADIUS_SCALAR = 2.5

  def __init__(self):
    self.curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
    self.create_cross_sections()
    self.brep = rs.AddLoftSrf(self.cross_sections)
    self.points_from_cross()
    # self.add_text()
    self.points_for_lines()
    self.create_lines()
    self.fillet_lines()
    self.pipe_lines()
    # self.delete_cross_sections()
    rs.DeleteObjects(self.brep)


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
      modulo = len(self.point_lists[cross_section_index - 1])
      # prev_point_1 = self.point_lists[cross_section_index - 1][(point_index - 1) % modulo] if cross_section_index % 2 == 0 else self.point_lists[cross_section_index - 1][(point_index + 1) % modulo]
      # prev_point_2 = self.point_lists[cross_section_index - 1][point_index]
      # in_between_vector = rs.VectorAdd(rs.VectorCreate(prev_point_1, point), rs.VectorCreate(prev_point_2, point))
      # normal_vector = rs.SurfaceNormal(self.brep, rs.SurfaceClosestPoint(self.brep, point))
      closest_point = rs.CurveClosestPoint(self.cross_sections[cross_section_index], point)
      crv = rs.CurveCurvature(self.cross_sections[cross_section_index], closest_point)
      crvTangent = crv[1]
      crvPerp = rs.VectorUnitize(crv[4])
      # plane = rs.PlaneFromFrame(point, in_between_vector, normal_vector)
      # surf = rs.AddPlaneSurface(plane, 1, 1)
      # vector = rs.SurfaceNormal(surf, [0,0])
      # rs.DeleteObjects(surf)
      unit_vector = rs.VectorUnitize(crvTangent)
      return [rs.VectorScale(unit_vector, 0.45), crvPerp]

  def move_point_up(self, point, cross_section_index, point_index):
    if(cross_section_index > 0):
      offset_vectors = self.offset_vector(point, cross_section_index, point_index)
      normal = offset_vectors[0]
      scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.FLAT_LENGTH/2)
      new_point = rs.PointAdd(point, normal)
      return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]
    else:
      curve = self.cross_sections[cross_section_index]
      parameter = rs.CurveClosestPoint(curve, point)
      tangent = rs.CurveTangent(curve, parameter)
      unit_vector = rs.VectorUnitize(tangent)
      scale_vector = rs.VectorScale(unit_vector, 0.25)
      return [rs.PointAdd(point, scale_vector)]

  def move_point_down(self, point, cross_section_index, point_index):
    if(cross_section_index > 0):
      offset_vectors = self.offset_vector(point, cross_section_index, point_index)
      normal = rs.VectorReverse(offset_vectors[0])
      scaled_offset = rs.VectorScale(rs.VectorUnitize(offset_vectors[1]), self.FLAT_LENGTH/2)
      new_point = rs.PointAdd(point, normal)
      return [rs.PointAdd(new_point, scaled_offset), rs.PointAdd(new_point, rs.VectorReverse(scaled_offset))]
    else:
      curve = self.cross_sections[cross_section_index]
      parameter = rs.CurveClosestPoint(curve, point)
      tangent = rs.CurveTangent(curve, parameter)
      unit_vector = rs.VectorUnitize(tangent)
      scale_vector = rs.VectorReverse(rs.VectorScale(unit_vector, 0.25))
      return [rs.PointAdd(point, scale_vector)]

  def create_lines(self):
    self.line_lists = []
    for i in range(0, len(self.line_points)):
      line_list = []
      for j in range(0, len(self.line_points[i]) - 1):
        line_list.append(rs.AddLine(self.line_points[i][j], self.line_points[i][j + 1]))
      self.line_lists.append(line_list)

  def fillet_lines(self):
    self.lines = []
    for i in range(0, len(self.line_lists)):
      fillets = []
      new_line = []
      for j in range(0, len(self.line_lists[i]) - 1):
        fillets.append(rs.AddFilletCurve(self.line_lists[i][j], self.line_lists[i][j + 1], 0.125))
      for k in range(0, len(self.line_lists[i])):
        line = self.line_lists[i][k]
        if(k < len(self.line_lists[i]) - 1):
          line_domain = rs.CurveDomain(line)
          line_intersect = rs.CurveCurveIntersection(line, fillets[k])[0][5]
          line = rs.TrimCurve(self.line_lists[i][k], (line_domain[0], line_intersect), True)
        if(k > 0):
          line_domain = rs.CurveDomain(line)
          line_intersect = rs.CurveCurveIntersection(line, fillets[k-1])
          line = rs.TrimCurve(line, (line_intersect[0][5], line_domain[1]), True)
        new_line.append(line)
        if(k < len(self.line_lists[i]) - 1):
          new_line.append(fillets[k])
      new_curve = self.get_curve_from_segments(new_line)
      self.lines.append(new_curve)

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

  def pipe_lines(self):
    self.pipes = []
    for i in range(0, len(self.lines)):
      print self.lines[i]
      self.pipes.append(rs.AddPipe(self.lines[i], 0, 0.09375))

    rs.DeleteObjects(self.lines)


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
    return t_step * ((squared * 1.1) + 0.45)

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
      t +=  t_step #self.calc_step(t_step, pi_step)
      pi_step += pi_step_size

rs.EnableRedraw(False)
PathLattice()
rs.EnableRedraw(True)
