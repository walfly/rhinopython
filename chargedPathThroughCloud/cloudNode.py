class CloudNode:
  """An point in the point list"""

  def __init__(self, name):
    self.connections = {}
    self.connction_names = ['posIn', 'negIn']
    self.name = name

  def set_pos_in(self, node):
    self.connections['posIn'] = node
    return self

  def set_pos_out(self, node):
    self.connections['posOut'] = node
    return self

  def set_neg_in(self, node):
    self.connections['negIn'] = node
    return self

  def set_neg_out(self, node):
    self.connections['negOut'] = node
    return self

  def set_index(self, index):
    self.index = index
    return self

  def get_pos_in(self):
    return self.connections['posIn']

  def get_pos_out(self):
    return self.connections['posOut']

  def get_neg_in(self):
    return self.connections['negIn']

  def get_neg_out(self):
    return self.connections['negOut']

  def make_start_node(self):
    self.connections['posIn'] = 'blocked'
    self.connections['negIn'] = 'blocked'
    return self

  def has_open_connections(self):
    open_connections = False
    for v in self.connction_names:
      if v not in self.connections:
        open_connections = True
    return open_connections

  def already_connected(self, node):
    isAlreadyConnected = False
    for k,v in self.connections.items():
      if v == node:
        isAlreadyConnected = True
    return isAlreadyConnected

