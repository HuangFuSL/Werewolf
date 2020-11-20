import socket
from threading import Thread
from typing import Optional, List, Tuple

from ..WP.api import ChunckedData, ReceiveThread, TimeLock, _recv

defaultTimeout: float = 120.0  # 超时时间，是各方法的默认参数


def default_timeout(timeout=None) -> float:
    """
    Get or set the default timeout value.

    Parameter:

    - float or `None`
        * float: set the default timeout value
        * `None`: get the default timeout value

    Returns:

    * float, the value of the default timeout
    """
    global defaultTimeout
    if timeout is not None and timeout > 0:
        defaultTimeout = timeout
    return defaultTimeout


class Person():

    """
    Base class for a player.

    Attributes:

        id: the identifier of the player.

        socket: the outgoing socket for communication with the client
        recv: the incoming socket for communication with the client
        client: the (ip, port) tuple format of address of the client
        server: the (ip, port) tuple format of address of the server

        police: bool, whether the player is the police
        innocent: bool, whether the player is innocent, this attribute is for the predictor
        alive: bool whether the player is alive

    Private methods:

        _getBasePacket(): Get a template of the packet
        _startListening(): Listen to the port and return the data received

    Methods:

        vote(): Inform the client to vote for the exiled
        joinElection(): Ask the client to join the election
        voteForPolice(): Inform the client to vote for the police
        setPolice(): The result of the vote
        speak(): The player communicate with each other in day
        onDead(): Perform actions after the player is killed

    """

    def __init__(self, id: int, connection: socket.socket):
        """
        Initialize the player

        Parameters:

            id: int, provided by the upper layer
            client: tuple, in form of (ip, port)
            server: tuple, same with client

        Returns:

            Person, the objcet created.
        """
        # AF_INET：使用TCP/IP-IPv4协议簇；SOCK_STREAM：使用TCP流
        self.socket = connection
        self.server = self.socket.getsockname()
        self.client = self.socket.getpeername()
        self.id = id
        self.police = False  # police的值由服务器进行分配，在__init__()方法中被初始化为False
        self.innocent = True  # 如果某个客户端是狼人，则innocent的值为False；否则为True
        self.alive = True

    def _getBasePacket(self) -> dict:
        """
        Gets a packet for modification

        Parameters:

            None

        Returns:

            dict, containing the IP address and the port of the client and the server.
        """
        ret = {}
        ret['srcAddr'] = self.server[0]
        ret['srcPort'] = self.server[1]
        ret['destAddr'] = self.client[0]
        ret['destPort'] = self.client[1]
        return ret

    def _startListening(self, timeout=0) -> ReceiveThread:
        """
        Listen to the client for a specified time.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            ChunckedData, the data received
        """
        recevingThread = ReceiveThread(self.socket, timeout)
        recevingThread.start()
        return recevingThread

    def inform(self, content: str):
        packet = self._getBasePacket()
        packet['content'] = content
        packetSend = ChunckedData(4, **packet)
        sendingThread = Thread(target=packetSend.send,
                               args=(self.socket, ))
        sendingThread.start()

    def vote(self, timeout: float = defaultTimeout) -> ReceiveThread:
        """
        Send a package to a player to vote for the exiled.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            ReceiveThread, the thread receiving from the client
        """
        packet = self._getBasePacket()
        packet['prompt'] = "Please vote for the people to be banished:"
        packet['timeLimit'] = timeout
        packetSend = ChunckedData(7, **packet)
        sendingThread = Thread(target=packetSend.send,
                               args=(self.socket, ))
        sendingThread.start()
        return self._startListening(timeout=timeout)

    def joinElection(self, timeout: float = defaultTimeout) -> ReceiveThread:
        """
        Send a package to a player to join the police election.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            ReceiveThread, the thread receiving from the client
        """
        packet = self._getBasePacket()
        packet['format'] = 'bool'
        packet['prompt'] = 'Do you want to be the policeman?\nYou have %f seconds to decide.\nEnter `True` to join and `False` to stay out.' % (
            timeout, )
        packet['timeLimit'] = timeout
        packet['iskill'] = False
        packetSend = ChunckedData(3, **packet)
        sendingThread = Thread(target=packetSend.send, args=(self.socket,))
        sendingThread.start()
        return self._startListening(timeout=timeout)

    def policeSetseq(self, timeout: float = defaultTimeout) -> Optional[ReceiveThread]:
        """
        Send a package to a player to vote for the police.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            receiveThread, the thread receiving from the client
        """
        if self.police:
            packet = self._getBasePacket()
            packet['prompt'] = "Please choose the sequence: True for clockwise and False for anti-clockwise:\n"
            packet['timeLimit'] = timeout
            packet['iskill'] = False
            packet['format'] = "bool"
            packetSend = ChunckedData(3, **packet)
            sendingThread = Thread(
                target=packetSend.send, args=(self.socket, ))
            sendingThread.start()
            return self._startListening(timeout=timeout)
        else:
            return None

    def setPolice(self, val: bool = True):
        """
        Set the player to be the police.

        Parameters:

            val: bool, whether the player is the police

        Returns:

            None
        """
        self.police = val

    def voteForPolice(self, timeout: float = defaultTimeout) -> Optional[ReceiveThread]:
        """
        Send a package to the police to choose the sequence.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            receiveThread, the thread receiving from the client
        """
        if not self.police:
            packet = self._getBasePacket()
            packet['prompt'] = "Please vote for the police:"
            packet['timeLimit'] = timeout
            packetSend = ChunckedData(7, **packet)
            sendingThread = Thread(
                target=packetSend.send, args=(self.socket, ))
            sendingThread.start()
            return self._startListening(timeout=timeout)
        else:
            return None

    def speak(self, timeout: float = defaultTimeout) -> ReceiveThread:
        """
        Send a package to a player to talk about the situation before the vote.

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            ReceiveThread, the thread receiving from the client
        """
        packet = self._getBasePacket()
        packet['timeLimit'] = timeout
        packetSend = ChunckedData(6, **packet)
        sendingThread = Thread(target=packetSend.send,
                               args=(self.socket, ))
        sendingThread.start()
        return self._startListening(timeout=timeout)

