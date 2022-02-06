from ptouch_py.domain import DevInfo

SUPPORTED_DEVICES = [
    DevInfo("PT-P700", 0x04f9, 0x2061, packbits=True, p700_init=True),
    DevInfo("PT-P700 (PLite Mode)", 0x04f9, 0x2064, is_plite=True),
    DevInfo("PT-P750W", 0x04f9, 0x2062, packbits=True, p700_init=True),
    DevInfo("PT-P750W (PLite Mode)", 0x04f9, 0x2065, is_plite=True),
]