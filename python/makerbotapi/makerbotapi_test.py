#!/usr/bin/python

"""Unit tests for makerbotapi."""

import os
import socket
import time
import unittest
import urllib2
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import makerbotapi
import mock

FCGI_ANSWER_PENDING_RESPONSE = '{"answer": "pending", "username": "Anonymous"}'
FCGI_ANSWER_ACCEPTED_RESPONSE = '{"code": "abcde", "username": "Anonymous", "answer": "accepted"}'
FCGI_CODE_RESPONSE = '{"client_id": "MakerWare", "username": "Anonymous", "status": "ok", "answer_code": "12345"}'
FCGI_TOKEN_RESPONSE = '{"status": "success", "username": "Anonymous", "access_token": "12345abcde"}'
FCGI_TOKEN_FAILED_RESPONSE = '{"status": "error", "message": "Access denied: auth_code=12345"}'

JSONRPC_HANDSHAKE_RESPONSE = '{"result": {"commit": "5924ea5", "machine_type": "platypus", "ip": "169.254.0.79", "iserial": "1234567890ABCDEFG", "port": "9999", "firmware_version": {"minor": 2, "bugfix": 0, "major": 1, "build": 112}, "vid": 9153, "builder": "Release_Birdwing_1.0", "pid": 5, "machine_name": "MakerBot Replicator"}, "jsonrpc": "2.0", "id": 0}'
JSONRPC_GET_SYTEM_INFORMATION_RESPONSE = '{"result": {"version": "0.0.1", "disabled_errors": [], "suspended_processes": {}, "machine_type": "tinkerbell", "machine": {"machine_error": 256, "move_buffer_available_space": 100, "step": "running", "extruder_temp": 29, "toolhead_0_status": {"current_mag": -256, "error": 0, "tool_id": 1, "filament_fan_running": false, "filament_presence": true, "extrusion_percent": 0, "filament_jam": false, "encoder_adc": 0}, "state": "idle", "preheat_percent": 0, "toolhead_0_heating_status": {"current_temperature": 29, "preheating": 0, "target_temperature": 0}}, "machine_name": "MakerBot Replicator Mini", "has_been_connected_to": true, "current_processes": {}, "ip": "192.168.23.44", "firmware_version": {"build": 112, "minor": 2, "bugfix": 0, "major": 1}}, "jsonrpc": "2.0", "id": 0}'
JSONRPC_NOT_AUTHENTICATED_RESPONSE = '{"id": 2, "jsonrpc": "2.0", "error": {"code": -32601, "message": "method not found"}}'
JSONRPC_AUTHENTICATED_RESPONSE = '{"jsonrpc": "2.0", "result": null, "id": 0}'

BROADCAST_RESPONSE = '{"commit": "5924ea5", "machine_type": "platypus", "ip": "169.254.0.79", "iserial": "1234567890ABCDEFG", "port": "9999", "firmware_version": {"minor": 2, "bugfix": 0, "major": 1, "build": 112}, "vid": 9153, "builder": "Release_Birdwing_1.0", "pid": 5, "machine_name": "MakerBot Replicator"}'


mock_time = mock.Mock()