#   def sendMessage(self, data: list = []):
#       packet = self._getBasePacket()
#       packet['description'] = '\n'.join(data)
#       packet['parameter'] = tuple()
#       sendingThread = Thread(target=packetSend.send(), args=(self.socket, ))
#       sendingThread.start()

    def onDead(self, withFinalWords: bool, timeouts: float):
        """
        Called on the death of a player.

        Parameters:

            withFinalWords: bool, whether the player can talk at death.
            timeouts: tuple, the timeout limit for two actions.

        Returns:

            a tuple, containing the following item:
            ChunckedData or None: the player inherit the police
            ChunckedData or None: the comment of the player
        """
        self.alive = False
        ret = []
        if self.police:
            packet = self._getBasePacket()
            packet['prompt'] = "Please select the player you want to inherit the police:"
            packet['timeLimit'] = timeouts
            packetSend = ChunckedData(7, **packet)
            sendingThread = Thread(
                target=packetSend.send, args=(self.socket, ))
            sendingThread.start()
            ret.append(self._startListening(timeout=timeouts))
        else:
            ret.append(None)
        if withFinalWords:
            packet = self._getBasePacket()
            packet['timeLimit'] = timeouts
            packetSend = ChunckedData(6, **packet)
            sendingThread = Thread(
                target=packetSend.send, args=(self.socket, ))
            sendingThread.start()
            ret.append(self._startListening(timeout=timeouts))
        else:
            ret.append(None)
        return tuple(ret)


class Villager(Person):
    """
    Villager, player without any additional skills.

    Attributes and methods are inherited from class Person
    """

    def __init__(self, id: int, connection: socket.socket):
        super().__init__(id, connection)
        self.type = 0


class Wolf(Person):
    """
    Werewolves, can wake up at night to kill someone.

    Attributes:

        Some attributes are inherited from class Person without modification

        innocent: bool, inherited from class Person, but initialized to False
        peerList: list, other wolves in the game

    Methods:

        Some methods are inherited from class Person without modification

        setPeer(): used for the server to add other wolves to the list
        removePeer(): used for the server to remove a wolf when it's killed
        kill(): ask the client to kill a player
    """

    def __init__(self, id: int, connection: socket.socket):
        """
        Initialization method inherited from class Person
        """
        super().__init__(id, connection)
        self.innocent = False
        self.type = -1
        self.peerList: List[Wolf] = []

    def setPeer(self, peer):
        """
        Add a wolf to the list
        """
        self.peerList.append(peer)

    def removePeer(self, peer):
        """
        Remove a wolf from the list
        """
        self.peerList.remove(peer)

    def kill(self, timeout: float = defaultTimeout) -> Optional[ReceiveThread]:
        """
        Wolves communicate with each other and specifying the victim

        Parameters:

            timeout: float, time to wait for the client

        Returns:

            receiveThread, the thread receiving from the client
        """
        packet = self._getBasePacket()
        packet['format'] = "int"
        packet['prompt'] = "Please select a person to kill.\nYou have %f seconds to decide with your partner" % (
            timeout, )
        packet['timeLimit'] = timeout
        packet['iskill'] = True
        packetSend = ChunckedData(3, **packet)
        sendingThread = Thread(target=packetSend.send,
                               args=(self.socket,))
        sendingThread.start()
        timer = TimeLock(timeout)
        timer.setDaemon(True)
        timer.start()
        recv: Optional[ReceiveThread] = None
        recv = self._startListening(timeout)
        while not timer.getStatus():
            if recv.getResult() is None:
                continue
            elif recv.getResult().type == -3:
                return recv
            elif recv.getResult().type == 5:
                packet: dict = recv.getResult().content.copy()
                recv = self._startListening(timeout)
                packet.pop('type')
                for peer in self.peerList:
                    packet.update(**peer._getBasePacket())
                    packetSend = ChunckedData(5, **packet)
                    thread = Thread(target=packetSend.send,
                                    args=(peer.socket, ))
                    thread.start()
        return recv


