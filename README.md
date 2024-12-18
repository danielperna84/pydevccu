# pydevccu
Virtual HomeMatic CCU XML-RPC Server with fake devices for development.

If you develop applications that communicate with a CCU (or Homegear) via XML-RPC, you can use this server instead of a real CCU. It currently provides all HomeMatic Wired and HomeMatic Wireless devices (allthough some devices with multiple similar channels with just a single channel). HomeMatic IP devices will follow.  

The main objective is to provide you access to all available devices without owning them, as well as not stressing your CCU / messing with your devices while testing your work. It should also be possible to use this for automated testing / CI.  

The `init` method used to subscribe to events is available and functional. Events will be fired when you use the `setValue` or `putParamset` methods to change parameters of a device.  

When adding the `logic` argument while creating the server-object, modules found in _device\_logic_ will be loaded depending on which devices are enabled. For example: the module [HM_Sec_SC_2.py](https://github.com/sukramj/pydevccu/blob/master/pydevccu/device_logic/HM_Sec_SC_2.py) fires two events at the specified _interval_. The `STATE` toggles with every event, and `LOWBAT` gets toggled every 5 events.  
The _startupdelay_ randomizes when the eventloop will initially start from 0 to _startupdelay_ seconds. This is to prevent multiple devices from firing their events at the same time.

## Methods
- `setValue(address, value_key, value, force=False)`
- `getValue(address, value_key)`
- `getDeviceDescription(address)`
- `getParamsetDesctiption(address, paramset_key)`
- `getParamset(address, paramset_key)` (The `mode` argument of a real CCU is not supported)
- `putParamset(address, paramset_key, paramset, force=False)` (The `rx_mode` argument of a real CCU is not supported)
- `listDevices()`
- `init(url, interface_id)`
- `getServiceMessages()` (Returns dummy-error)
- `supportedDevices()` (Proprietary, `dict` of supported devices)
- `addDevices(devices)` (Proprietary, add additional devices during runtime. `devices` is a list of device names, like when initializing the server)
- `removeDevices(devices)` (Proprietary, remove devices during runtime. `devices` is a list of device names, like when initializing the server)

For more information about the methods refer to the official [HomeMatic XML-RPC API](https://www.eq-3.de/Downloads/eq3/download%20bereich/hm_web_ui_doku/HM_XmlRpc_API.pdf) (german).

## Usage

```python
import pydevccu
# Create server that listens on 127.0.0.1:2001
# To listen on another address initialize with ("1.2.3.4", 1234) as first argument
# Add optional list of device names to only load these devices
# Enable paramset persistance (will be saved to paramset_db.json)
# Enable automated device logic (only if module for device is available), firing events at intervals of 30 seconds
s = pydevccu.Server(devices=['HM-Sec-WDS', 'HM-Sen-MDIR-WM55', 'HM-Sec-SC-2'], persistance=True, logic={"startupdelay": 5, "interval": 30})
# Start server
s.start()
# Get address for a HM-Sec-WDS device
s.supportedDevices()['HM-Sec-WDS']
# Get device description
s.getDeviceDescription('VCU0000348')
# Get VALUES paramset for channel 1
s.getParamsetDescription('VCU0000348:1', 'VALUES')
# Get current state
s.getValue('VCU0000348:1', 'STATE')
# Set state to 2
# Set force=True because parameter does not allow write operations (it's a sensor updated by hardware in real life)
s.setValue('VCU0000348:1', 'STATE', 2, force=True)
# Set state to 1 using the putParamset method
s.putParamset('VCU0000348:1', 'VALUES', {'STATE': 1}, force=True)
# Trigger PRESS_SHORT event for HM-Sen-MDIR-WM55 on channel 2
s.setValue("VCU0000274:2", "PRESS_SHORT", True)
# Add a HM-CC-RT-DN device during runtime
s.addDevices(devices=['HM-CC-RT-DN'])
# Remove the HM-Sec-SC-2
s.removeDevices(devices=['HM-Sec-SC-2'])
# Stop server
s.stop()
```

## Installation

`pip install pydevccu`