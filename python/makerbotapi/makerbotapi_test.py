#!/usr/bin/python

"""Unit tests for makerbotapi."""

import socket
import unittest

import makerbotapi
import mock


JSONRPC_HANDSHAKE_RESPONSE = '{"result": {"commit": "5924ea5", "machine_type": "platypus", "ip": "169.254.0.79", "iserial": "1234567890ABCDEFG", "port": "9999", "firmware_version": {"minor": 2, "bugfix": 0, "major": 1, "build": 112}, "vid": 9153, "builder": "Release_Birdwing_1.0", "pid": 5, "machine_name": "MakerBot Replicator"}, "jsonrpc": "2.0", "id": 0}'


class MakerbotTest(unittest.TestCase):

  def setUp(self):
    self.handle = mock.Mock()
    self.handle.connect = mock.Mock()
    self.handle.sendall = mock.Mock()
    self.handle.recv.return_value = ''
    self.handle.close = mock.Mock()

    socket.socket = mock.Mock(return_value=self.handle)
    
    self.makerbot = makerbotapi.Makerbot('169.254.0.79', auto_connect=False)

  def testDoHandshake(self):
    self.handle.recv.return_value = JSONRPC_HANDSHAKE_RESPONSE
    
    self.makerbot.DoHandshake()

    self.assertEqual(self.makerbot.builder, 'Release_Birdwing_1.0')
    self.assertEqual(self.makerbot.commit, '5924ea5')
    self.assertEqual(self.makerbot.firmware_version['major'], 1)
    self.assertEqual(self.makerbot.firmware_version['minor'], 2)
    self.assertEqual(self.makerbot.firmware_version['bugfix'], 0)
    self.assertEqual(self.makerbot.firmware_version['build'], 112)
    self.assertEqual(self.makerbot.iserial, '1234567890ABCDEFG')
    self.assertEqual(self.makerbot.machine_name, 'MakerBot Replicator')
    self.assertEqual(self.makerbot.machine_type, 'platypus')
    self.assertEqual(self.makerbot.vid, 9153)


if __name__ == '__main__':
    unittest.main()
