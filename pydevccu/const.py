"""
Constants used in pydevccu
"""

VERSION = '0.1.8'

IP_LOCALHOST_V4 = '127.0.0.1'
IP_LOCALHOST_V6 = '::1'
IP_ANY_V4 = '0.0.0.0'
IP_ANY_V6 = '::'
PORT_ANY = 0

PORT_WIRED = 2000
PORT_WIRED_TLS = 42000
PORT_RF = 2001
PORT_RF_TLS = 42001
PORT_IP = 2010
PORT_IP_TLS = 42010
PORT_GROUPS = 9292
PORT_GROUPS_TLS = 49292

DEVICE_DESCRIPTIONS = "device_descriptions"
PARAMSET_DESCRIPTIONS = "paramset_descriptions"
PARAMSETS_DB = "paramsets_db.json"

ATTR_ADDRESS = 'ADDRESS'
ATTR_CHILDREN = 'CHILDREN'
ATTR_NAME = 'NAME'
ATTR_TYPE = 'TYPE'
ATTR_PARENT_TYPE = 'PARENT_TYPE'
ATTR_FLAGS = 'FLAGS'
ATTR_ERROR = 'ERROR'
ATTR_PARENT = 'PARENT'
ATTR_PARENT_TYPE = 'PARENT_TYPE'

PARAMSET_ATTR_MASTER = 'MASTER'
PARAMSET_ATTR_VALUES = 'VALUES'
PARAMSET_ATTR_LINK = 'LINK'
PARAMSET_ATTR_MIN = 'MIN'
PARAMSET_ATTR_MAX = 'MAX'
PARAMSET_ATTR_OPERATIONS = 'OPERATIONS'
PARAMSET_ATTR_DEFAULT = 'DEFAULT'
PARAMSET_ATTR_VALUE_LIST = 'VALUE_LIST'
PARAMSET_ATTR_SPECIAL = 'SPECIAL'
PARAMSET_ATTR_UNIT = 'UNIT'
PARAMSET_ATTR_CONTROL = 'CONTROL'

PARAMSET_TYPE_FLOAT = 'FLOAT'
PARAMSET_TYPE_INTEGER = 'INTEGER'
PARAMSET_TYPE_BOOL = 'BOOL'
PARAMSET_TYPE_ENUM = 'ENUM'
PARAMSET_TYPE_STRING = 'STRING'
PARAMSET_TYPE_ACTION = 'ACTION'

PARAMSET_OPERATIONS_READ = 1
PARAMSET_OPERATIONS_WRITE = 2
PARAMSET_OPERATIONS_EVENT = 4

PARAMSET_FLAG_INVISIBLE = 0
PARAMSET_FLAG_VISIBLE = 1
PARAMSET_FLAG_INTERNAL = 2
PARAMSET_FLAG_TRANSFORM = 4
PARAMSET_FLAG_SERVICE = 8
PARAMSET_FLAG_STICKY = 10
