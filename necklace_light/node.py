import rhinoscriptsyntax as rs

class Node:
  def __init__(self, fv, fc, mfc, ofv, ofc, sv, sc, msc, osv, osc):
    self.first_vector = fv
    self.opposite_first_vector = ofv
    self.second_vector = sv
    self.opposite_second_vector = osv
    self.first_loft = self.loft(fc, mfc, ofc)
    # self.second_loft = self.loft(sc, msc, osc)

  def loft(self, f, s, t):
    if not rs.CurveDirectionMatch(f, s):
      rs.ReverseCurve(s)
    if not rs.CurveDirectionMatch(s, t):
      rs.ReverseCurve(t)
    return rs.AddLoftSrf([f,s,t])