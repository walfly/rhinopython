import pytest
from cloudNodeList import CloudNodeList
from cloudNode import CloudNode

def test_array():
  test_array = []
  for i in xrange(1, 12):
    test_array.append(CloudNode(i))
  return test_array

def test_creation():
  nodeList = CloudNodeList(test_array())
  assert len(nodeList.node_list) == 11

def test_set_starts():
  nodeList = CloudNodeList(test_array())
  nodeList.set_starts()
  assert nodeList.node_list[0].get_pos_in() == 'blocked'
  assert nodeList.node_list[0].get_neg_in() == 'blocked'
  assert nodeList.node_list[1].get_pos_in() == 'blocked'
  assert nodeList.node_list[1].get_neg_in() == 'blocked'
  assert nodeList.pos_start == nodeList.node_list[0]
  assert nodeList.neg_start == nodeList.node_list[1]

def test_choose_lights():
  nodeList = CloudNodeList(test_array())
  nodeList.choose_lights([2, 5, 7, 8, 9, 10])
  assert nodeList.lights = [2, 5, 7, 8, 9, 10]

def test_connect_nodes():
  nodeList = CloudNodeList(test_array())
  nodeList.set_starts()
  nodeList.choose_lights([2, 5, 7, 8, 9, 10])
  nodeList.connect_nodes()
  assert