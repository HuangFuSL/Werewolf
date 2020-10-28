import gzip
import json
import socket
import threading
from io import BytesIO
from .utils import _checkParam

class PacketTypeMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str):
        super.__init__()
        self.type = packetType
        self.field = fieldName
    
    def __str__(self):
        return "Packet type %d requires field '%s', which is not found." % (self.type, self.field)

class PacketFieldMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str, fieldType: type, expectedType: type):
        super.__init__()
        self.type = packetType
        self.name = fieldName
        self.field = fieldType
        self.expected = expectedType

    def __str__(self):
        return "Field %s of packet type %d requires type %s, got %s." % (self.name, self.type, str(self.expected), str(self.field))

class NotConnectedError(Exception):

    def __init__():
        super.__init__()

    def __str__(self):
        return 'The socket is not connected.'

class ReceiveTimeoutError(Exception):

    def __init__(self, timeout: int):
        self.timeout = timeout
        super(ReceiveTimeoutError).__init__()

    def __str__(self):
        return "Data receive timeout."


class ChunckedData(object):

    def __init__(self, packetType: int, **kwargs):
        """
        Defines a new data packet.
        """
        self.type = packetType
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
                        raise PacketFieldMismatchException(self.type, i, type(self.content[i]), type(_checkParam[''][i]))
                for i in _checkParam[self.type].keys():
                    if not isinstance(self.content[i], _checkParam[self.type][i]):
                        raise PacketFieldMismatchException(self.type, i, type(self.content[i]), type(_checkParam[self.type][i]))
            except KeyError as a:
                raise PacketTypeMismatchException(self.type, *a.args)

    def setValue(self, name, value):
        self.content[name] = value       

    @staticmethod
    def _compress(content: str) -> bytearray:
        buffer = BytesIO()   
        with gzip.GzipFile(mode="wb", fileobj=buffer) as compressor:
            compressor.write(content.encode(encoding='utf-8'))
        return buffer.getvalue()

    @staticmethod
    def _decompress(data: bytearray) -> str:
        buffer = BytesIO(data)
        with gzip.GzipFile(mode='rb', fileobj=buffer) as output:
            return output.read()

    def toBytesArray(self) -> bytearray:
        c = self.content.copy()
        c['type'] = self.type
        return self._compress(json.dumps(c))

    def send(self, connection: socket.socket, dest: tuple):
        connection.connect(dest)
        assert (self.content['destAddr'], self.content['destPort']) == connection.getpeername()
        connection.send(self.toBytesArray())

def _recv(connection: socket.socket) -> ChunckedData:
    connection.listen(5)
    c, addr = connection.accept()
    ret = ChunckedData(0, rawData=c.recv(16384))
    assert (ret.content['destAddr'], ret.content['destPort']) == c.getsockname()
    c.close()
    return ret

class ReceiveThread(threading.Thread):

    def __init__(self, connection: socket.socket, timeout: float = 0):
        super(ReceiveThread, self).__init__()
        self.result = None
        self.timeout = timeout
        self.connection = connection
        self.exitcode = 0
        self.exception = None
        self.exc_traceback = ''

    def run(self):
        if not self.timeout:
            self.result = _recv(self.connection)
        else:
            dest = ReceiveThread(self.connection)
            dest.setDaemon(True)
            dest.start()
            dest.join(self.timeout)
            self.result = dest.getResult()
            if self.result is None:
                self.exitcode = 1
                self.exception = ReceiveTimeoutError(self.timeout)
                self.exc_traceback = str(self.exception)
                

    def getResult(self) -> ChunckedData:
        try:
            assert not isinstance(self.exception, ReceiveTimeoutError)
            return self.result  
        except AssertionError:
            raise self.exception
        except:
            return None
