# signalrclient

Simple SignalR client for Python


# Installation

```bash
git clone https://github.com/koheishoji/signalrclient.git projdir
pip install ./projdir
```


# Usage

build connection

```python
import logging
from signalrclient.HubConnectionBuilder import HubConnectionBuilder

conn = HubConnectionBuilder() \
	.withUrl("wss://hogeguga.com", options={
		"accessTokenFactory": None,
		"verifySsl": False,
		"skipNegotiation": True
	}) \
	.configureLogging(level=logging.INFO) \
	.withAutomaticReconnect(interval=5) \
	.build()
```

start connection
```python
conn.onOpen(funcOpen)
conn.onClose(funcClose)
conn.on("receiveMessage", lambda x: messageHandler(x))
conn.start()
```

send message and stop
```python
while conn.isRunning():

	conn.send("sendMessage", [arg1, arg2])
	results = conn.invoke("invokeMessage", [arg1])

	if xxxxx:
		break

conn.stop()
```

# Description
Signalrclient is Python package to communicate with ASP.NET Core SignalR hub.

User creates connection object using HubConnectionBuilder and registers handlers. When connection is started, signalrclient creates two threads, websocket running and pediodic ping. Websocket running thread listens messages from SignalR hub server and fires registered handler when the message arrives. Pediodic ping thread keeps connection alive. When stop function is called from main thread, signalrclient terminates both websocket and ping threads.

While connection is running, user can send messages to server by using send or invoke function. Invoke function waits the return from the server but send does not.

Server functions like :
```C#
public async Task sendMessage(string arg1, string arg2)
{
	await Clients.Others.SendAsync(...);
}

public async Task<bool> invokeMessage(string arg1)
{
	await Clients.Group("XXX").SendAsync(...);
	return true;
}
```

If connection is lost because of poor network or something, signalrclient tries to reconnect with time interval specified at withAutomaticReconnect function. To disable automatic reconnction, set interval to None.

```python
	.withAutomaticReconnect(interval=None)
```


# Features

* Transport protocols
  - WebSockets

* Encoding
  - JSON - send, invoke

* NOT implemented
  - Transport
    - HTTP POST
    - Server-Sent Events
    - Long Polling
  - Encoding
    - JSON streaming
    - MessagePack


# Requirement

* websocket


# References

* SignalR Specification
https://github.com/dotnet/aspnetcore/tree/main/src/SignalR/docs/specs


# License
"signalrclient" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).