class MakerbotTest(unittest.TestCase):

    def setUp(self):
        self.handle = mock.Mock()
        self.handle.connect = mock.Mock()
        self.handle.sendall = mock.Mock()
        self.handle.recv.return_value = ''
        self.handle.close = mock.Mock()

        socket.socket = mock.Mock(return_value=self.handle)
        urllib2.urlopen = mock.Mock()

        self.makerbot = makerbotapi.Makerbot(
            '169.254.0.79', auto_connect=False)

    @mock.patch('time.sleep', mock.Mock())
    def test_authenticate_fcgi(self):
        urllib2.urlopen.side_effect = [StringIO(FCGI_CODE_RESPONSE),
                                       StringIO(FCGI_ANSWER_PENDING_RESPONSE),
                                       StringIO(FCGI_ANSWER_ACCEPTED_RESPONSE)]
        self.makerbot.authenticate_fcgi()

        self.assertEqual(self.makerbot.auth_code, 'abcde')

    @mock.patch('time.time', mock_time)
    @mock.patch('time.sleep', mock.Mock())
    def test_authenticate_fcgi_timeout(self):
        urllib2.urlopen.side_effect = [StringIO(FCGI_CODE_RESPONSE),
                                       StringIO(FCGI_ANSWER_PENDING_RESPONSE),
                                       StringIO(FCGI_ANSWER_PENDING_RESPONSE)]
        mock_time.side_effect = [1,
                                 self.makerbot.auth_timeout - 5,
                                 self.makerbot.auth_timeout + 1]

        self.assertRaises(makerbotapi.AuthenticationTimeout,
                          self.makerbot.authenticate_fcgi)

    def test_do_handshake(self):
        self.handle.recv.return_value = JSONRPC_HANDSHAKE_RESPONSE

        self.makerbot.do_handshake()

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

    def test_get_access_token(self):
        urllib2.urlopen.return_value = StringIO(FCGI_TOKEN_RESPONSE)
        self.assertEqual(
            self.makerbot.get_access_token('jsonrpc'), '12345abcde')

        self.assertRaises(makerbotapi.InvalidContextError,
                          self.makerbot.get_access_token,
                          'test')

        urllib2.urlopen.return_value = StringIO(FCGI_TOKEN_FAILED_RESPONSE)
        self.assertRaises(makerbotapi.AuthenticationError,
                          self.makerbot.get_access_token,
                          'jsonrpc')

#    def test_get_system_information(self):
#        self.handle.recv.return_value = JSONRPC_GET_SYTEM_INFORMATION_RESPONSE
#        botstate = self.makerbot.get_system_information()
#        self.assertEqual(botstate.step, botstate.STEP_RUNNING)
#        self.assertEqual(botstate.extruder_temp, 29)
#        self.assertEqual(botstate.state, botstate.STATE_IDLE)
#        self.assertEqual(botstate.preheat_percent, 0)
#
#        self.assertEqual(botstate.get_tool_head_count(), 1)
#        toolhead = botstate.toolheads[0]
#        self.assertEqual(toolhead.filament_fan_running, False)
#        self.assertEqual(toolhead.filament_presence, True)
#        self.assertEqual(toolhead.extrusion_percent, 0)
#        self.assertEqual(toolhead.filament_jam, False)
#        self.assertEqual(toolhead.current_temperature, 29)
#        self.assertEqual(toolhead.preheating, 0)
#        self.assertEqual(toolhead.target_temperature, 0)

    def testNotAuthenticated(self):
        self.handle.recv.return_value = JSONRPC_NOT_AUTHENTICATED_RESPONSE
        self.assertRaises(
            makerbotapi.NotAuthenticated, self.makerbot.get_system_information)

    def test_authenticate_json_rpc(self):
        urllib2.urlopen.return_value = StringIO(FCGI_TOKEN_RESPONSE)
        self.handle.recv.return_value = JSONRPC_AUTHENTICATED_RESPONSE
        self.makerbot.authenticate_json_rpc()
        self.assertTrue(self.makerbot.jsonrpc_authenticated)

    def test__get_raw_camera_image_data(self):
        curr_path = os.path.dirname(__file__)
        camera_response = os.path.join(
            curr_path, 'test_output/camera_response')
        urllib2.urlopen.return_value = open(camera_response)
        self.makerbot.get_access_token = mock.Mock(return_value='abcdef1234')
        tpl = self.makerbot._get_raw_camera_image_data()
        self.assertEquals(tpl[:4], (153616, 320, 240, 1))


class ModuleTest(unittest.TestCase):

    def setUp(self):
        self.handle = mock.Mock()
        self.handle.recvfrom = mock.Mock()
        self.handle.sendto = mock.Mock()
        self.handle.recvfrom.return_value = ('', '1.2.3.4')
        self.handle.close = mock.Mock()

    def test_discover(self):
        sock_mock = mock.Mock()
        sock_mock.recvfrom.return_value = (
            BROADCAST_RESPONSE, ('192.168.1.1', 12345))
        socket.socket = mock.Mock(return_value=sock_mock)
        socks = makerbotapi.createSockets()
        ans = makerbotapi.discover(socks)
        self.assertEquals(
            ans, [('192.168.1.1', u'MakerBot Replicator', u'1234567890ABCDEFG')])


if __name__ == '__main__':
    unittest.main()
