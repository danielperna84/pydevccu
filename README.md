# pydevccu
Virtual HomeMatic CCU XML-RPC Server with fake devices for development.

If you develop applications that communicate with a CCU (or Homegear) via XML-RPC, you can use this server instead of a real CCU. It currently provides all HomeMatic Wired and HomeMatic Wireless devices (allthough some devices with multiple similar channels with just a single channel). HomeMatic IP devices will follow.  

The main objective is to provide you access to all available devices without owning them, as well as not stressing your CCU / messing with your devices while testing your work. It should also be possible to use this for automated testing / CI.

## Methods
- `setValue(address, value_key, value, force=False)`
- `getValue(address, value_key)`
- `getDeviceDescription(address)`
- `getParamsetDesctiption(address, paramset)`
- `listDevices()`
- `getServiceMessages()` (Returns dummy-error)

## Usage

```python
import pydevccu
# Create server that listens on 127.0.0.1:2001
# To listen on another address initialize with ("1.2.3.4", 1234) as first argument
s = pydevccu.Server()
# Start server
s.start()
# Get device description for a HM-Sec-WDS
s.getDeviceDescription("VCU0000348")
# Get current state
s.getValue('VCU0000348:1', "STATE")
# Set state to 2
# Set force=True because parameter does not allow write operations (it's a sensor updated by hardware in real life)
s.setValue('VCU0000348:1', "STATE", 2, force=True)
# Stop server
s.stop()
```
