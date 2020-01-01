# -*- coding: utf-8 -*-
"""
Convert XML-files for HomeMaticIP and HomeMaticIP Wired to JSON files.
Extract /opt/HMServer/HMIPServer.jar (zip).
Relevant folders:
- de/eq3/cbcs/devicedescription/channelspecification/ (Channel definitions)
- de/eq3/cbcs/devicedescription/devicespecification/eQ-3/ (Device descriptions)
"""
import os
import re
import sys
import copy
import json
import pprint
import xml.etree.ElementTree as ET

START_ID = 1
VCU = "VCU0000000"

PATH_XML_DEVICESPECIFICATION = 'hmip_xml/devicespecification/eQ-3'
PATH_XML_CHANNELSPECIFICATION = 'hmip_xml/channelspecification'
PATH_JSON_DEVICE_DESCRIPTIONS = 'device_descriptions_ip'
PATH_JSON_PARAMSET_DESCRIPTIONS = 'paramset_descriptions_ip'

DEV_FLAG_VISIBLE = 1
DEV_FLAG_INTERNAL = 2
DEV_FLAG_DONTDELETE = 8
DEV_FLAG_VISIBLE_STR = 'visible'
DEV_FLAG_INVISIBLE_STR = 'invisible'
DEV_FLAG_INTERNAL_STR = 'internal'
DEV_FLAG_DONTDELETE_STR = 'dontdelete' # ?

DEV_RX_MODE_ALWAYS = 1
DEV_RX_MODE_BURST = 2
DEV_RX_MODE_CONFIG = 4
DEV_RX_MODE_WAKEUP = 8
DEV_RX_MODE_LAZY_CONFIG = 10
DEV_RX_MODE_ALWAYS_STR = 'ALWAYS'
DEV_RX_MODE_BURST_STR = 'BURST'
DEV_RX_MODE_CONFIG_STR = 'CONFIG'
DEV_RX_MODE_WAKEUP_STR = 'WAKEUP'
DEV_RX_MODE_LAZY_CONFIG_STR = 'LAZY_CONFIG'

CHAN_DIRECTION_NONE = 0
CHAN_DIRECTION_SENDER = 1
CHAN_DIRECTION_RECEIVER = 2
FRAME_DIRECTION_TO_DEVICE_XML = 'to_device'
FRAME_DIRECTION_FROM_DEVICE_XML = 'from_device'

PARAM_FLAG_INVISIBLE = 0
PARAM_FLAG_VISIBLE = 1
PARAM_FLAG_INTERNAL = 2
PARAM_FLAG_TRANSFORM = 4
PARAM_FLAG_SERVICE = 8
PARAM_FLAG_STICKY = 10
PARAM_FLAG_INVISIBLE_STR = 'invisible'
PARAM_FLAG_VISIBLE_STR = 'visible'
PARAM_FLAG_INTERNAL_STR = 'internal'
PARAM_FLAG_TRANSFORM_STR = 'transform'
PARAM_FLAG_SERVICE_STR = 'service'
PARAM_FLAG_STICKY_STR = 'sticky'

PARAM_OPERATION_READ = 1
PARAM_OPERATION_READ_XML = 'read'
PARAM_OPERATION_WRITE = 2
PARAM_OPERATION_WRITE_XML = 'write'
PARAM_OPERATION_EVENT = 4
PARAM_OPERATION_EVENT_XML = 'event'

VAL_TRUE = 'true'
VAL_FALSE = 'false'

TAG_MAP = {
    'link': 'LINK',
    'configuration': 'MASTER',
    'state': 'VALUES'
}

DEV_DESC_DEV = {
    "UPDATABLE": 0,
    "TYPE": "",
    "CHILDREN": [],
    "FIRMWARE": "",
    "PARAMSETS": [],
    "ROAMING": 0,
    "PARENT": "",
    "FLAGS": 1,
    "INTERFACE": "",
    "RX_MODE": 0,
    "ADDRESS": "",
    "RF_ADDRESS": 0,
    "VERSION": 0,
}

DEV_DESC_CHAN = {
    "TYPE": "",
    "PARENT_TYPE": "",
    "PARAMSETS": [],
    "LINK_TARGET_ROLES": "",
    "PARENT": "",
    "FLAGS": 1,
    "AES_ACTIVE": 0,
    "DIRECTION": 0,
    "INDEX": 0,
    "VERSION": 0,
    "LINK_SOURCE_ROLES": "",
    "ADDRESS": ""
}

PARAMSET_DESC = {
    "TYPE": "",
    "OPERATIONS": 0,
    "FLAGS": 1,
    "DEFAULT": 0,
    "MAX": 0,
    "MIN": 0,
    "UNIT": "",
    "TAB_ORDER": 0,
}

PVAL_XML_FALSE = 'false'
PVAL_PD_FALSE = 0
PVAL_XML_TRUE = 'true'
PVAL_PD_TRUE = 1

PARAMTYPE_MAP = {
    'boolean': 'BOOL',
    'integer': 'INTEGER',
    'float': 'FLOAT',
    'option': 'ENUM',
    'action': 'ACTION',
    'string': 'STRING'
}

INT_MAX = 2147483647
INT_MIN = -2147483648

if not os.path.exists(PATH_JSON_DEVICE_DESCRIPTIONS):
    os.makedirs(PATH_JSON_DEVICE_DESCRIPTIONS)
