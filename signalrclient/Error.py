

class UnauthorizedError(Exception):
	pass

class WebSocketError(Exception):
	pass

class InvokeTimeoutError(Exception):
	pass

class SendTransportError(Exception):
	def __init__(self, message=""):
		if message == "": message = "send message failed at transport level"
		super().__init__(message)

class NotConnectedError(Exception):
	def __init__(self, message=""):
		if message == "": message = "not connected now, cannot execute invoke/send method"
		super().__init__(message)

class ConnectionClosingError(Exception):
	def __init__(self, message=""):
		if message == "": message = "failed to close connection"
		super().__init__(message)
