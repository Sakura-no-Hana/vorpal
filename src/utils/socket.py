import json

import zlib


class Decoder:
    def __init__(self):
        self.buffer = bytearray()
        self.zlib = zlib.decompressobj()

    def decode(self, msg):
        if type(msg) is bytes:
            self.buffer.extend(msg)

            if len(msg) >= 4:
                if msg[-4:] == b"\x00\x00\xff\xff":
                    msg = self.zlib.decompress(self.buffer)
                    msg = msg.decode("utf-8")
                    self.buffer = bytearray()
                else:
                    return dict()
            else:
                return dict()

        return json.loads(msg)
