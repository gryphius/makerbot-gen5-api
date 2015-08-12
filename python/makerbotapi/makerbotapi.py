#!/usr/bin/python
#
# Copyright Jeff Rebeiro (jeff@rebeiro.net)

"""Makerbot Gen 5 API."""

import sys
import json
import socket
import time
import urllib
import urllib2
import ctypes
import struct
import png

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class Error(Exception):

    """Error."""


class AuthenticationError(Error):

    """Authentication timed out."""


class AuthenticationTimeout(Error):

    """Authentication timed out."""


class InvalidContextError(Error):

    """Invalid context."""


class MakerBotError(Error):

    """MakerBot Error."""


class NotAuthenticated(Error):

    """Access to privileged method call denied."""


class UnexpectedJSONResponse(Error):
    #Here's what the JSON should look like (When a process is not running):
    #
    #https://jsonblob.com/55bfee62e4b0f6d7e5be5aca

    """Unexpected JSON Response."""
    
    


class Toolhead(object):

    def __init__(self):
        self.tool_id = None
        self.filament_presence = None
        self.preheating = None
        self.index = None
        self.tool_present = None
        self.current_temperature = None
        self.target_temperature = None


def discover():
    """Discover Makerbot Gen5 in the network

        Args:

        Returns:
          a list of tuples in the form ('<ipaddress>','<machine name>','<serial>')
    """
    
    bcaddr = '255.255.255.255'
    target_port = 12307
    listen_port = 12308
    source_port = 12309
    
    
    broadcastsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcastsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcastsocket.bind(('', source_port))

    answersocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    discover_request = '{"command": "broadcast"}'
    answersocket.bind(('', listen_port))
    answersocket.settimeout(3)
    
    broadcast_dict = {"command" : "broadcast"}
    discover_request = json.dumps(broadcast_dict)
    
    answers = []
    knownbotips = []
    for _ in range(3):
        broadcastsocket.sendto(discover_request, (bcaddr, target_port))
        try:
            data, fromaddr = answersocket.recvfrom(1024)
            if fromaddr not in knownbotips:
                knownbotips.append(fromaddr)
                infodic = json.loads(data)
                machine_name = infodic['machine_name']
                serial = infodic['iserial']
                answers.append((fromaddr[0], machine_name, serial),)
            else:
                continue
        except socket.timeout:
            continue
        time.sleep(1)
    return answers


class BotState(object):

    """Current Bot status data object"""
    STEP_RUNNING = 'running'
    # TODO: find out other step states

    STATE_IDLE = 'idle'
    # TODO: find out other states

    def __init__(self):
        self.step = None
        # TODO: find out how this differs from current_temperatore
        self.extruder_temp = None
        self.toolheads = []
        self.preheat_percent = None
        self.state = None
        self.current_process = None

    def get_tool_head_count(self):
        return len(self.toolheads)

    def __str__(self):
        return '<Bostate state=%s temp=%s>' % (self.state, self.extruder_temp)

class CurrentBotProcess(object):

    def __init__(self):
        self.username = None
        self.name = None
        self.cancellable = None
        self.temperature_settings = []
        self.tool_index = None
        self.step = None
        self.error = None
        self.cancelled = None
        self.id = None
        self.methods = []


