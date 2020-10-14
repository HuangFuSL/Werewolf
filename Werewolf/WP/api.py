import gzip
import json
import pytest
from io import BytesIO
from .utils import _checkParam

class PacketTypeMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str):
        self.type = packetType
        self.field = fieldName
    
    def __str__(self):
        return "Packet type %d requires field '%s', which is not found." % (self.type, self.field)

class PacketFieldMismatchException(Exception):

    def __init__(self, packetType: int, fieldName: str, fieldType: type, expectedType: type):
        self.type = packetType
        self.name = fieldName
        self.field = fieldType
        self.expected = expectedType

    def __str__(self):
        return "Field %s of packet type %d requires type %s, got %s." % (self.name, self.type, str(self.expected), str(self.field))

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
            try:
                for i in _checkParam[''].keys():
                    if not isinstance(self.content[i], _checkParam[''][i]):
                        raise PacketFieldMismatchException(self.type, i, type(self.content[i]), type(_checkParam[''][i]))
                for i in _checkParam[self.type].keys():
                    if not isinstance(self.content[i], _checkParam[self.type][i]):
                        raise PacketFieldMismatchException(self.type, i, type(self.content[i]), type(_checkParam[self.type][i]))
            except KeyError as a:
                raise PacketTypeMismatchException(self.type, *a.args)
                

    @staticmethod
    def _compress(content: str) -> bytearray:
        buffer = BytesIO()   
        compressor = gzip.GzipFile(mode="wb", fileobj=buffer)
        compressor.write(content.encode(encoding='utf-8'))
        compressor.close()
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

    def send(self):
        # TODO: Send the data to the remote
        pass

def receive() -> ChunckedData:
    # TODO: Receive the data and decode
    pass