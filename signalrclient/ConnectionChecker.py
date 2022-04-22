import logging
import time
from enum import Flag, auto

from .Util import Util


class ConnectionState(Flag):
	connected = auto()
	connecting = auto()
	reconnecting = auto()
	disconnecting = auto()
	disconnected = auto()
	handshaking = connecting | reconnecting
	running = connected | connecting | reconnecting


class ConnectionChecker(object):
	def __init__(self, keepAliveInterval, serverTimeout, sleep=5):
		self.logger = Util.configLogger(__name__)
		self.keepAliveInterval = keepAliveInterval
		self.serverTimeout = serverTimeout
		self.sleep = sleep
		self.running = False
		self.lastTrySend = None
		self.lastReceived = None
		self.ping = None
		self.stopConnection = None

	def run(self, ping, stop):
		self.ping = ping
		self.sendStop = stop
		self.running = True
		self.lastTrySend = time.time()
		self.lastReceived = time.time()

		while self.running:
			time.sleep(self.sleep)
			
			timeFromSend = time.time() - self.lastTrySend
			if timeFromSend > self.keepAliveInterval: self.ping()

			if self.serverTimeout is None: continue
			timeFromReceived = time.time() - self.lastReceived
			if timeFromReceived > self.serverTimeout:
				self.logger.error("elapsed time after last message from server {0:.1f} sec".format(timeFromReceived))
				self.sendStop()
				break

	def stop(self):
		self.running = False
