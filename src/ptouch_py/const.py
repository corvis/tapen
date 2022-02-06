PTOUCH_ENDPOINT = 0x02
PTOUCH_INPUT_ENDPOINT = 0x81
PTOUCH_STATUS_REPLY_SIZE = 32


CMD_INIT = b"\x1b\x40"
CMD_STATUS_INFO = b"\x1b\x69\x53"
CMD_ENABLE_PACKBITS = b"\x4d\x02"
CMD_DISABLE_PACKBITS = b"\x4d\x00"
CMD_RASTER_START = b"\x1b\x69\x52\x01"
CMD_RASTER_START_P700 = b"\x1b\x69\x61\x01"
CMD_EJECT = b"\x1a"  # print and cut tape
CMD_ADVANCE = b"\x0c"  # print and advance tape, but do not cut