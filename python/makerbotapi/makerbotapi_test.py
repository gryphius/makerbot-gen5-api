#!/usr/bin/python

"""Unit tests for makerbotapi."""

import socket
import unittest

import makerbotapi
import mock


JSONRPC_HANDSHAKE_RESPONSE = '{"result": {"commit": "5924ea5", "machine_type": "platypus", "ip": "169.254.0.79", "iserial": "1234567890ABCDEFG", "port": "9999", "firmware_version": {"minor": 2, "bugfix": 0, "major": 1, "build": 112}, "vid": 9153, "builder": "Release_Birdwing_1.0", "pid": 5, "machine_name": "MakerBot Replicator"}, "jsonrpc": "2.0", "id": 0}'
JSONRPC_GET_SYTEM_INFORMATION_RESPONSE = '{"result": {"version": "0.0.1", "disabled_errors": [], "suspended_processes": {}, "machine_type": "tinkerbell", "machine": {"machine_error": 256, "move_buffer_available_space": 100, "step": "running", "extruder_temp": 29, "toolhead_0_status": {"current_mag": -256, "error": 0, "tool_id": 1, "filament_fan_running": false, "filament_presence": true, "extrusion_percent": 0, "filament_jam": false, "encoder_adc": 0}, "state": "idle", "preheat_percent": 0, "toolhead_0_heating_status": {"current_temperature": 29, "preheating": 0, "target_temperature": 0}}, "machine_name": "MakerBot Replicator Mini", "has_been_connected_to": true, "current_processes": {}, "ip": "192.168.23.44", "firmware_version": {"build": 112, "minor": 2, "bugfix": 0, "major": 1}}, "jsonrpc": "2.0", "id": 0}'
JSONRPC_NOT_AUTHENTICATED_RESPONSE = '{"id": 2, "jsonrpc": "2.0", "error": {"code": -32601, "message": "method not found"}}'
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

  def testGetSystemInformation(self):
      self.handle.recv.return_value = JSONRPC_GET_SYTEM_INFORMATION_RESPONSE
      botstate=self.makerbot.GetSystemInformation()
      self.assertEqual(botstate.step, botstate.STEP_RUNNING)
      self.assertEqual(botstate.extruder_temp, 29)
      self.assertEqual(botstate.state, botstate.STATE_IDLE)
      self.assertEqual(botstate.preheat_percent, 0)
      
      self.assertEqual(botstate.GetToolHeadCount(),1)
      toolhead=botstate.toolheads[0]
      self.assertEqual(toolhead.filament_fan_running, False)
      self.assertEqual(toolhead.filament_presence, True)
      self.assertEqual(toolhead.extrusion_percent, 0)
      self.assertEqual(toolhead.filament_jam, False)
      self.assertEqual(toolhead.current_temperature, 29)
      self.assertEqual(toolhead.preheating, 0)
      self.assertEqual(toolhead.target_temperature, 0)
      

  def testNotAuthenticated(self):
      self.handle.recv.return_value = JSONRPC_NOT_AUTHENTICATED_RESPONSE
      self.assertRaises(makerbotapi.NotAuthenticated, self.makerbot.GetSystemInformation)
      

if __name__ == '__main__':
    unittest.main()
