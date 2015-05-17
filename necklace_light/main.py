import rhinoscriptsyntax as rs
import math

samples = 15

bend_radius = 4

perp_radius = 2

points_on_cross_section = 20

def create_scalar(step):
  squared = math.sin(step) * math.sin(step)
  return 4 * (squared + 1)

def points_from_ellipse(ellipse, even):
  ellipse_domain = rs.CurveDomain(ellipse)
  ellipse_step = (ellipse_domain[1] - ellipse_domain[0])/points_on_cross_section
  points = []
  j = 0
  for i in rs.frange(ellipse_domain[0], ellipse_domain[1], ellipse_step):
    if even:
      if j % 2 == 0:
        points.append(rs.EvaluateCurve(ellipse, i))
    else:
      if (j + 1) % 2 == 0:
        points.append(rs.EvaluateCurve(ellipse, i))
    j += 1
  return points

def points_from_cross(cross_sections):
  arr = []
  for i in range(0, len(cross_sections)):
    points = points_from_ellipse(cross_sections[i], i % 2 == 0)
    arr.append(points)
  return arr

def add_spheres(points):
  print(points)
  for i in range(0, len(points)):
    for j in range(0, len(points[i])):
      rs.AddSphere(points[i][j], 1)

def FlatWorm():
  curve_object = rs.GetObject("Pick a backbone curve", 4, True, False)
  if not curve_object:
    return

  crvdomain = rs.CurveDomain(curve_object)
  crosssections = []

  t_step = (crvdomain[1]-crvdomain[0])/samples
  pi_step_size = math.pi/samples
  pi_step = 0

  for t in rs.frange(crvdomain[0], crvdomain[1], t_step):
    crvcurvature = rs.CurveCurvature(curve_object, t)
    crosssectionplane = None
    if not crvcurvature:
      crvPoint = rs.EvaluateCurve(curve_object, t)
      crvTangent = rs.CurveTangent(curve_object, t)
      crvPerp = (0,0,1)
      crvNormal = rs.VectorCrossProduct(crvTangent, crvPerp)
      crosssectionplane = rs.PlaneFromFrame(crvPoint, crvPerp, crvNormal)
    else:
      crvPoint = crvcurvature[0]
      crvTangent = crvcurvature[1]
      crvPerp = rs.VectorUnitize(crvcurvature[4])
      crvNormal = rs.VectorCrossProduct(crvTangent, crvPerp)
      crosssectionplane = rs.PlaneFromFrame(crvPoint, crvPerp, crvNormal)
    if crosssectionplane:
      pi_scalar = create_scalar(pi_step)
      new_br = bend_radius * pi_scalar
      new_pr = perp_radius * pi_scalar
      csec = rs.AddEllipse(crosssectionplane, new_br, new_pr)
      crosssections.append(csec)
    pi_step += pi_step_size

  if not crosssections:
    return

  points = points_from_cross(crosssections)
  add_spheres(points)
  # lines = polyline_lists(points)
  # add_polylines(lines)
  rs.DeleteObjects(crosssections)

FlatWorm()