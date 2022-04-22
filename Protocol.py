import json

from .Util import Util


class Protocol(object):
    def __init__(self, name, version):
        self.logger = Util.configLogger(__name__)
        self.name = name
        self.version = version
        self.separator = chr(0x1E)

    def encode(self, message):
        return None

    def decode(self, message):
        return None

class JsonProtocol(Protocol):
    def __init__(self, version):
        super().__init__("json", version)

    def encode(self, message):
        encoded = json.dumps(message) + self.separator
        return encoded

    def decode(self, raw):
        messages = [ x for x in raw.split(self.separator) if x != "" ]
        decoded = [ json.loads(x) for x in messages ]
        return decoded

class MessagePackProtocol(Protocol):
    def __init__(self, version):
        super().__init__("messagepack", version)
        raise NotImplementedError("MessagePackProtocol is not implemented")

    def encode(self, message):
        return None

    def decode(self, message):
        return None
