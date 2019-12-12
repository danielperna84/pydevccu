import os
import sys
import time
import logging
import threading
import json
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from pydevccu.const import IP_LOCALHOST_V4, PORT_RF, DEVICE_DESCRIPTIONS, PARAMSET_DESCRIPTIONS
from pydevccu.proxy import LockingServerProxy

LOG = logging.getLogger(__name__)
if sys.stdout.isatty():
    logging.basicConfig(level=logging.DEBUG)
    LOG.addHandler(logging.StreamHandler(sys.stdout))

# Object holding the methods the XML-RPC server should provide.
class RPCFunctions():
    def __init__(self):
        LOG.debug("RPCFunctions.__init__")
        self.remotes = {}
        try:
            self.devices = []
            self.paramset_descriptions = {}
            script_dir = os.path.dirname(__file__)
            dd_rel_path = DEVICE_DESCRIPTIONS
            dd_path = os.path.join(script_dir, dd_rel_path)
            for filename in os.listdir(dd_path):
                with open(os.path.join(dd_path, filename)) as fptr:
                    self.devices.extend(json.load(fptr))
            pd_rel_path = PARAMSET_DESCRIPTIONS
            pd_path = os.path.join(script_dir, pd_rel_path)
            for filename in os.listdir(pd_path):
                with open(os.path.join(pd_path, filename)) as fptr:
                    pd = json.load(fptr)
                    for k, v in pd.items():
                        self.paramset_descriptions[k] = v
        except Exception as err:
            LOG.debug("RPCFunctions.__init__: Exception: %s" % err)
            self.devices = []

    def _askDevices(self, interface_id):
        LOG.debug("RPCFunctions._askDevices: waiting")
        time.sleep(0.5)
        knownDevices = self.remotes[interface_id].listDevices(interface_id)
        LOG.debug("RPCFunctions._askDevices: %s" % knownDevices)
        t = threading.Thread(name='_pushDevices',
                             target=self._pushDevices,
                             args=(interface_id, ))
        t.start()

    def _pushDevices(self, interface_id):
        LOG.debug("RPCFunctions._pushDevices: waiting")
        time.sleep(0.5)
        self.remotes[interface_id].newDevices(interface_id, self.devices)
        LOG.debug("RPCFunctions._pushDevices: pushed")

    def listDevices(self, interface_id=None):
        LOG.debug("RPCFunctions.listDevices: interface_id = %s" % interface_id)
        return self.devices

    def getServiceMessages(self):
        LOG.debug("RPCFunctions.getServiceMessages")
        return [['VCU0000001:1', 'ERROR', 7]]

    def getValue(self, address, value_key):
        LOG.debug("RPCFunctions.getValue: address=%s, value_key=%s" % (address, value_key))
        return True

    def setValue(self, address, value_key, value):
        LOG.debug("RPCFunctions.getValue: address=%s, value_key=%s, value=%s" % (address, value_key, value))
        return ""

    def getDeviceDescription(self, address):
        LOG.debug("RPCFunctions.getDeviceDescription: address=%s" % (address, ))
        for device in self.devices:
            if device.get('ADDRESS') == address:
                return device
        raise Exception

    def getParamsetDescription(self, address, paramset):
        LOG.debug("RPCFunctions.getParamsetDescription: address=%s, paramset=%s" % (address, paramset))
        return self.paramset_descriptions[address][paramset]

    def init(self, url, interface_id=None):
        LOG.debug("RPCFunctions.init: url=%s, interface_id=%s" % (url, interface_id))
        if interface_id:
            try:
                self.remotes[interface_id] = LockingServerProxy(url)
                t = threading.Thread(name='_askDevices',
                                     target=self._askDevices,
                                     args=(interface_id, ))
                t.start()
            except Exception as err:
                LOG.debug("RPCFunctions.init:Exception: %s" % (err))
        return ""

class RequestHandler(SimpleXMLRPCRequestHandler):
    """We handle requests to / and /RPC2"""
    rpc_paths = ('/', '/RPC2',)

class ServerThread(threading.Thread):
    """XML-RPC server thread to handle messages from CCU / Homegear"""
    def __init__(self, local=IP_LOCALHOST_V4, localport=PORT_RF):
        self._local = local
        self._localport = localport
        LOG.debug("ServerThread.__init__")
        threading.Thread.__init__(self)

        # Create proxies to interact with CCU / Homegear
        LOG.debug("__init__: Registering RPC methods")
        self._rpcfunctions = RPCFunctions()

        # Setup server to handle requests from CCU / Homegear
        LOG.debug("ServerThread.__init__: Setting up server")
        self.server = SimpleXMLRPCServer((self._local, self._localport),
                                         requestHandler=RequestHandler,
                                         logRequests=False, allow_none=True)
        self._localport = self.server.socket.getsockname()[1]
        self.server.register_introspection_functions()
        self.server.register_multicall_functions()
        LOG.debug("ServerThread.__init__: Registering RPC functions")
        self.server.register_instance(
            self._rpcfunctions, allow_dotted_names=True)

    def run(self):
        LOG.info("Starting server at http://%s:%i" %
                 (self._local, self._localport))
        self.server.serve_forever()

    def stop(self):
        """Shut down our XML-RPC server."""
        LOG.info("Shutting down server")
        self.server.shutdown()
        LOG.debug("ServerThread.stop: Stopping ServerThread")
        self.server.server_close()
        LOG.info("Server stopped")
