from cloudNode import CloudNode

class CloudNodeList:

  def __init__(self, node_list):
    self.node_list = node_list
    self.set_indexes()

  def set_starts(self):
    self.pos_start = self.node_list[0].make_start_node()
    self.neg_start = self.node_list[1].make_start_node()

  def choose_lights(self, indexes):
    self.lights = indexes

  def set_indexes(self):
    for i in xrange(len(self.node_list)):
      self.node_list[i].set_index(i)

  def make_path(self, current_pos = None, current_neg = None, start_index = 0):
    if current_neg == None && current_pos == None:
      current_pos = self.pos_start
      current_neg = self.neg_start

    light_list_index = self.lights[start_index]
    next_node = self.node_list[light_list_index]

    pos = self.connect_nodes(current_pos, next_node, light_list_index, 'pos')
    neg = self.connect_nodes(current_neg, next_node, light_list_index, 'neg')
    self.make_path(pos, neg, start_index + 1)

  def connect_nodes(self, current_node, next_node, index, charge_type):
    if(next_node.already_connected(current_node)):
      index = index + 1
      connect_nodes(current_node, self.node_list[index], index)
    else:
      if charge_type == 'pos':
        return next_node.set_pos_in(current_node)
      else:
        return next_node.set_neg_in(current_node)