class SkilledPerson(Person):
    """
    Villiagers with skills. Some skill could be used only once, but some can use indefinitely.

    Attributes:

        used: int, if the value is True, the player can no longer use the ability

    Methods:

        skill(): ask a player to use his ability.
        postSkill(): set ability availibity.
    """

    def __init__(self, id: int, connection: socket.socket):
        """
        Initialization method inherited from class Person
        """
        super(SkilledPerson, self).__init__(id, connection)
        self.used: int = 0

    def postSkill(self, increment=1):
        """
        Sets the used attribute of the player to True
        """
        self.used += increment

    def skill(self, prompt: str = "", timeout: float = defaultTimeout, format: str = "int") -> ReceiveThread:
        """
        Ask the player whether to use the skill

        Parameters:

            timeout: float, time to wait for the client
            format: the accepted parameter type

        Returns:

            receiveThread, the thread receiving from the client
        """
        packet = self._getBasePacket()
        packet['format'] = format
        packet['prompt'] = prompt
        packet['timeLimit'] = timeout
        packet['iskill'] = False
        packetSend = ChunckedData(3, **packet)
        sendingThread = Thread(target=packetSend.send,
                               args=(self.socket, ))
        sendingThread.start()
        return self._startListening(timeout)


class KingOfWerewolves(Wolf, SkilledPerson):
    """
    King of werewolves, can kill a person when not being poisoned.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(KingOfWerewolves, self).__init__(id, connection)
        self.type = -3

    def skill(self, timeout: float = defaultTimeout):
        prompt = """Please select a person to kill.
you have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class WhiteWerewolf(Wolf, SkilledPerson):
    """
    White werewolf, can kill a person at day.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(WhiteWerewolf, self).__init__(id, connection)
        self.type = -2

    def skill(self, timeout: float = defaultTimeout):
        prompt = """Please select a person to kill.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Predictor(SkilledPerson):
    """
    Perdictor, can observe a player's identity at night.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(Predictor, self).__init__(id, connection)
        self.type = 1

    def skill(self, timeout: float = defaultTimeout):
        prompt = """Please select a person to inspect his identity.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Witch(SkilledPerson):
    """
    Witch, can kill a person or save a person at night.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(Witch, self).__init__(id, connection)
        self.type = 2

    def skill(self, killed: int = 0, timeout: float = defaultTimeout):
        packet = self._getBasePacket()
        if self.used % 2 == 1:
            killed = 0
        packet['content'] = "The player %s is killed at night." % (
            str(killed) if killed else "unknown", )
        packetSend = ChunckedData(5, **packet)
        if self.used == 0:  # Not ever used
            prompt = """Please select a person to use the poison. If you want to save the killed player %d, enter "0".
You have %f seconds to decide.""" % (killed, timeout)
        elif self.used == 1:  # Saved somebody.
            prompt = """Please select a person to use the poison. You have %f seconds to decide.""" % (
                timeout, )
        elif self.used == 2:  # Killed somebody
            prompt = """If you want to save the killed player %d, enter "0".\nYou have %f seconds to decide.""" % (killed,
                                                                                                                   timeout)
        else:
            return None
        return SkilledPerson.skill(self, prompt, timeout, "int")


class Hunter(SkilledPerson):
    """
    Hunter, can kill a person when not being poisoned.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(Hunter, self).__init__(id, connection)
        self.type = 3

    def skill(self, timeout: float = defaultTimeout):
        prompt = """Please select a person to kill.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Guard(SkilledPerson):
    """
    Guard, can guard a person to avoid him being killed.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(Guard, self).__init__(id, connection)
        self.type = 4

    def skill(self, timeout: float = defaultTimeout):
        prompt = """Please select a person to guard.
You have %f seconds to decide.""" % (timeout, )
        return SkilledPerson.skill(self, prompt, timeout)


class Idiot(SkilledPerson):
    """
    Idiot, avoid from dying when being exiled.

    Attributes and methods are inherited from class SkilledPerson.
    """

    def __init__(self, id: int, connection: socket.socket):
        super(Idiot, self).__init__(id, connection)
        self.type = 5

    def skill(self):
        """
        The skill() of class Idiot should not be called outside the class
        """
        self.postSkill()

    def onDead(self, killedAtNight, withFinalWords, timeouts):
        if killedAtNight or self.used:
            return super().onDead(withFinalWords, timeouts)
        else:
            self.skill()
            return None
