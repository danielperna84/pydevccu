# pylint: disable=line-too-long,too-many-branches,missing-function-docstring,missing-module-docstring,missing-class-docstring,invalid-name,broad-except,bare-except,protected-access
import os
import sys
import logging
import threading
import json
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from . import const
from .proxy import LockingServerProxy

LOG = logging.getLogger(__name__)
if sys.stdout.isatty():
    logging.basicConfig(level=logging.DEBUG)
    LOG.addHandler(logging.StreamHandler(sys.stdout))

def initStates():
    with open(const.STATES_DB, 'w') as fptr:
        fptr.write("{}")

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
            self.supported_devices = {}
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
                initStates()
            self._loadStates()
            for device in self.devices:
                if not ':' in device.get(const.ATTR_ADDRESS):
                    self.supported_devices[device.get(const.ATTR_TYPE)] = device.get(const.ATTR_ADDRESS)
        except Exception as err:
            LOG.debug("RPCFunctions.__init__: Exception: %s", err)
            self.devices = []

    def _loadStates(self):
        with open(const.STATES_DB) as fptr:
            self.states = json.load(fptr)

    def _saveStates(self):
        LOG.debug("Saving states")
        with open(const.STATES_DB, 'w') as fptr:
            json.dump(self.states, fptr)

    def _askDevices(self, interface_id):
        self.knownDevices = self.remotes[interface_id].listDevices(interface_id)
        LOG.debug("RPCFunctions._askDevices: %s", self.knownDevices)
        t = threading.Thread(name='_pushDevices',
                             target=self._pushDevices,
                             args=(interface_id, ))
        t.start()

    def _pushDevices(self, interface_id):
        #newDevices = [d for d in self.devices if d[const.ATTR_ADDRESS] not in self.paramset_descriptions.keys()]
        #self.remotes[interface_id].newDevices(interface_id, newDevices)
        self.remotes[interface_id].newDevices(interface_id, self.devices)
        LOG.debug("RPCFunctions._pushDevices: pushed")
        self.knownDevices = []

    def _fireEvent(self, interface_id, address, value_key, value):
        LOG.debug("RPCFunctions._fireEvent: %s, %s, %s, %s", interface_id, address, value_key, value)

    def listDevices(self, interface_id=None):
        LOG.debug("RPCFunctions.listDevices: interface_id = %s", interface_id)
        return self.devices

    def getServiceMessages(self):
        LOG.debug("RPCFunctions.getServiceMessages")
        return [['VCU0000001:1', 'ERROR', 7]]

    def getValue(self, address, value_key):
        LOG.debug("RPCFunctions.getValue: address=%s, value_key=%s", address, value_key)
        try:
            return self.states[address][value_key]
        except:
            return self.paramset_descriptions[address][const.ATTR_VALUES][value_key][const.PARAMSET_ATTR_DEFAULT]

    def setValue(self, address, value_key, value, force=False):
        LOG.debug("RPCFunctions.setValue: address=%s, value_key=%s, value=%s", address, value_key, value)
        paramsets = self.paramset_descriptions[address]
        paramset_values = paramsets[const.ATTR_VALUES]
        param_data = paramset_values[value_key]
        param_type = param_data[const.PARAMSET_ATTR_TYPE]
        if not const.PARAMSET_OPERATIONS_WRITE & param_data[const.PARAMSET_ATTR_OPERATIONS] and not force:
            LOG.warning(
                "RPCFunctions.setValue: address=%s, value_key=%s: write operation not allowed", address, value_key)
            raise Exception
        if param_type == const.PARAMSET_TYPE_ACTION:
            self._fireEvent(self.interface_id, address, value_key, True)
            return ""
        if param_type == const.PARAMSET_TYPE_BOOL:
            value = bool(value)
        if param_type == const.PARAMSET_TYPE_STRING:
            value = str(value)
        if param_type in [const.PARAMSET_TYPE_INTEGER, const.PARAMSET_TYPE_ENUM]:
            value = int(float(value))
        if param_type == const.PARAMSET_TYPE_FLOAT:
            value = float(value)
        if param_type == const.PARAMSET_TYPE_ENUM:
            if value > float(param_data[const.PARAMSET_ATTR_MAX]):
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too high", address, value_key)
                raise Exception
            if value < float(param_data[const.PARAMSET_ATTR_MIN]):
                LOG.warning("RPCFunctions.setValue: address=%s, value_key=%s: value too low", address, value_key)
                raise Exception
        if param_type in [const.PARAMSET_TYPE_FLOAT, const.PARAMSET_TYPE_INTEGER]:
            special = param_data.get(const.PARAMSET_ATTR_SPECIAL, [])
            valid = []
            for special_value in special:
                for _, v in special_value:
                    valid.append(v)
            value = float(value)
            if param_type == const.PARAMSET_TYPE_INTEGER:
                value = int(value)
            if value not in valid:
                max_val = float(param_data[const.PARAMSET_ATTR_MAX])
                min_val = float(param_data[const.PARAMSET_ATTR_MIN])
                if param_type == const.PARAMSET_TYPE_INTEGER:
                    max_val = int(max_val)
                    min_val = int(min_val)
                if value > max_val:
                    value = max_val
                if value < min_val:
                    value = min_val
        self._fireEvent(self.interface_id, address, value_key, value)
        if address not in self.states:
            self.states[address] = {}
        self.states[address][value_key] = value
        return ""

    def getDeviceDescription(self, address):
        LOG.debug("RPCFunctions.getDeviceDescription: address=%s", address)
        for device in self.devices:
            if device.get(const.ATTR_ADDRESS) == address:
                return device
        raise Exception

    def getParamsetDescription(self, address, paramset):
        LOG.debug("RPCFunctions.getParamsetDescription: address=%s, paramset=%s", address, paramset)
        return self.paramset_descriptions[address][paramset]

    def init(self, url, interface_id=None):
        LOG.debug("RPCFunctions.init: url=%s, interface_id=%s", url, interface_id)
        if interface_id:
            try:
                self.remotes[interface_id] = LockingServerProxy(url)
                t = threading.Thread(name='_askDevices',
                                     target=self._askDevices,
                                     args=(interface_id, ))
                t.start()
            except Exception as err:
                LOG.debug("RPCFunctions.init:Exception: %s", err)
        return ""

