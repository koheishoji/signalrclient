from .Util import Util
from .HubConnection import HubConnection
from .ConnectionChecker import ConnectionChecker
from . import Protocol
from . import Transport


class HubConnectionBuilder(object):
    @staticmethod
    def help():
        helpMessage = \
"""------ example ------
import logging
from signalrclient.HubConnectionBuilder import HubConnectionBuilder

conn = HubConnectionBuilder() \\
    .withUrl("wss://hogeguga.com", options={
        "accessTokenFactory": None,            # set function returns token
        "verifySsl": True,                     #
        "skipNegotiation": False,              #
        "headers": \{\},                       # 
        "keepAliveInterval": 15,               # interval ping to server
        "serverTimeout": None                  # close if not receive message from server
    }) \\
    .configureLogging(level=logging.INFO, handler=None, socketTrace=False)
    .withProtocol(protocol=Protocol.JsonProtocol(version=1))
    .withTransport(transport=Transport.WebSocketTransport())
    .withAutomaticReconnect(interval=5, surrender=True)
    .build()"""
        print(helpMessage)

    def __init__(self):
        self.hubUrl = None
        self.options = None
        self.protocol = Protocol.JsonProtocol(version=1)
        self.transport = Transport.WebSocketTransport()
        self.reconnection = None
        self.surrender = True

    def withUrl(self, hubUrl, options = {}):
        if hubUrl is None or hubUrl.strip() == "":
            raise ValueError("hubUrl must be a valid url.")

        if options is not None:
            if type(options) is not dict:
                raise TypeError("options must be a dict {0}.".format(options))

            if "accessTokenFactory" in options.keys()\
                    and not callable(options["accessTokenFactory"]):
                raise TypeError("accessTokenFactory must be a function without params")

            if "verifySsl" in options.keys() \
                    and type(options["verifySsl"]) is not bool:
                raise TypeError("verifySsl must be a bool")
        
            if "skipNegotiation" in options.keys() \
                    and type(options["skipNegotiation"]) is not bool:
                raise TypeError("skipNegotiation must be a bool")
        
            if "headers" in options.keys() \
                    and type(options["headers"]) is not dict:
                raise TypeError("headers must be a dict {0}.".format(options["headers"]))
        
            if "keepAliveInterval" in options.keys() \
                    and type(options["keepAliveInterval"]) is not int:
                raise TypeError("keepAliveInterval must be an integer")
        
            if "serverTimeout" in options.keys() \
                    and type(options["serverTimeout"]) is not int \
                    and type(options["serverTimeout"]) is not None:
                raise TypeError("serverTimeout must be an integer or None")
        
        self.hubUrl = hubUrl
        self.options = options
        return self

    def configureLogging(self, level, handler=None, socketTrace=False):
        Util.loggingLevel = level
        Util.loggingHandler = handler
        Util.logSocketTrace = socketTrace
        return self

    def withProtocol(self, protocol):
        self.protocol = protocol
        return self
    
    def withTransport(self, transport):
        self.transport = transport
        return self

    def withAutomaticReconnect(self, interval=5, surrender=True):
        self.reconnection = interval
        self.surrender = surrender
        return self

    def build(self):
        authFunction = None
        if "accessTokenFactory" in self.options.keys():
            authFunction = self.options["accessTokenFactory"]

        verifySsl = True
        if "verifySsl" in self.options.keys():
            verifySsl = self.options["verifySsl"]

        skipNegotiation = False
        if "skipNegotiation" in self.options.keys():
            skipNegotiation = self.options["skipNegotiation"]

        headers = {}
        if "headers" in self.options.keys():
            headers = self.options["headers"]

        keepAliveInterval = 15
        if "keepAliveInterval" in self.options.keys():
            keepAliveInterval = self.options["keepAliveInterval"]
        
        serverTimeout = None
        if "serverTimeout" in self.options.keys():
            serverTimeout = self.options["serverTimeout"]

        connectionChecker = ConnectionChecker(keepAliveInterval, serverTimeout)

        return HubConnection(
            url=self.hubUrl,
            protocol=self.protocol,
            transport=self.transport,
            connectionChecker=connectionChecker,
            reconnection=self.reconnection,
            surrender=self.surrender,
            authFunction=authFunction,
            verifySsl=verifySsl,
            skipNegotiation=skipNegotiation,
            headers=headers
        )
