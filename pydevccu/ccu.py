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

def initParamsets():
    with open(const.PARAMSETS_DB, 'w') as fptr:
        fptr.write("{}")

# Object holding the methods the XML-RPC server should provide.
class RPCFunctions():
    def __init__(self, devices):
        LOG.debug("RPCFunctions.__init__")
        self.remotes = {}
        try:
            self.knownDevices = []
            self.interface_id = "pydevccu"
            self.devices = []
            self.paramset_descriptions = {}
            self.supported_devices = {}
            self.paramsets = {}
            self.active_devices = devices
            if self.active_devices is not None:
                LOG.info("RPCFunctions.__init__: Limiting to devices: %s", self.active_devices)
            script_dir = os.path.dirname(__file__)
            dd_rel_path = const.DEVICE_DESCRIPTIONS
            dd_path = os.path.join(script_dir, dd_rel_path)
            for filename in os.listdir(dd_path):
                if self.active_devices is not None:
                    devname = filename.split('.')[0].replace('_', ' ')
                    if devname not in self.active_devices:
                        continue
                with open(os.path.join(dd_path, filename)) as fptr:
                    self.devices.extend(json.load(fptr))
            pd_rel_path = const.PARAMSET_DESCRIPTIONS
            pd_path = os.path.join(script_dir, pd_rel_path)
            for filename in os.listdir(pd_path):
                if self.active_devices is not None:
                    devname = filename.split('.')[0].replace('_', ' ')
                    if devname not in self.active_devices:
                        continue
                with open(os.path.join(pd_path, filename)) as fptr:
                    pd = json.load(fptr)
                    for k, v in pd.items():
                        self.paramset_descriptions[k] = v
            if not os.path.exists(const.PARAMSETS_DB):
                initParamsets()
            self._loadParamsets()
            for device in self.devices:
                if not ':' in device.get(const.ATTR_ADDRESS):
                    self.supported_devices[device.get(const.ATTR_TYPE)] = device.get(const.ATTR_ADDRESS)
        except Exception as err:
            LOG.debug("RPCFunctions.__init__: Exception: %s", err)
            self.devices = []

    def _loadParamsets(self):
        with open(const.PARAMSETS_DB) as fptr:
            self.paramsets = json.load(fptr)

    def _saveParamsets(self):
        LOG.debug("Saving paramsets")
        with open(const.PARAMSETS_DB, 'w') as fptr:
            json.dump(self.paramsets, fptr)

    def _askDevices(self, interface_id):
        self.knownDevices = self.remotes[interface_id].listDevices(interface_id)
        LOG.debug("RPCFunctions._askDevices: %s", self.knownDevices)
        t = threading.Thread(name='_pushDevices',
                             target=self._pushDevices,
                             args=(interface_id, ))
        t.start()

    def _pushDevices(self, interface_id):
        newDevices = []
        deleteDevices = []
        knownDeviceAddresses = []
        for device in self.knownDevices:
            if device[const.ATTR_ADDRESS] not in self.paramset_descriptions.keys():
                deleteDevices.append(device)
            else:
                knownDeviceAddresses.append(device[const.ATTR_ADDRESS])
        for device in self.devices:
            if device[const.ATTR_ADDRESS] not in knownDeviceAddresses:
                newDevices.append(device)
        self.remotes[interface_id].newDevices(interface_id, newDevices)
        self.remotes[interface_id].deleteDevices(interface_id, deleteDevices)
        LOG.debug("RPCFunctions._pushDevices: pushed")

    def _fireEvent(self, interface_id, address, value_key, value):
        LOG.debug("RPCFunctions._fireEvent: %s, %s, %s, %s", interface_id, address, value_key, value)
        for interface_id, proxy in self.remotes.items():
            proxy.event(interface_id, address, value_key, value)

    def listDevices(self, interface_id=None):
        LOG.debug("RPCFunctions.listDevices: interface_id = %s", interface_id)
        return self.devices

    def getServiceMessages(self):
        LOG.debug("RPCFunctions.getServiceMessages")
        return [['VCU0000001:1', const.ATTR_ERROR, 7]]

    def getValue(self, address, value_key):
        LOG.debug("RPCFunctions.getValue: address=%s, value_key=%s", address, value_key)
        return self.getParamset(address, const.PARAMSET_ATTR_VALUES).get(value_key)

    def setValue(self, address, value_key, value, force=False):
        LOG.debug("RPCFunctions.setValue: address=%s, value_key=%s, value=%s, force=%s", address, value_key, value, force)
        paramset = {value_key: value}
        self.putParamset(address, const.PARAMSET_ATTR_VALUES, paramset, force=force)
        return ""

    def putParamset(self, address, paramset_key, paramset, force=False, rx_mode=None):
        LOG.debug("RPCFunctions.putParamset: address=%s, paramset_key=%s, paramset=%s, force=%s", address, paramset_key, paramset, force)
        paramsets = self.paramset_descriptions[address]
        paramset_values = paramsets[paramset_key]
        for value_key, value in paramset.items():
            param_data = paramset_values[value_key]
            param_type = param_data[const.ATTR_TYPE]
            if not const.PARAMSET_OPERATIONS_WRITE & param_data[const.PARAMSET_ATTR_OPERATIONS] and not force:
                LOG.warning(
                    "RPCFunctions.putParamset: address=%s, value_key=%s: write operation not allowed", address, value_key)
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
                    LOG.warning("RPCFunctions.putParamset: address=%s, value_key=%s: value too high", address, value_key)
                    raise Exception
                if value < float(param_data[const.PARAMSET_ATTR_MIN]):
                    LOG.warning("RPCFunctions.putParamset: address=%s, value_key=%s: value too low", address, value_key)
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
            if address not in self.paramsets:
                self.paramsets[address] = {}
            if paramset_key not in self.paramsets[address]:
                self.paramsets[address][paramset_key] = {}
            self.paramsets[address][paramset_key][value_key] = value
            self._fireEvent(self.interface_id, address, value_key, value)

    def getDeviceDescription(self, address):
        LOG.debug("RPCFunctions.getDeviceDescription: address=%s", address)
        for device in self.devices:
            if device.get(const.ATTR_ADDRESS) == address:
                return device
        raise Exception

    def getParamsetDescription(self, address, paramset_type):
        LOG.debug("RPCFunctions.getParamsetDescription: address=%s, paramset_type=%s", address, paramset_type)
        return self.paramset_descriptions[address][paramset_type]

    def getParamset(self, address, paramset_key, mode=None):
        LOG.debug("RPCFunctions.getParamset: address=%s, paramset_key=%s", address, paramset_key)
        if mode is not None:
            LOG.debug("RPCFunctions.getParamset: mode argument not supported")
            raise Exception
        if paramset_key not in [const.PARAMSET_ATTR_MASTER, const.PARAMSET_ATTR_VALUES]:
            raise Exception
        data = {}
        pd = self.paramset_descriptions[address][paramset_key]
        for parameter in pd.keys():
            if pd[parameter][const.ATTR_FLAGS] & const.PARAMSET_FLAG_INTERNAL:
                continue
            try:
                data[parameter] = self.paramsets[address][paramset_key][parameter]
            except:
                data[parameter] = self.paramset_descriptions[address][paramset_key][parameter][const.PARAMSET_ATTR_DEFAULT]
        return data

    def init(self, url, interface_id=None):
        LOG.debug("RPCFunctions.init: url=%s, interface_id=%s", url, interface_id)
        if interface_id is not None:
            try:
                self.remotes[interface_id] = LockingServerProxy(url)
                t = threading.Thread(name='_askDevices',
                                     target=self._askDevices,
                                     args=(interface_id, ))
                t.start()
            except Exception as err:
                LOG.debug("RPCFunctions.init:Exception: %s", err)
        else:
            deletedremote = None
            for remote in self.remotes:
                if self.remotes[remote]._ServerProxy__host in url:
                    deletedremote = remote
                    break
            if deletedremote is not None:
                del self.remotes[deletedremote]
        return ""

class RequestHandler(SimpleXMLRPCRequestHandler):
    """We handle requests to / and /RPC2"""
    rpc_paths = ('/', '/RPC2',)

class ServerThread(threading.Thread):
    """XML-RPC server thread to handle messages from CCU / Homegear"""
    def __init__(self, addr=(const.IP_LOCALHOST_V4, const.PORT_RF), devices=None):
        LOG.debug("ServerThread.__init__")
        threading.Thread.__init__(self)
        self.addr = addr
        LOG.debug("__init__: Registering RPC methods")
        self._rpcfunctions = RPCFunctions(devices)
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
        self._rpcfunctions._saveParamsets()
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

    def getParamset(self, address, paramset):
        return self._rpcfunctions.getParamset(address, paramset)

    def putParamset(self, address, paramset_key, paramset, force=False, rx_mode=None):
        return self._rpcfunctions.putParamset(address, paramset_key, paramset, force, rx_mode)

    def listDevices(self):
        return self._rpcfunctions.listDevices()

    def getServiceMessages(self):
        return self._rpcfunctions.getServiceMessages()

    def supportedDevices(self):
        return self._rpcfunctions.supported_devices
