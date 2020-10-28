import socket
import abc
from time import sleep
from threading import Thread

from WP.api import ChunckedData, ReceiveThread, ReceiveTimeoutError

_default_timeout = 30.0

def default_timeout(timeout = None):
    if timeout is not None and timeout > 0:
        _default_timeout = timeout
    return _default_timeout

class TimeLock(Thread):

    def __init__(self, timeout: float = _default_timeout):
        self.end = False
        self.timeout = timeout

    def run(self):
        sleep(self.timeout)
        self.end = True

    def getStatus(self):
        return self.end


class Person():

    def __init__(self, id: int, client: tuple, server: tuple):
        # AF_INET：使用TCP/IP-IPv4协议簇；SOCK_STREAM：使用TCP流
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client = client
        self.server = server
        self.id = id
        self.police = False # police的值由服务器进行分配，在__init__()方法中被初始化为False
        self.innocent = True # 如果某个客户端是狼人，则innocent的值为False；否则为True
        self.alive = True
        self.recv.bind(server)
        self.recv.listen(1)

    def _getBasePacket(self) -> dict:
        """
        获取地址与端口信息
        """
        ret = {}
        ret['srcAddr'] = self.server[0]
        ret['srcPort'] = self.server[1]
        ret['destAddr'] = self.client[0]
        ret['destPort'] = self.client[1]
        return ret

    def startListening(self, timeout=0):
        recevingThread = ReceiveThread(self.recv, timeout)
        recevingThread.start()
        recevingThread.join()
        try:
            return recevingThread.getResult()
        except ReceiveTimeoutError as e:
            return None

    def vote(self, timeout: float = _default_timeout):
        packet = self._getBasePacket()
        pakcet['prompt'] = "Please vote for the people to be banished:"
        packetSend = ChunckedData(7, packet)
        sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
        sendingThread.start()
        return startListening(timeout=timeout)

    def joinElection(self, timeout: float = _default_timeout):
        packet = self._getBasePacket()
        packet['format'] = bool
        packet['prompt'] = 'Do you want to be the policeman?\nYou have %f seconds to decide.' % (timeout, )
        packet['timeout'] = timeout
        packetSend = ChunckedData(3, packet)
        sendingThread = Thread(target=packetSend.send(), args=(self.socket,))
        sendingThread.start()
        return startListening(timeout=timeout)


    def voteForPolice(self, timeout: float = _default_timeout):
        if not self.police:
            packet = self._getBasePacket()
            packet['prompt'] = "Please vote for the police:"
            packetSend = ChunckedData(7, packet)
            sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
            sendingThread.start()
            return startListening(timeout=timeout)
        else:
            return None

    def setPolice(self, val: bool = True):
        self.police = val

    def speak(self, timeout: float = _default_timeout):
        packet = self._getBasePacket()
        packet['timeLimit'] = timeout
        packetSend = ChunckedData(6, packet)
        sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
        sendingThread.start()
        return startListening(timeout=timeout)

    def sendMessage(self, data: list = []):
        packet = self._getBasePacket()
        packet['description'] = '\n'.join(data)
        packet['parameter'] = tuple()
        sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
        sendingThread.start()

    def onDead(self, withFinalWords: bool, timeouts: tuple):
        """
        玩家出局，需要讨论警徽归属与遗言
        """
        self.alive = False
        ret = []
        if self.police:
            packet = self._getBasePacket()
            packet['prompt'] = "Please select the player you want to inherit the police:"
            packetSend = ChunckedData(7, packet)
            sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
            sendingThread.start()
            ret.append(self.startListening(timeout=timeouts[0]))
        else:
            ret.append(None)
        if withFinalWords:
            packet = self._getBasePacket()
            packet['timeLimit'] = timeouts[1]
            packetSend = ChunckedData(6, packet)
            sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
            sendingThread.start()
            ret.append(self.startListening(timeout=timeouts[1]))
        else:
            ret.append(None)
        return ret


class Villager(Person):
    """
    村民类型，没有任何技能
    """
    def __init__(self, id: int, client: tuple, server: tuple):
        super().__init__(id, client, server)


