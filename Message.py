from enum import IntEnum


class MessageType(IntEnum):
    invocation = 1
    streamItem = 2
    completion = 3
    streamInvocation = 4
    cancelInvocation = 5
    ping = 6
    close = 7


class Message(object):
    @staticmethod
    def createHandshakeRequest(protocol, version):
        return {
            "protocol": protocol,
            "version": version
        }
    
    @staticmethod
    def createPing():
        return {
            "type": MessageType.ping
        }
    
    @staticmethod
    def createInvocation(invocationId, target, arguments, headers):
        return {
            "type": MessageType.invocation,
            "invocationId": invocationId,
            "target": target,
            "arguments": arguments
        }

    @staticmethod
    def createInvocationNonBlocking(target, arguments, headers):
        return {
            "type": MessageType.invocation,
            "target": target,
            "arguments": arguments
        }
