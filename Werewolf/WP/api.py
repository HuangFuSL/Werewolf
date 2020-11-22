import ctypes
import gzip
import json
import socket
import threading
from io import BytesIO
from time import sleep
from typing import Any, Callable, Dict, Optional, Tuple

from .utils import _checkParam


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
            ret = output.read().decode(encoding="utf-8")
            # REVIEW for debugging
            # print(ret)
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
        # REVIEW for debugging
        # print(json.dumps(c))
        return self._compress(json.dumps(c))

    def send(self, connection: socket.socket):
        connection.send(bytes(self.toBytesArray()))


def _recv(connection: socket.socket) -> ChunckedData:
    """
    Wrapper for receiving thread.
    """
    ret = ChunckedData(0, rawData=connection.recv(16384))
    return ret


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


class KillableThread(threading.Thread):
    """
    A thread class extending threading.Thread, provides a kill() method to stop the thread and a getResult() method to get the return value of the thread.
    """

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func: Callable = func
        self.funcArg: dict = kwargs
        self.funcTup: Tuple = args
        self.result: Any = None
        self.exception: Any = None

    def run(self):
        """
        Executes the function here
        """
        try:
            self.result = self.func(*self.funcTup, **self.funcArg)
        except BaseException as e:
            self.exception = e

    def get_id(self):
        """
        Get the id of the thread
        """
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def kill(self):
        """
        Stops the thread
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

    def getResult(self):
        if self.exception is None:
            return self.result
        else:
            raise self.exception


def getInput(prompt: str, inputType: type = str, allowInterrupt: bool = False) -> Any:
    temp: str
    while True:
        try:
            temp = input(prompt)
        except EOFError:
            if allowInterrupt:
                return KeyboardInterrupt()
            else:
                continue
        if inputType != str:
            try:
                return eval(temp)
            except:
                print("你的输入格式不匹配")
        else:
            return temp


class ReadInput(KillableThread):
    """
    The input thread, will be interrupted by KeyBoardInterruption
    """

    def __init__(self, prompt: str, inputType: type = str, timeout: float = 0, allowInterrupt: bool = False):
        super().__init__(getInput)
        self.inputType = inputType
        self.timeout = timeout
        self.result: Any = None
        self.prompt = prompt
        self.allowInterrupt: bool = allowInterrupt

    def run(self) -> Any:
        if self.timeout == 0:
            self.result = getInput(self.prompt, self.inputType)
        else:
            dest: ReadInput = ReadInput(
                self.prompt, self.inputType, 0, self.allowInterrupt)
            dest.setDaemon(True)
            dest.start()
            dest.join(self.timeout)
            self.result = dest.getResult()
            if self.result is None:
                print("Input timeout.")

    def getResult(self) -> Any:
        """
        Get the return value of the input

        - inputType: if the input is correctly processed
        - `None`: if timeout
        - `KeyboardInterrupt`: if Ctrl-C is pressed
        """
        return self.result


class ReceiveThread(KillableThread):

    def __init__(self, connection: socket.socket, timeout: float = 0):
        super(ReceiveThread, self).__init__(_recv, *(connection, ))
        self.result: Any = None
        self.timeout: float = timeout
        self.connection: socket.socket = connection
        self.exception: Any = None

    def run(self):
        try:
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
        except BaseException as e:
            self.exception = e
            self.result = None

    def getResult(self) -> Optional[ChunckedData]:
        if self.exception is None:
            return self.result
        else:
            raise self.exception