class Makerbot(object):

    """MakerBot."""

    def __init__(self, ip, auth_code=None, auto_connect=True):
        self.auth_code = auth_code
        self.auth_timeout = 120
        self.client_id = 'MakerWare'
        self.client_secret = 'python-makerbotapi'
        self.fcgi_retry_interval = 5
        self.host = ip
        self.jsonrpc_port = 9999

        self.builder = None
        self.commit = None
        self.firmware_version = None
        self.iserial = None
        self.machine_name = None
        self.machine_type = None
        self.vid = None

        self.default_params = {'username': 'conveyor',
                               'host_version': '1.0'}
        self.request_id = -1

        self.debug_jsonrpc = False
        self.debug_fcgi = False

        self.rpc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if auto_connect:
            self._connect_json_rpc()
            self.do_handshake()

    def _debug_print(self, protocol, direction, content):
        # TODO(gryphius): Convert this to use logging.debug once we implement
        # logging module support
        sys.stderr.write("(%s) %s: %s\n" % (protocol, direction, content))

    def _connect_json_rpc(self):
        """Create a socket connection to the MakerBot JSON RPC interface."""
        self.rpc_socket.connect((self.host, self.jsonrpc_port),)
        self.jsonrpc_connected = True

    def _disconnect_json_rpc(self):
        """Disconnect from the MakerBot JSON RPC interface."""
        pass

    def _generate_json_rpc(self, method, params, id):
        """Generate a JSON RPC payload.

        Args:
          method: RPC Method to call
          params: dict containing key/value pairs for the RPC method
          id: ID of this request. Must be sequential in order to retrieve the
              correct output from the bot.

        Returns:
          A JSON RPC formatted string.
        """
        jsonrpc = {'id': id,
                   'jsonrpc': '2.0',
                   'method': method,
                   'params': params}
        # TODO(n-i-x): Do some error checking here
        return json.dumps(jsonrpc)

    def _get_request_id(self):
        """Increment the request id counter."""
        self.request_id += 1
        return self.request_id

    def _send_fcgi(self, path, query_args):
        """Send an FCGI request to the MakerBot FCGI interface."""
        encoded_args = urllib.urlencode(query_args)

        url = 'http://%s/%s?%s' % (self.host, path, encoded_args)

        if self.debug_fcgi:
            self._debug_print('FCGI', 'REQUEST', url)

        response = urllib2.urlopen(url)
        if self.debug_fcgi:
            content = response.read()
            self._debug_print('FCGI', 'RESPONSE', content)
            result = json.loads(content)
        else:
            result = json.load(response)

        return result

    def _send_rpc(self, jsonrpc):
        """Send an RPC to the MakerBot JSON RPC interface.

        Args:
          jsonrpc: A JSON RPC request generated by _generate_json_rpc()

        Returns:
          A JSON decoded response
        """
        if self.debug_jsonrpc:
            self._debug_print('JSONRPC', 'REQUEST', jsonrpc)

        self.rpc_socket.sendall(jsonrpc)
        response = self.rpc_socket.recv(2048)

        if self.debug_jsonrpc:
            self._debug_print('JSONRPC', 'RESPONSE', response)

        return json.loads(response)

    def authenticate_fcgi(self):
        """Authenticate to the MakerBot FCGI interface."""
        query_args = {'response_type': 'code',
                      'client_id': self.client_id,
                      'client_secret': self.client_secret}
        response = self._send_fcgi('auth', query_args)

        answer_code = response['answer_code']

        query_args = {'response_type': 'answer',
                      'client_id': self.client_id,
                      'client_secret': self.client_secret,
                      'answer_code': answer_code}
        start_time = time.time()
        while True:
            response = self._send_fcgi('auth', query_args)

            if response.get('answer') == 'accepted':
                self.auth_code = response.get('code')
                break

            if time.time() - start_time >= self.auth_timeout:
                raise AuthenticationTimeout

            time.sleep(self.fcgi_retry_interval)

    def authenticate_json_rpc(self):
        """Authenticate to the MakerBot JSON RPC interface."""
        request_id = self._get_request_id()
        method = 'authenticate'
        params = {
            'access_token': self.get_access_token(context='jsonrpc'),
        }
        jsonrpc = self._generate_json_rpc(
            method, params, request_id)
        response = self._send_rpc(jsonrpc)
        if 'error' in response:
            err = response['error']
            code = err['code']
            message = err['message']
            raise MakerBotError(
                'RPC Error code=%s message=%s' % (code, message))
        else:
            self.jsonrpc_authenticated = True

    def do_handshake(self):
        """Perform handshake with MakerBot over JSON RPC."""
        method = 'handshake'
        request_id = self._get_request_id()
        jsonrpc = self._generate_json_rpc(
            method, self.default_params, request_id)
        response = self._send_rpc(jsonrpc)
        if 'result' in response and len(response.get('result')):
            self.builder = response['result'].get('builder')
            self.commit = response['result'].get('commit')
            self.firmware_version = response['result'].get('firmware_version')
            self.iserial = response['result'].get('iserial')
            self.machine_name = response['result'].get('machine_name')
            self.machine_type = response['result'].get('machine_type')
            self.vid = response['result'].get('vid')

    def get_access_token(self, context):
        """Get an OAuth access token from the MakerBot FCGI interface.

        Args:
          context: Context of the token. Valid contexts are 'camera', 'jsonrpc', 'put'.

        Returns:
          A string containing the access token for the specified context.
        """
        valid_contexts = ['jsonrpc', 'put', 'camera']

        if context not in valid_contexts:
            raise InvalidContextError

        query_args = {'response_type': 'token',
                      'client_id': self.client_id,
                      'client_secret': self.client_secret,
                      'auth_code': self.auth_code,
                      'context': context}
        response = self._send_fcgi('auth', query_args)

        if response.get('status') == 'success':
            return response.get('access_token')
        else:
            raise AuthenticationError(response.get('message'))

    def _get_raw_camera_image_data(self):
        """Request the current camera data

        Returns:
          A tuple total_blob_size, image_width, image_height, pixel_format, latest_cached_image
        """
        access_token = self.get_access_token('camera')
        url = 'http://%s/camera?token=%s' % (self.host, access_token)
        data = urllib2.urlopen(url).read()
        return struct.unpack('!IIII{0}s'.format(len(data) - ctypes.sizeof(ctypes.c_uint32 * 4)), data)


    def get_system_information(self):
        """Get system information from MakerBot over JSON RPC.

        Returns:
          A BotState object
        """
        request_id = self._get_request_id()
        method = 'get_system_information'
        params = {
            'username': 'conveyor'
        }
        jsonrpc = self._generate_json_rpc(
            method, params, request_id)
        response = self._send_rpc(jsonrpc)
        if 'error' in response:
            err = response['error']
            code = err['code']
            message = err['message']
            # 'method not found' means the current connection is not
            # authenticated
            if code == -32601:
                raise NotAuthenticated(message)
            else:
                raise MakerBotError(
                    'RPC Error code=%s message=%s' % (code, message))

        bot_state = BotState()
        
        #Uncommment this line to see the raw JSON the bot is sending
        #print json.dumps(response)
                
        if not response['result']:
            raise UnexpectedJSONResponse(response)
        if 'machine_name' not in response['result']:
           raise UnexpectedJSONResponse(response)
        json_machine_status = response['result']['machine_name']
        print json_machine_status

        for attr in ['step', 'extruder_temp', 'state', 'preheat_percent']:
            if attr in json_machine_status:
                setattr(bot_state, attr, json_machine_status[attr])

        # for now we just support one toolhead (are there any gen5 with
        # multiple heads anyway?)
        toolhead = Toolhead()
        json_toolhead_status = response['result']['toolheads']['extruder'][0]
        #json_toolhead_status = json_machine_status['toolhead_0_status']
        for attr in ['tool_id',
                     'filament_presence',
                     'preheating',
                     'index',
                     'tool_present',
                     'current_temperature',
                     'target_temperature']:
            if attr in json_toolhead_status:
                setattr(toolhead, attr, json_toolhead_status[attr])
        
        bot_state.toolheads.append(toolhead)
        
        #Check to see if there's a process happening.
        if response['result']['current_process']:
            #If the machine is doing something (loading filament, etc.), this will not be None.
            current_bot_process = CurrentBotProcess()
            json_current_process = response['result']['current_process']
            for attr in ['username',
                        'name',
                        'cancellable',
                        'temperature_settings',
                        'tool_index',
                        'step',
                        'complete',
                        'error',
                        'cancelled',
                        'reason',
                        'id',
                        'methods']:
                if attr in json_current_process:
                    setattr(current_bot_process, attr, json_current_process[attr])
        else:
            current_bot_process = None
        
        bot_state.current_process = current_bot_process
        
        return bot_state

    def _rgb_clamp(self, x):
        """Clamp an RGB value between 0 and 255.

        Args:
            x: Value to clamp

        Returns:
          The clamped value
        """
        if x < 0:
            return 0
        elif x > 255:
            return 255
        else:
            return x

    def _rgb_rows_to_png(self, rgb_rows, width, height, output_file):
        """Save RGB rows as returned by self._yuv_to_rgb_rows() as PNG.

        Args:
            rgb_rows: RGB rows as returned by self._yuv_to_rgb_rows()
            output_file: PNG file to save
        """
        f = open(output_file, 'wb')
        png_file = png.Writer(width, height)
        png_file.write(f, rgb_rows)
        f.close()

    def save_camera_png(self, output_file):
        """Save an image from the MakerBot camera in PNG format.

        Args:
            output_file: PNG file to save.
        """
        _, width, height, _, yuv_image = self._get_raw_camera_image_data()
        rgb_rows = self._yuv_to_rgb_rows(StringIO(yuv_image), width, height)
        self._rgb_rows_to_png(rgb_rows, width, height, output_file)

    def _yuv_to_rgb_rows(self, yuv_image, width, height):
        """Convert YUYV422 to RGB pixels.

        Args:
            yuv_image: A file-like object containing YUYV422 image data
            width: Width in pixels
            height: Height in pixels

        Returns:
          A list of lists containing RGB pixel values.
        """
        rgb_rows = []
        for row in range(0, height):
            rgb_row = []
            for column in range(0, width / 2):
                # http://en.wikipedia.org/wiki/YUV#Y.27UV422_to_RGB888_conversion
                # Modified for MakerBot YUYV format
                y1 = ord(yuv_image.read(1))
                u = ord(yuv_image.read(1))
                y2 = ord(yuv_image.read(1))
                v = ord(yuv_image.read(1))

                # http://www.lems.brown.edu/vision/vxl_doc/html/core/vidl_vil1/html/vidl__vil1__yuv__2__rgb_8h.html
                R = 1.164 * (y1 - 16) + 1.596 * (v - 128)
                G = 1.164 * (y1 - 16) - 0.813 * (v - 128) - 0.391 * (u - 128)
                B = 1.164 * (y1 - 16) + 2.018 * (u - 128)
                rgb_row.append(self._rgb_clamp(int(R)))
                rgb_row.append(self._rgb_clamp(int(G)))
                rgb_row.append(self._rgb_clamp(int(B)))

                R = 1.164 * (y2 - 16) + 1.596 * (v - 128)
                G = 1.164 * (y2 - 16) - 0.813 * (v - 128) - 0.391 * (u - 128)
                B = 1.164 * (y2 - 16) + 2.018 * (u - 128)
                rgb_row.append(self._rgb_clamp(int(R)))
                rgb_row.append(self._rgb_clamp(int(G)))
                rgb_row.append(self._rgb_clamp(int(B)))
            rgb_rows.append(rgb_row)
        return rgb_rows
