# WP - Werewolf Protocol

Werewolf Protocol (WP in the context) defines ways for server and clients to communicate.

> For detailed gamerule, please refer to [`README.md`](../../README.md) in thr root directory.

Modules in the package are:

* `api.py`: provides an interface to send, receive and decode the data;
* `utils.py`: defines global variables in the module.

## `api.py`

`api.py` contains class `ChunckedData`, which use `json` module to encode data and `gzip` module to compress data. Class `ReceiveThread` which is a subclass of `threading.Thread` is used to open a new thread to receive data.

Methods:

* `ChunckedData(type, **kwargs)`: initialize a new data packet.
  * `type`: `int`, indicate the content type of the packet.
  * `kwargs`: `dict`, content required by the packet. For a full list of contents please refer to `utils.py` part.
  * Throws `PacketTypeMismatchException` when a required field for the package is not found and throws `PacketFieldMismatchException` when value provided is not compatible with the expected type.
* `ChunckedData.setValue(name, value)`: modify the content of the packet manually.
  * `name`: `str`, name of the attribute.
  * `value`: `Any`, value of the attribute.
* `ChunckedData.toBytesArray()`: transform the packet to a gzipped bytearray.
  * Returns: a `bytearray` object.
* `ChunckedData.send(connection)`: send the data through the given socket.
  * `connection`: `socket.socket`, the socket to perform the action.
  * Throws `NotConnectedError` when the connection request is not yet accepted and throws `AssertionError` when the destination address is in conflict with the address in package.
* `ReceiveThread(socket)`: initialize a new thread for receiving the data packet.
* `ReceiveThread.start()`: start a new thread to receive data, this method is inherited from `threading.Thread`.
* `ReceiveThread.join()`: block the main thread until the thread stopped, this method is inherited from `threading.Thread`.
* `ReceiveThread.getResult()` get the returned value after the thread has stopped.
  * `timeout`: `int`, maximum waiting time before raising `ReceiveTimeoutError`.
  *  Returns a `ChunckedData` object.

Private methods - these methods should **NOT** be called outside the module.

* `ChunckedData._compress(content)`: compress a string to a bytearray using gzip.
  * `content`: `str`, the string to be compressed.
  * Returns: a `bytearray` object.
* `ChunckedData._decompress(data)`: decompress the bytearray to get a `ChunckedData` object.
  * `data`: `bytearray`, the bytearray to be decoded.
  * Returns: a `ChunckedData` object.
* `_recv(connection)`: receives the data using a given socket
  * `connection`: `socket.socket`, the socket used to receive data
  * Returns: a `ChunckedData` object.

## `utils.py`

Contents:

* `py2`: Version of the Python environment. Will be `true` if the script is running in a Python 2.x environment.
* `_packetType`: Defines the different packets to be used.
* `_checkParam`: Defines the format of the packets. The number corresponds with the values in `_packetType`

Values in `_packetType`:

|Key|Value|Description|
|:-:|:---:|:---------:|
|EncodedData|0|Encoded data is first decoded, then analyzed.|
|Establish|1|The client requests to establish a connection with the server.|
|EstablishResp|-1|The server informs the client about the current game status.|
|Choose|2|The client requests to choose a specified seat.|
|ChooseResp|-2|The server informs the position and in-game identity of the client.|
|ActionPrompt|3|The server requests the client to take an action.|
|ActionResp|-3|The client choose an available action.|
|InformationPublishing|4|The server post information to all of the players.|
|InformationPublishingResp|-4|The ACK packet corresponds to a 'InformationPublishing' packet.|
|FreeConversation|5|The client send message freely. The server does not reply, only forwards it.|
|LimitedConversation|6|The server request the client to send message.|
|LimitedConversationResp|-6|The client submits the message to be sent.|
|Vote|7|The server requests the client to vote.|
|VoteResp|-7|The client reply to the server.|
|Death|8|The server informs the client loses the game.|

Values in `_checkParam`:

Except for the EncodedData packet, all other kinds of packets contain the following common fields.

|Attribute|Type|Description|
|:-------:|:--:|:---------:|
|srcAddr|`str`| The IP address of the sender|
|destAddr|`str`| The IP address of the receiver|
|srcPort|`int`|The outgoing port of the sender|
|destPort|`int`|The incoming port of the receiver|

* EncodedData

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|rawData|`bytearray`|The raw data send through network|
* Establish: This kind of packet does not contain any other fields.
* EstablishResp:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|playerRemaining|`int`|Remaining seats in the room|
	|playerSeats|`list`|Available seats in the room|

* Choose:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|chosenSeat|`int`|Seat chosen by the player|

* ChooseResp:
  
	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|success|`bool`|`False` if the requested seat is invalid|
	|chosenSeat|`int`|Number of seat actually chosen|
	|identity|`int`|The in-game identity of the player|

* ActionPrompt:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|identityLimit|`list`|Identity list of the player to receive the message|
	|format|`tuple`|The format of the response|
	|prompt|`str`|Command line prompt for user to enter the action|
	|timeLimit|`int`|Time limit for a player to make decision, measured in seconds|

* ActionResp:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|action|`bool`|Whether or not the player take action|
	|response|`Any`|The action taken|

* InformationPublishing:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|description|`str`|The message being posted|
	|parameter|`tuple`|The parameter of the message|

* InformationPublishingResp:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|ACK|`bool`|Always `true`|

* FreeConversation:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|content|`str`|The content of the message|
	|type|`tuple`|Identity list of the player to receive the message|

* LimitedConversation:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|timeLimit|`int`|Time limit for a player to prepare the message, measured in seconds|

* LimitedConversationResp:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|content|`str`|The content of the message|

* Vote:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|ACK|`bool`|Whether the player can vote / Whether the vote is valid|

* VoteResp:

	|Attribute|Type|Description|
	|:-------:|:--:|:---------:|
	|vote|`bool`|Whether the player has voted|
	|candidate|`int`|The number of player voted to|

* Death: This kind of packet does not contain any other fields.

## Testing

The module use `pytest` to run the testcase. Execute `pytest` in the package directory to start a test.