class Wolf(Person):
    """
    狼人，在夜间醒来，可以选择杀一个人
    """
    def __init__(self, id: int, client: tuple, server: tuple):
        super().__init__(id, client, server)
        self.innocent = False
        self.peerList = []

    def setPeer(peer: Wolf):
        self.peerList.append(peer)

    def removePeer(peer: Wolf):
        self.peerList.remove(peer)

    def kill(self, alivePlayers: list, timeout: float = _default_timeout):
        """
        狼人之间进行讨论及确定投票目标
        """
        packet = self._getBasePacket()
        packet['format'] = int
        packet['prompt'] = "Please select a person to kill.\nYou have %f seconds to decide with your partner" % (timeout, )
        packet['timeout'] = timeout
        packetSend = ChunckedData(3, packet)
        sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
        sendingThread.start()
        timer = TimeLock(timeout)
        timer.setDaemon(True)
        timer.start()
        while not timer.getStatus():
            dataRecv = self.startListening(timeout)
            if dataRecv is None or dataRecv['type'] == -3:
                return dataRecv
            elif dataRecv['type'] == 5:
                dataRecv.pop('type')
                packetSend = ChunckedData(5, dataRecv)
                sendingThreads = [Thread(target=packetSend.send(), args=(_, )) for _ in self.peerList.socket]
                for thread in sendingThreads:
                    thread.start()
        return None

class SkilledPerson(Person):

    def __init__(self, id: int, client: tuple, server: tuple):
        super(SkilledPerson, self).__init__(id, client, server)
        self.used = False

    def postSkill(self):
        self.used = True

    def skill(self, prompt: str = "", timeout: float = _default_timeout, format: type = int):
        self.used = True
        packet = self._getBasePacket()
        packet['format'] = format
        packet['prompt'] = prompt
        packet['timeout'] = timeout
        packetSend = ChunckedData(3, packet)
        sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
        sendingThread.start()
        return self.startListening(timeout)

class KingOfWerewolves(Wolf, SkilledPerson):

    def __init__(self, id: int, client: tuple, server: tuple):
        super(KingOfWerewolves, self).__init__(id, client, server)

    def skill(self, timeout: float = _default_timeout):
        self.used = True
        prompt = """Please select a person to kill.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class WhiteWerewolf(Wolf, SkilledPerson):

    def __init__(self, id: int, client: tuple, server: tuple):
        super(WhiteWerewolf, self).__init__(id, client, server)

    def skill(self, timeout: float = _default_timeout):
        prompt = """Please select a person to kill.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Predictor(SkilledPerson):
    
    def __init__(self, id: int, client: tuple, server: tuple):
        super(Predictor, self).__init__(id, client, server)

    def skill(self, timeout: float = _default_timeout):
        prompt = """Please select a person to inspect his identity.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Witch(SkilledPerson):
    
    def __init__(self, id: int, client: tuple, server: tuple):
        super(Witch, self).__init__(id, client, server)

    def skill(self, killed: int = 0, timeout: float = _default_timeout):
        packet = self._getBasePacket()
        packet['content'] = "The player %s is killed at night." % (str(killed) if killed else "unknown", )
        packetSend = ChunckedData(5, packet)
        prompt = """Please select a person to use the poison. If you want to save the victim, enter "save".
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout, (int, str))


class Hunter(SkilledPerson):

    def __init__(self, id: int, client: tuple, server: tuple):
        super(Hunter, self).__init__(id, client, server)

    def skill(self, timeout: float = _default_timeout):
        prompt = """Please select a person to kill.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Guard(SkilledPerson):
    
    def __init__(self, id: int, client: tuple, server: tuple):
        super(Guard, self).__init__(id, client, server)

    def skill(self, timeout: float = _default_timeout):
        prompt = """Please select a person to guard.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Idiot(SkilledPerson):
    
    def __init__(self, id: int, client: tuple, server: tuple):
        super(Idiot, self).__init__(id, client, server)

    def skill(self):
        self.postSkill()

    def onDead(self, killedAtNight, withFinalWords, timeouts):
        if killedAtNight or self.used: 
            return super().onDead(withFinalWords, timeouts)
        else:
            self.skill()
            return None