if not os.path.exists(PATH_JSON_PARAMSET_DESCRIPTIONS):
    os.makedirs(PATH_JSON_PARAMSET_DESCRIPTIONS)

# Clear old data
for filename in os.listdir(PATH_JSON_DEVICE_DESCRIPTIONS):
    os.unlink(os.path.join(PATH_JSON_DEVICE_DESCRIPTIONS, filename))
for filename in os.listdir(PATH_JSON_PARAMSET_DESCRIPTIONS):
    os.unlink(os.path.join(PATH_JSON_PARAMSET_DESCRIPTIONS, filename))
nextid = len(os.listdir(PATH_JSON_DEVICE_DESCRIPTIONS)) + START_ID

def get_rx_mode(node, default_rx=0):
    rx = default_rx
    modes = node.get("rx_modes").split(',')
    if DEV_RX_MODE_ALWAYS_STR in modes:
        rx = rx | DEV_RX_MODE_ALWAYS
    if DEV_RX_MODE_BURST_STR in modes:
        rx = rx | DEV_RX_MODE_BURST
    if DEV_RX_MODE_CONFIG_STR in modes:
        rx = rx | DEV_RX_MODE_CONFIG
    if DEV_RX_MODE_WAKEUP_STR in modes:
        rx = rx | DEV_RX_MODE_WAKEUP
    if DEV_RX_MODE_LAZY_CONFIG_STR in modes:
        rx = rx | DEV_RX_MODE_LAZY_CONFIG
    return rx

CHANNEL_SPECIFICATIONS = {}

# Parse channel specifications
files = os.listdir(PATH_XML_CHANNELSPECIFICATION)
files = ['channel_type_switch_transmitter.xml', 'channel_type_switch_virtual_receiver_2.xml']
for filename in files:
    if filename == '.gitkeep':
        continue
    f = os.path.join(PATH_XML_CHANNELSPECIFICATION, filename)
    tree = ET.parse(f)
    root = tree.getroot()
    channeltype = root.get('type')
    version = int(root.get('typeversion'))
    if CHANNEL_SPECIFICATIONS.get(channeltype) is None:
        CHANNEL_SPECIFICATIONS[channeltype] = {}
    CHANNEL_SPECIFICATIONS[channeltype][version] = {}
    for paramset in root.getchildren():
        print(paramset.tag)
        paramset_type = TAG_MAP[paramset.tag]
        CHANNEL_SPECIFICATIONS[channeltype][version][paramset_type] = {}
        for parameter in paramset.findall('parameter'):
            CHANNEL_SPECIFICATIONS[channeltype][version][paramset_type][parameter.text] = {}
            if paramset.tag == 'link':
                for role in paramset.findall('type'):
                    CHANNEL_SPECIFICATIONS[channeltype][version][paramset_type][parameter.text][role.text] = {}

print(CHANNEL_SPECIFICATIONS)
sys.exit(0)
# Parse device specifications
files = os.listdir(PATH_XML_DEVICESPECIFICATION)
files = ['device_psm.xml']
for filename in files:
    if filename == '.gitkeep':
        continue
    f = os.path.join(PATH_XML_DEVICESPECIFICATION, filename)
    tree = ET.parse(f)
    root = tree.getroot()
    parent_map = dict((c, p) for p in tree.getiterator() for c in p)
    nicename = root.get('description')
    supported_types = root.find("devTypes")
    channels = root.find("channels")
    if channels is None:
        continue
    paramset_defs = {}
    for devtype in supported_types.findall('devType'):
        devname = devtype.get('label')
        if devname == 'CENTRAL':
            continue
        if '/' in devname:
            print("Skipping: %s (%s)", (devname, filename))
            continue
        dev_desc = []
        paramsets = {}
        d_dict = copy.deepcopy(DEV_DESC_DEV)
        d_dict["TYPE"] = devname
        address = "VCU" + format(nextid, '07d')
        d_dict["ADDRESS"] = address
        d_dict["INTERFACE"] = VCU
        
        if root.get("version") is not None:
            d_dict["VERSION"] = int(root.get("version"))
        if root.get("updatable") == VAL_TRUE:
            d_dict["UPDATABLE"] = 1
        dev_desc.append(d_dict)
        for channel in channels:
            index = int(channel.get("index"))
            count = 1
            for i in range(count):
                c_direction = CHAN_DIRECTION_NONE
                direction = CHAN_DIRECTION_NONE
                s_dict = copy.deepcopy(DEV_DESC_CHAN)
                s_dict["TYPE"] = channel.get("type")
                #print(s_dict["TYPE"])
                s_dict["PARENT"] = address
                s_dict["PARENT_TYPE"] = devname
                s_dict["INDEX"] = index + i
                s_dict["ADDRESS"] = "%s:%i" % (address, index + i)
                dev_desc[0]["CHILDREN"].append(s_dict["ADDRESS"])
                paramsets[s_dict["ADDRESS"]] = {}
                for ptype in CHANNEL_SPECIFICATIONS[s_dict["TYPE"]][version].keys():
                    if CHANNEL_SPECIFICATIONS[s_dict["TYPE"]][version][ptype]:
                        s_dict['PARAMSETS'].append(ptype)
                dev_desc.append(s_dict)

        pprint.pprint(dev_desc)

