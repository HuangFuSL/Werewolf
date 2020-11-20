import gzip
import json
import socket
import threading
from io import BytesIO
from time import sleep
from .utils import _checkParam
from typing import Any, Dict, Optional, Tuple


class PacketTypeMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str):
        super().__init__()
        self.type: int = packetType
        self.field: str = fieldName

    def __str__(self):
        return "Packet type %d requires field '%s', which is not found." % (self.type, self.field)


class PacketFieldMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str, fieldType: type, expectedType: type):
        super().__init__()
        self.type: int = packetType
        self.name: str = fieldName
        self.field: type = fieldType
        self.expected: type = expectedType

    def __str__(self):
        return "Field %s of packet type %d requires type %s, got %s." % (self.name, self.type, str(self.expected), str(self.field))


class NotConnectedError(Exception):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return 'The socket is not connected.'


class ReceiveTimeoutError(Exception):

    def __init__(self, timeout: float):
        self.timeout: float = timeout
        super(ReceiveTimeoutError).__init__()

    def __str__(self):
        return "Data receive timeout."


class ChunckedData(object):

    @staticmethod
    def _compress(content: str) -> bytearray:
        buffer: BytesIO = BytesIO()
        with gzip.GzipFile(mode="wb", fileobj=buffer) as compressor:
            compressor.write(content.encode(encoding='utf-8'))
        return bytearray(buffer.getvalue())

    @staticmethod
    def _decompress(data: bytearray) -> str:
        buffer: BytesIO = BytesIO(bytes(data))
        with gzip.GzipFile(mode='rb', fileobj=buffer) as output:
            # REVIEW
            ret = output.read().decode(encoding="utf-8")
            print(ret)
            return ret

    def __init__(self, packetType: int, **kwargs: Any):
        """
        Defines a new data packet.
        """
        self.type: int = packetType
        self.content: Dict[str, Any] = {}
        if self.type == 0:
            try:
                self.content = json.loads(self._decompress(kwargs['rawData']))
            except KeyError:
                raise PacketTypeMismatchException(self.type, 'rawData')
            self.type = self.content['type']
            del self.content['type']
        else:
            self.content = kwargs
            # Check the content
            try:
                for i in _checkParam[''].keys():
                    if not isinstance(self.content[i], _checkParam[''][i]):
                        raise PacketFieldMismatchException(self.type, i, type(
                            self.content[i]), _checkParam[''][i])
                for i in _checkParam[self.type].keys():
                    if not isinstance(self.content[i], _checkParam[self.type][i]):
                        raise PacketFieldMismatchException(self.type, i, type(
                            self.content[i]), _checkParam[self.type][i])
            except KeyError as a:
                raise PacketTypeMismatchException(self.type, *a.args)

    def __getitem__(self, index):
        return self.content[index]

    def __setitem__(self, index, value):
        self.content[index] = value

    def getAddr(self, dest: str) -> Tuple[str, int]:
        assert dest in ('source', 'destination')
        if (dest == 'source'):
            return self.content['srcAddr'], self.content['srcPort']
        else:
            return self.content['destAddr'], self.content['destPort']

    def setValue(self, name: str, value: Any):
        self.content[name] = value

    def toBytesArray(self) -> bytearray:
        c = self.content.copy()
        c['type'] = self.type
        # REVIEW
        print(json.dumps(c))
        return self._compress(json.dumps(c))

    def send(self, connection: socket.socket):
        connection.send(bytes(self.toBytesArray()))


def _recv(connection: socket.socket) -> ChunckedData:
    ret = ChunckedData(0, rawData=connection.recv(16384))
    return ret


class ReceiveThread(threading.Thread):

    def __init__(self, connection: socket.socket, timeout: float = 0):
        super(ReceiveThread, self).__init__()
        self.result: Any = None
        self.timeout: float = timeout
        self.connection: socket.socket = connection
        self.exception: ReceiveTimeoutError = ReceiveTimeoutError(self.timeout)

    def run(self):
        if not self.timeout:
            self.result = _recv(self.connection)
        else:
            dest: ReceiveThread = ReceiveThread(self.connection)
            dest.setDaemon(True)
            dest.start()
            dest.join(self.timeout)
            self.result = dest.getResult()
            if self.result is None:
                self.exitcode = 1
                self.exception = ReceiveTimeoutError(self.timeout)
                self.exc_traceback = str(self.exception)

    def getResult(self) -> Optional[ChunckedData]:
        return self.result


class TimeLock(threading.Thread):
    """
    Start a thread waiting in the background.

    Initialization:

        timeout: int, the specified waiting time

    Methods:

        TimeLock.start(): start waiting
        TimeLock.getStatus(): get current status

    Notice:

        **TimeLock.setDeamon(True) should be called before starting.**
    """

    def __init__(self, timeout: float):
        super().__init__()
        self.end = False
        self.timeout = timeout

    def run(self):
        sleep(self.timeout)
        self.end = True

    def getStatus(self):
        return self.end
