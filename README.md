# pydevccu
Virtual HomeMatic CCU XML-RPC Server with fake devices for development.

If you develop applications that communicate with a CCU (or Homegear) via XML-RPC, you can use this server instead of a real CCU. It currently provides all HomeMatic Wired and HomeMatic Wireless devices (allthough some devices with multiple similar channels with just a single channel). HomeMatic IP devices will follow.  

The main objective is to provide you access to all available devices without owning them, as well as not stressing your CCU / messing with your devices while testing your work. It should also be possible to use this for automated testing / CI.
