import logging
from urllib import parse
import json


class Util(object):

	loggingLevel = logging.INFO
	loggingHandler = None
	logSocketTrace = False

	@classmethod
	def configLogger(cls, name):
		logger = logging.getLogger(name)
		logger.setLevel(cls.loggingLevel)
		if cls.loggingHandler is not None: logger.addHandler(cls.loggingHandler)
		return logger

	@staticmethod
	def getNegotiateUrl(url):
		parsedUrl = parse.urlparse(url)
		parsedUrl = parsedUrl._replace(scheme=parsedUrl.scheme.replace("ws", "http"))
		negotiateSuffix = "negotiate" if parsedUrl.path.endswith('/') else "/negotiate"
		parsedUrl = parsedUrl._replace(path=parsedUrl.path + negotiateSuffix)
		return parse.urlunparse(parsedUrl)

	@classmethod
	def getSliced(cls, subject):
		message = ""
		if cls.loggingLevel != logging.DEBUG: return message

		if type(subject) is dict: message = json.dumps(subject)
		if type(subject) is list: message = json.dumps(subject)
		if type(subject) is str: message = subject
		
		if len(message) < 300: return message
		return message[0:99] + " ... " + message[-100:-1]
