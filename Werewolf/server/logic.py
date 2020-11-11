from ..abstraction import *
from random import shuffle, randint
from ..WP import ChunckedData, _recv
from threading import Thread
from .util import *


class Game():
    """
    # Game - the main class for game logic

    class Game implements the communication process and the whole game process. Provides interfaces for custimizing a game.

    ## Attributes

    - playerCount : `int`,                the number of the players
    - activePlayer: `dict`,               the number and the identity of remaining player.
    - Key         : `int`,                the identification number of each player
    - Value       : `Any`,                the identity of each player, should be a class in `abstraction.py`
    - ports       : `list`,               the ports available for communication with the player
    - running     : `bool`,               the status of the game, can set to `True` when the `identityList` is empty and the length of `activePlayer` equals with `playerCount`
    - identityList: `list`,               used when allocating the user identity
    - listner     : `IncomingConnection`, the thread for receiving handshakes

    ## Methods

    `__init__(self, ip: str, port: int, playerCount: int)`
    """

    def __init__(self, ip: str, port: int, playerCount: int):
        """
        Initializa a new game

        ### Parameters:

        - ip: `str`, the IP address of the server
        - port: `int`, the port used for listending to the incoming connection
        - playerCount: `int`, the number of players in a game

        ### Returns:

        A `Game` object
        """

        # Attribute initialization
        self.playerCount = playerCount
        self.activePlayer = {}
        self.listeningAddr = (ip, port)
        self.ports = list(range(port + 1, port + playerCount + 2))
        self.running = False
        self.identityList = []
        self.listener = IncomingConnection(self.listeningAddr, self)
        # Further initialization
        for i in range(1, self.playerCount + 1):
            self.messageQueue[i] = []
        self.listener.setName("Incoming connection receiver")
        # Verbose
        print("Server port: ", ", ".join(self.ports))

    def startListening(self):
        """
        Start listening for clients before the game starts. Must be called when the server is not listening.

        The thread would automatically stop when there are enough players.

        ### Parameters:

        None

        ### Returns:

        None
        """
        assert self.identityList  # The identity list should not be empty
        assert self.listener.is_alive() == False
        self.listener.start()

    def activate(self):
        """
        Activate the game

        The game must have enough players and have already allocated the identities.
        """
        assert self.listener.is_alive() == False
        assert not self.identityList
        assert len(self.activePlayer) == self.playerCount
        self.running = True  # 激活游戏，不允许新的玩家进入

    def deactivate(self):
        self.running = False  # 游戏结束

    def setIdentityList(self, **kwargs):
        """
        Initialize the identity configuration.

        ### Parameters:

        - Villager      : `int`, REQUIRED, the number of villagers
        - Wolf          : `int`, REQUIRED, the number of wolves
        - KingofWerewolf: `int`, optional, the number of kings of werewolves
        - WhiteWerewolf : `int`, optional, the number of white werewolves
        - Predictor     : `int`, optional, the number of predictors
        - Witch         : `int`, optional, the number of witches
        - Hunter        : `int`, optional, the number of hunters
        - Guard         : `int`, optional, the number of guards
        - Idiot         : `int`, optional, the number of idiots

        The value of `Villager` and `Wolf` parameter should be **at least** 1, and values of the other parameters should be **at most** 1.

        ### Returns:

        None
        """
        self.identityList = []
        assert "Villager" in kwargs
        assert "Wolf" in kwargs
        for identity in kwargs:
            assert identity in availableIdentity
            if identity in uniqueIdentity:
                assert kwargs[identity] <= 1
            else:
                assert kwargs[identity] >= 1
            for i in range(kwargs[identity]):
                # eval(identity) returns a class
                self.identityList.append(eval(identity))
        shuffle(self.identityList)

    def addPlayer(self, data: ChunckedData):
        """
        The server add a player to game after receiving a choose seat request.

        ### Parameters:

        - data: data packet received.

        ### Returns:

        None
        """
        assert self.running == False
        assert data.content['type'] == 2  # The packet type must match
        # `identityList` must be initialized
        assert len(self.identityList) != 0
        # Read the content of the packet
        server = data.getAddr('destination')
        client = data.getAddr('source')
        id = data.content['chosenSeat']
        # Verify the seat is available
        if id in range(1, self.playerCount + 1) and id not in self.activePlayer.keys():
            self.activePlayer[id] = self.identityList.pop()(
                id=id, server=server, client=client)
        else:   # Randomly allocate seat when the seat chosen is already taken
            id = randint(1, self.playerCount)
            while id in self.activate.keys():
                id = randint(1, self.playerCount)
            self.activePlayer[id] = self.identityList.pop()(
                id=id, server=server, client=client)
        # Send response
        identity = getIdentityCode(self.activePlayer[id])
        packet = getBasePacket(server, client)
        packet['success'] = True
        packet['chosenSeat'] = id
        packet['identity'] = identity
        sendingThread = Thread(
            target=ChunckedData(-2, **packet).send, args=(self.activePlayer[id].socket, ))
        sendingThread.start()


class IncomingConnection(Thread):
    """
    Create a thread that receives a handshake package.
    """

    def __init__(self, addr: tuple, dest: Game):
        super(IncomingConnection, self).__init__()
        self.address = addr
        self.game = dest

    def run(self):
        receivingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        receivingSocket.bind(self.address)
        while self.game.playerCount != len(self.game.activePlayer):
            self.game.addPlayer(_recv(receivingSocket))
