import threading
import requests
import traceback
import uuid
import time
import logging
import queue
from typing import Callable

from .Util import Util
from .Error import *
from .ConnectionChecker import ConnectionState, ConnectionChecker
from .Message import Message, MessageType
from .Transport import WebSocketTransport


class HubConnection(object):
	def __init__(self,
		url,
		protocol,
		transport,
		connectionChecker,
		reconnection,
		surrender,
		authFunction,
		verifySsl,
		skipNegotiation,
		headers
	):
		self.url = url
		self.protocol = protocol
		self.transport = transport
		self.connectionChecker = connectionChecker
		self.reconnection = reconnection        
		self.surrender = surrender
		self.authFunction = authFunction
		self.verifySsl = verifySsl
		self.skipNegotiation = skipNegotiation
		self.headers = headers

		self.logger = Util.configLogger(__name__)
		self.invokeTimeout = 5
		self.state = ConnectionState.disconnected

		self.threadTransport = None
		self.threadChecker = None

		self.resultQueues = []
		self.eventHandlers = []
		self.callbacks = []

		self._onOpen = lambda: self.logger.debug("dummy onOpen")
		self._onClose = lambda: self.logger.debug("dummy onClose")
		self._onReconnecting = lambda: self.logger.debug("dummy onReconnecting")
		self._onReconnected = lambda: self.logger.debug("dummy onReconnected")

	def __exit__(self, exception_type, exception_value, traceback):
		self.stop()

	def isRunning(self):
		return self.state & ConnectionState.running

	def start(self):
		if self.isRunning():
			self.logger.warning("already running, unable to start")
			return False
		
		self.logger.info("start connection")
		self.state = ConnectionState.connecting
		self.threadTransport = threading.Thread(target=self._run)
		self.threadTransport.setDaemon(True)
		self.threadTransport.start()
		return True

	def _run(self):
		self.threadChecker = threading.Thread(target=self.connectionChecker.run, args=(self._sendPing, self.stop))
		self.threadChecker.setDaemon(True)
		self.threadChecker.start()

		while True:
			try:
				if self.state == ConnectionState.reconnecting: self._onReconnecting()

				if self.authFunction is not None:
					token = self.authFunction()
					self.logger.debug("auth function result {0}".format(token))
					self.headers["Authorization"] = "Bearer " + token

				if not self.skipNegotiation: self._negotiate()
				
				self.logger.info("connect to " + self.url)
				self.transport.initialize(
					self.url,
					header=self.headers,
					onOpen=self._onTransportOpen,
					onMessage=self._onTransportMessage,
					onError=self._onTransportError,
					onClose=self._onTransportClose
				)
				self.transport.run(self.verifySsl)

			except requests.exceptions.ConnectionError as e:
				self.logger.warning("connection error on negotiation {}".format(e))

			except (UnauthorizedError, Exception) as e:
				self.logger.exception("error while transport run : {}".format(e))
				self.state = ConnectionState.disconnecting

			finally:
				if self.state == ConnectionState.connecting and self.surrender: break
				if self.state == ConnectionState.disconnecting: break
				if self.reconnection is None: break

				self.logger.info("reconnecting")
				self.state = ConnectionState.reconnecting
				time.sleep(self.reconnection)

		self.logger.info("connection stopped")
		self.connectionChecker.stop()
		self.state = ConnectionState.disconnected
		self._onClose()

	def _negotiate(self):
		negotiateUrl = Util.getNegotiateUrl(self.url)
		self.logger.debug("negotiate url {0}".format(negotiateUrl))

		response = requests.post(negotiateUrl, headers=self.headers, verify=self.verifySsl)
		self.logger.debug("response status code {0}".format(response.status_code))

		if response.status_code != 200:
			raise UnauthorizedError("negotiation response has status code {0}".format(response.status_code))

		negotiateResults = response.json()
		self.logger.debug("negotiation results : {0}".format(negotiateResults))
		
	def stop(self):
		if self.isRunning():
			self.logger.info("stop connection")
			self.state = ConnectionState.disconnecting
			self.transport.stop()
			self._checkThread(5)

	# stop could be ignored if called while reconnecting
	# stop called from same thread(onTransportXXX) works fine
	def _checkThread(self, ntry):
		if threading.get_ident() == self.threadTransport.ident: return

		self.threadTransport.join(3)
		if self.threadTransport.is_alive():
			if ntry == 0: raise ConnectionClosingError()
			self.state = ConnectionState.disconnecting
			self.transport.stop()
			self._checkThread(ntry - 1)

	def onOpen(self, handler):
		if not callable(handler):
			raise TypeError("argument handler must be callable function")
		self._onOpen = handler

	def onClose(self, handler):
		if not callable(handler):
			raise TypeError("argument handler must be callable function")
		self._onClose = handler

	def onReconnecting(self, handler):
		if not callable(handler):
			raise TypeError("argument handler must be callable function")
		self._onReconnecting = handler

	def onReconnected(self, handler):
		if not callable(handler):
			raise TypeError("argument handler must be callable function")
		self._onReconnected = handler

	def on(self, event, handler):
		if not callable(handler):
			raise TypeError("argument handler must be callable function")
		self.logger.info("event handler registered {0}".format(event))
		self.eventHandlers.append((event, handler))

	def off(self, event):
		self.logger.info("event handler unregistered {0}".format(event))
		self.eventHandlers = [x for x in self.eventHandlers if x[0] != event]

	def invoke(self, target, arguments):
		if type(arguments) is not list: raise TypeError("arguments must be a list")
		if self.state != ConnectionState.connected: raise NotConnectedError()

		try:
			invocationId = str(uuid.uuid4())
			message = Message.createInvocation(invocationId, target, arguments, headers=self.headers)
			myQueue = {"invocationId": invocationId, "queue": queue.Queue()}
			
			self.resultQueues.append(myQueue)
			self._sendTransport(message)

			result = myQueue["queue"].get(timeout=self.invokeTimeout)
			return result
		except queue.Empty as e:
			self.resultQueues.remove(myQueue)
			raise InvokeTimeoutError("cannot get result within {} sec".format(self.invokeTimeout))
		except Exception as e:
			raise
	
	def send(self, target, arguments):
		if type(arguments) is not list: raise TypeError("arguments must be a list")
		if self.state != ConnectionState.connected: raise NotConnectedError()
		
		try:
			message = Message.createInvocationNonBlocking(target, arguments, headers=self.headers)
			self._sendTransport(message)
		except Exception as e:
			raise
		
	def _sendPing(self):
		if self.state != ConnectionState.connected: return
		
		try:
			message = Message.createPing()
			self._sendTransport(message)
		except Exception as e:
			pass

	def _sendHandshake(self):
		if not self.state & ConnectionState.handshaking: return

		try:
			message = Message.createHandshakeRequest(self.protocol.name, self.protocol.version)
			self._sendTransport(message)
		except Exception as e:
			self.stop()
			self.logger.exception("failed to send handshake : {0}".format(e))

	def _sendTransport(self, message):
		try:
			self.connectionChecker.lastTrySend = time.time()
			self.logger.debug("sending message {0}".format(Util.getSliced(message)))
			encoded = self.protocol.encode(message)
			self.logger.debug("message encoded {0}".format(Util.getSliced(encoded)))
			self.transport.send(encoded)

		except Exception as e:
			raise SendTransportError() from e

	def _onTransportOpen(self, ws):
		self.logger.debug("transport opened")
		self._sendHandshake()

	def _onTransportClose(self, ws):
		self.logger.debug("transport closed")

	def _onTransportError(self, ws, err):
		try:
			self.transport.onError(err)

		except Exception as errTransport:
			self.logger.exception("transport error {0}".format(errTransport))
			self.stop()

	def _onTransportMessage(self, ws, message):
		self.connectionChecker.lastReceived = time.time()
		self.logger.debug("message received {0}".format(Util.getSliced(message)))
		decoded = self.protocol.decode(message)
		self.logger.debug("message decoded {0}".format(Util.getSliced(decoded)))

		if self.state & ConnectionState.handshaking:
			self._confirmHandshake(decoded.pop(0))
		
		self._messageHandler(decoded)

	def _confirmHandshake(self, response):
		self.logger.debug("check handshake response {0}".format(response))
		
		if response.get("error", "") == "":
			try:
				oldState = self.state
				self.resultQueues.clear()
				self.state = ConnectionState.connected
				self.logger.info("connection started")
				if oldState == ConnectionState.connecting: self._onOpen()
				if oldState == ConnectionState.reconnecting: self._onReconnected()
				
			except Exception as e:
				self.stop()
				self.logger.exception("failed {0}".format(e))
		else:
			self.stop()
			self.logger.exception("handshake failed : {0}".format(response.get("error")))

	def _messageHandler(self, messages):
		for message in messages:
			if message["type"] == MessageType.ping:
				self.logger.debug("received ping")

			if message["type"] == MessageType.close:
				self.logger.info("close message received from server")

			if message["type"] == MessageType.invocation:
				targetHandlers = [x for x in self.eventHandlers if x[0] == message["target"]]
				if len(targetHandlers) == 0:
					self.logger.warning("event '{0}' doesn't fire any handler".format(message["target"]))
				try:
					for handler in targetHandlers: handler[1](message["arguments"])
				except Exception as e:
					self.stop()
					self.logger.exception("handler {0} had error {1}".format(handler[0], e))

			if message["type"] == MessageType.completion:
				error = message.get("error", None)
				result = message.get("result", None)
				out = None
				if result is not None: out = result
				if error is not None: out = error

				myQueues = [x for x in self.resultQueues if x["invocationId"] == message["invocationId"]]
				self.resultQueues = [x for x in self.resultQueues if x["invocationId"] != message["invocationId"]]
				
				resultQueue = myQueues[0] if len(myQueues) > 0 else None
				if resultQueue is not None: resultQueue["queue"].put(out)