class RequestHandler(SimpleXMLRPCRequestHandler):
    """We handle requests to / and /RPC2"""
    rpc_paths = ('/', '/RPC2',)

class ServerThread(threading.Thread):
    """XML-RPC server thread to handle messages from CCU / Homegear"""
    def __init__(self, addr=(const.IP_LOCALHOST_V4, const.PORT_RF)):
        LOG.debug("ServerThread.__init__")
        threading.Thread.__init__(self)
        self.addr = addr
        LOG.debug("__init__: Registering RPC methods")
        self._rpcfunctions = RPCFunctions()
        LOG.debug("ServerThread.__init__: Setting up server")
        self.server = SimpleXMLRPCServer(addr, requestHandler=RequestHandler, logRequests=False, allow_none=True)
        self.server.register_introspection_functions()
        self.server.register_multicall_functions()
        LOG.debug("ServerThread.__init__: Registering RPC functions")
        self.server.register_instance(
            self._rpcfunctions, allow_dotted_names=True)

    def run(self):
        LOG.info("Starting server at http://%s:%i", self.addr[0], self.addr[1])
        self.server.serve_forever()

    def stop(self):
        """Shut down our XML-RPC server."""
        self._rpcfunctions._saveStates()
        LOG.info("Shutting down server")
        self.server.shutdown()
        LOG.debug("ServerThread.stop: Stopping ServerThread")
        self.server.server_close()
        LOG.info("Server stopped")

    # Convenience methods at server scope
    def setValue(self, address, value_key, value, force=False):
        return self._rpcfunctions.setValue(address, value_key, value, force)

    def getValue(self, address, value_key):
        return self._rpcfunctions.getValue(address, value_key)

    def getDeviceDescription(self, address):
        return self._rpcfunctions.getDeviceDescription(address)

    def getParamsetDescription(self, address, paramset):
        return self._rpcfunctions.getParamsetDescription(address, paramset)

    def listDevices(self):
        return self._rpcfunctions.listDevices()

    def getServiceMessages(self):
        return self._rpcfunctions.getServiceMessages()

    def supportedDevices(self):
        return self._rpcfunctions.supported_devices
