import websocket
import ssl

from .Util import Util
from .Error import *


class Transport(object):

    def __init__(self, name):
        self.logger = Util.configLogger(name)
    
    def initialize(self, url, header, onOpen, onMessage, onError, onClose):
        self.logger.error("must override this method")

    def run(self, verifySsl):
        self.logger.error("must override this method")

    def stop(self):
        self.logger.error("must override this method")

    def send(self, encoded):
        self.logger.error("must override this method")

class WebSocketTransport(Transport):
    def __init__(self):
        super().__init__(__name__)
        self.webSocket = None
        websocket.enableTrace(Util.logSocketTrace)
        self.opcode = 0x1 # 0x2 for binary

    def initialize(self, url, header, onOpen, onMessage, onError, onClose):
        self.webSocket = websocket.WebSocketApp(
            url,
            header=header,
            on_open=onOpen,
            on_message=onMessage,
            on_error=onError,
            on_close=onClose
        )

    def run(self, verifySsl):
        self.webSocket.run_forever(
            sslopt={"cert_reqs": ssl.CERT_NONE} if not verifySsl else {}
        )

    def stop(self):
        self.webSocket.close()

    def send(self, encoded):
        self.webSocket.send(encoded, self.opcode)

    def onError(self, err):
        if type(err) is websocket._exceptions.WebSocketConnectionClosedException:
            self.logger.info("websocket connection closed : {0}".format(err))

        elif isinstance(err, ConnectionError):
            self.logger.info("websocket connection error : {0}".format(err))

        elif type(err) is websocket._exceptions.WebSocketBadStatusException \
                and "Handshake status 401 Unauthorized" in str(err):
            raise UnauthorizedError("websocket unauthorized error") from err

        else:
            raise WebSocketError("Unknown error") from err

class ServerSentEventsTransport(Transport):
    def __init__(self):
        super().__init__(__name__)
        raise NotImplementedError("ServerSentEventsTransport is not implemented")

class LongPollingTransport(Transport):
    def __init__(self):
        super().__init__(__name__)
        raise NotImplementedError("LongPollingTransport is not implemented")
