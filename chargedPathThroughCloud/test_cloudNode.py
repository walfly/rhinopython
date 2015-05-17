import pytest
from cloudNode import CloudNode

def test_node_name():
  node = CloudNode(1)
  assert node.name == 1

def test_set_and_get_possitive_in():
  node = CloudNode(1)
  node2 = CloudNode(2)
  node.set_pos_in(node2)
  assert node.get_pos_in() == node2

def test_set_and_get_possitive_out():
  node = CloudNode(1)
  node2 = CloudNode(2)
  node.set_pos_out(node2)
  assert node.get_pos_out() == node2

def test_set_and_get_neg_in():
  node = CloudNode(1)
  node2 = CloudNode(2)
  node.set_neg_in(node2)
  assert node.get_neg_in() == node2

def test_set_and_get_neg_out():
  node = CloudNode(1)
  node2 = CloudNode(2)
  node.set_neg_out(node2)
  assert node.get_neg_out() == node2

def test_already_connected_when_already_connected():
  node = CloudNode(1)
  node2 = CloudNode(2)
  node.set_pos_in(node2)
  assert node.already_connected(node2) == True

def test_already_connected_when_not_already_connected():
  node = CloudNode(1)
  node2 = CloudNode(2)
  assert node.already_connected(node2) == False

def test_make_start():
  node = CloudNode(1)
  assert node.make_start_node() == node
  assert node.get_pos_in() == 'blocked'
  assert node.get_neg_in() == 'blocked'

def test_has_open_connections():
  node = CloudNode(1)
  print node.has_open_connections()
  assert node.has_open_connections() == True

def test_doesnt_have_open_connections():
  node = CloudNode(1)
  node.make_start_node()
  node.set_neg_out('blocked')
  node.set_pos_out('blocked')
  assert node.has_open_connections() == False


