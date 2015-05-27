import rhinoscriptsyntax as rs
import math


class PathLattice:
  SAMPLES = 25

  BEND_RADIUS = 4

  PERP_RADIUS = 2

  POINTS_ON_CROSS_SECTION = 20


  def __init__(self):
    self.curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
    self.needs_flip = False
    self.create_cross_sections()
    self.points_from_cross()
    self.add_text()
    self.delete_cross_sections()

    self.create_nodes()



  def create_scalar(self, step):
    squared = math.sin(step) * math.sin(step)
    return 4 * (squared + 1)

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

  def create_nodes(self):
    self.nodes = []
    for i in range(1, len(self.point_lists)):
      if(i+1 < len(self.point_lists)):
        for j in range(0, len(self.point_lists[i])):
          modulo = len(self.point_lists[i])
          if(i % 2 == 0):
            self.nodes.append(Node(
              self.point_lists[i][j],
              self.point_lists[i+1][j],
              self.point_lists[i+1][(j-1) % modulo],
              self.point_lists[i-1][j],
              self.point_lists[i-1][(j-1) % modulo]
              )
            )
          else:
            self.nodes.append(Node(
              self.point_lists[i][j],
              self.point_lists[i+1][(j+1) % modulo],
              self.point_lists[i+1][j],
              self.point_lists[i-1][(j+1) % modulo],
              self.point_lists[i-1][j]
              )
            )

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

  def create_cross_sections(self):
    crvdomain = rs.CurveDomain(self.curve_object)
    self.cross_sections = []
    self.cross_section_planes = []

    t_step = (crvdomain[1]-crvdomain[0])/self.SAMPLES
    pi_step_size = math.pi/self.SAMPLES
    pi_step = 0

    prev_normal = None
    prev_perp = None

    for t in rs.frange(crvdomain[0], crvdomain[1], t_step):
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
      pi_step += pi_step_size

class Node:
  CIRCLE_WIDTH = 0.3
  CIRCLE_INNER_WIDTH = 0.1895
  INNER_PIPE_SCALAR = 0.15
  PIPE_SCALAR = 0.1

  def __init__(self, current_point, next_point_up, next_point_down, prev_point_up, prev_point_down):
    self.middle_point = current_point
    extrusion_nu = self.create_pipe(next_point_up, prev_point_down)
    extrusion_nd = self.create_pipe(next_point_down, prev_point_up)
    self.brep = rs.BooleanUnion([extrusion_nu, extrusion_nd])

  def create_pipe(self, point_n, point_p):
    outer_point_n = self.create_scaled_point(point_n, self.PIPE_SCALAR)
    outer_point_p = self.create_scaled_point(point_p, self.PIPE_SCALAR)
    inner_point_n = self.create_scaled_point(point_n, self.INNER_PIPE_SCALAR)
    inner_point_p = self.create_scaled_point(point_p, self.INNER_PIPE_SCALAR)
    opl = rs.AddPolyline([outer_point_p, self.middle_point, outer_point_n])
    ipl = rs.AddPolyline([inner_point_p, self.middle_point, inner_point_n])
    o_pipe = rs.AddPipe(opl, 0, self.CIRCLE_WIDTH, 1, 1)
    i_pipe = rs.AddPipe(ipl, 0, self.CIRCLE_INNER_WIDTH, 1, 1)
    return rs.BooleanUnion([o_pipe, i_pipe])

  def create_scaled_point(self, p, scalar):
    line = rs.AddLine(self.middle_point, p)
    domain = rs.CurveDomain(line)
    evaluation_pt = (domain[1] - domain[0]) * scalar
    scaled_pt = rs.EvaluateCurve(line, evaluation_pt)
    return scaled_pt

  def unit_vector(self, end_point):
    vector = rs.VectorCreate(self.middle_point, end_point)
    return rs.VectorUnitize(vector)

  def create_circles(self, point_up, point_down):
    vector_up = self.unit_vector(point_up)
    vector_down = self.unit_vector(point_down)
    self.circle_up = self.create_circle(vector_up)
    self.circle_down = self.create_circle(vector_down)

  def create_circle(self, vector):
    plane = rs.PlaneFromNormal(self.middle_point, vector)
    return rs.AddCircle(plane, self.CIRCLE_WIDTH)

  def get_distance(self, point):
    return rs.Distance(self.middle_point, point)

  def delete_circles(self):
    rs.DeleteObjects([self.circle_up, self.circle_down])


rs.EnableRedraw(False)
PathLattice()
rs.EnableRedraw(True)

