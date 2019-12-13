import os
import sys
import time
import logging
import threading
import json
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from pydevccu import const
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
            self.knownDevices = []
            self.interface_id = "pydevccu"
            self.devices = []
            self.paramset_descriptions = {}
            self.states = {}
            script_dir = os.path.dirname(__file__)
            dd_rel_path = const.DEVICE_DESCRIPTIONS
            dd_path = os.path.join(script_dir, dd_rel_path)
            for filename in os.listdir(dd_path):
                with open(os.path.join(dd_path, filename)) as fptr:
                    self.devices.extend(json.load(fptr))
            pd_rel_path = const.PARAMSET_DESCRIPTIONS
            pd_path = os.path.join(script_dir, pd_rel_path)
            for filename in os.listdir(pd_path):
                with open(os.path.join(pd_path, filename)) as fptr:
                    pd = json.load(fptr)
                    for k, v in pd.items():
                        self.paramset_descriptions[k] = v
            if not os.path.exists(const.STATES_DB):
                self._initStates()
            self._loadStates()
        except Exception as err:
            LOG.debug("RPCFunctions.__init__: Exception: %s" % err)
            self.devices = []

    def _initStates(self):
        with open(const.STATES_DB, 'w') as fptr:
            fptr.write("{}")

    def _loadStates(self):
        with open(const.STATES_DB) as fptr:
            self.states = json.load(fptr)

    def _saveStates(self):
        LOG.debug("Saving states")
        with open(const.STATES_DB, 'w') as fptr:
            json.dump(self.states, fptr)

    def _askDevices(self, interface_id):
        LOG.debug("RPCFunctions._askDevices: waiting")
        self.knownDevices = self.remotes[interface_id].listDevices(interface_id)
        LOG.debug("RPCFunctions._askDevices: %s" % self.knownDevices)
        t = threading.Thread(name='_pushDevices',
                             target=self._pushDevices,
                             args=(interface_id, ))
        t.start()

    def _pushDevices(self, interface_id):
        LOG.debug("RPCFunctions._pushDevices: waiting")
        newDevices = [d for d in self.devices if d[const.ATTR_ADDRESS] not in self.paramset_descriptions.keys()]
        self.remotes[interface_id].newDevices(interface_id, newDevices)
        LOG.debug("RPCFunctions._pushDevices: pushed")
        self.knownDevices = []

    def _fireEvent(self, interface_id, address, value_key, value):
        LOG.debug("RPCFunctions._fireEvent: %s, %s, %s, %s", interface_id, address, value_key, value)

    def listDevices(self, interface_id=None):
        LOG.debug("RPCFunctions.listDevices: interface_id = %s" % interface_id)
        return self.devices

    def getServiceMessages(self):
        LOG.debug("RPCFunctions.getServiceMessages")
        return [['VCU0000001:1', 'ERROR', 7]]

    def getValue(self, address, value_key):
        LOG.debug("RPCFunctions.getValue: address=%s, value_key=%s" % (address, value_key))
        try:
            return self.states[address][value_key]
        except:
            return self.paramset_descriptions[address][const.ATTR_VALUES][value_key][const.PARAMSET_ATTR_DEFAULT]

    def setValue(self, address, value_key, value):
        LOG.debug("RPCFunctions.setValue: address=%s, value_key=%s, value=%s" % (address, value_key, value))
        paramsets = self.paramset_descriptions[address]
        paramset_values = paramsets[const.ATTR_VALUES]
        param_data = paramset_values[value_key]
        if not const.PARAMSET_OPERATIONS_WRITE & param_data[const.PARAMSET_ATTR_OPERATIONS]:
            LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: write operation not allowed" % (address, value_key))
            raise Exception
        if param_data[const.PARAMSET_ATTR_TYPE] == const.PARAMSET_TYPE_ACTION:
            self._fireEvent(self.interface_id, address, value_key, True)
            return ""
        if param_data[const.PARAMSET_ATTR_TYPE] == const.PARAMSET_TYPE_BOOL:
            value = bool(value)
        if param_data[const.PARAMSET_ATTR_TYPE] == const.PARAMSET_TYPE_STRING:
            value = str(value)
        if param_data[const.PARAMSET_ATTR_TYPE] in [const.PARAMSET_TYPE_INTEGER, const.PARAMSET_TYPE_ENUM]:
            value = int(float(value))
        if param_data[const.PARAMSET_ATTR_TYPE] == const.PARAMSET_TYPE_FLOAT:
            value = float(value)
        if param_data[const.PARAMSET_ATTR_TYPE] in [const.PARAMSET_TYPE_INTEGER, const.PARAMSET_TYPE_ENUM]:
            if value > float(param_data[const.PARAMSET_ATTR_MAX]):
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too high" % (address, value_key))
                raise Exception
            if value < float(param_data[const.PARAMSET_ATTR_MIN]):
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too low" % (address, value_key))
                raise Exception
        if param_data[const.PARAMSET_ATTR_TYPE] == const.PARAMSET_TYPE_FLOAT:
            special = param_data.get(const.PARAMSET_ATTR_SPECIAL, [])
            valid = []
            for special_value in special:
                for _, v in special_value:
                    valid.append(v)
            if value > float(param_data[const.PARAMSET_ATTR_MAX]) and value not in valid:
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too high and not special" % (address, value_key))
                raise Exception
            if value < float(param_data[const.PARAMSET_ATTR_MIN]) and value not in valid:
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too low and not special" % (address, value_key))
                raise Exception
        self._fireEvent(self.interface_id, address, value_key, value)
        if address not in self.states:
            self.states[address] = {}
        self.states[address][value_key] = value
        return ""

    def getDeviceDescription(self, address):
        LOG.debug("RPCFunctions.getDeviceDescription: address=%s" % (address, ))
        for device in self.devices:
            if device.get(const.ATTR_ADDRESS) == address:
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
    def __init__(self, local=const.IP_LOCALHOST_V4, localport=const.PORT_RF):
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
        self._rpcfunctions._saveStates()
        LOG.info("Shutting down server")
        self.server.shutdown()
        LOG.debug("ServerThread.stop: Stopping ServerThread")
        self.server.server_close()
        LOG.info("Server stopped")
