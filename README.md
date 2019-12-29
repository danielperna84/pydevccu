# pydevccu
Virtual HomeMatic CCU XML-RPC Server with fake devices for development.

If you develop applications that communicate with a CCU (or Homegear) via XML-RPC, you can use this server instead of a real CCU. It currently provides all HomeMatic Wired and HomeMatic Wireless devices (allthough some devices with multiple similar channels with just a single channel). HomeMatic IP devices will follow.  

The main objective is to provide you access to all available devices without owning them, as well as not stressing your CCU / messing with your devices while testing your work. It should also be possible to use this for automated testing / CI.  

The `init` method used to subscribe to events is available and functional. Events will be fired when you use the `setValue` or `putParamset` methods to change parameters of a device.

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

For more information about the methods refer to the official [HomeMatic XML-RPC API](https://www.eq-3.de/Downloads/eq3/download%20bereich/hm_web_ui_doku/HM_XmlRpc_API.pdf) (german).

## Usage

```python
import pydevccu
# Create server that listens on 127.0.0.1:2001
# To listen on another address initialize with ("1.2.3.4", 1234) as first argument
# Add optional list of device names to only load these devices
# Enable paramset persistance (will be saved to paramset_db.json)
s = pydevccu.Server(devices=['HM-Sec-WDS', 'HM-CC-RT-DN', 'HM-Sec-SC-2'], persistance=True)
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
# Stop server
s.stop()
```
