from ..abstraction import *
from random import shuffle, randint
from ..WP import ChunckedData, _recv
from threading import Thread
from .util import *
from typing import Tuple
from itertools import groupby


class Game:
    """
    # Game - the main class for game logic

    class Game implements the communication process and the whole game process. Provides interfaces for customizing a game.

    ## Attributes

    - playerCount : `int`,                the number of the players
    - allPlayer   : `dict`,               the number and the identity of all player.
    - activePlayer: `dict`,               the number and the identity of remaining player.
    - Key         : `int`,                the identification number of each player (or you can say seat number)
    - Value       : `Any`,                the identity of each player, should be a class in `abstraction.py`
    - ports       : `list`,               the ports available for communication with the player
    - running     : `bool`,               the status of the game, can set to `True` when the `identityList` is empty and the length of `activePlayer` equals with `playerCount`
    - identityList: `list`,               used when allocating the user identity
    - listener    : `IncomingConnection`, the thread for receiving handshakes

    ## Methods

    - `__init__()`: Initialize a new game class
    - `startListening()`: Starts listening for clients
    - `activate()`: Set the `running` attribute to `True` to prevent further modification
    - `deactivate()`: Set the `running` attribute to `False` to prevent further modification
    - `setIdentityList()`: Generate an identity configuration according to the given parameter
    - `addPlayer()`: add a player to the game after receiving a packet
    - `checkStatus()`: Check whether the stopping criterion is triggered
      - Stopping criterion: either werewolves, villagers, skilled villagers are all eliminated
    - ``
    """

    def __init__(self, ip: str, port: int, playerCount: int):
        """
        Initializa a new game

        ### Parameter

        - ip: `str`, the IP address of the server
        - port: `int`, the port of the server, used for listening to the incoming connection
        - playerCount: `int`, the number of players in a game

        ### Return

        A `Game` object
        """

        # Attribute initialization
        self.playerCount: int = playerCount
        self.allPlayer: dict = {}
        self.activePlayer: dict = {}
        self.listeningAddr: Tuple[str, int] = (ip, port)
        self.ports: List[int] = list(range(port + 1, port + playerCount + 2))
        self.running: bool = False
        self.identityList: list = []
        self.listener: IncomingConnection = IncomingConnection(
            self.listeningAddr, self)
        # Further initialization
        self.listener.setName("Incoming connection receiver")

        # Game parameters
        self.day: int = 0
        self.night: int = 0
        self.police = None

        self.victim: List[int] = []
        self.guardedLastNight: int = 0
        self.hunterStatus: bool = True
        self.kingofwolfStatus: bool = True
        # Verbose
        print("Server port: ", ", ".join([str(_) for _ in self.ports]))

    def startListening(self):
        """
        Start listening for clients before the game starts. Must be called when the server is not listening.

        The thread would automatically stop when there are enough players.

        ### Parameter

        None

        ### Return

        None
        """
        assert (
            self.identityList
        ), "The identity list must be initialized"  # The identity list should not be empty
        assert self.listener.is_alive() == False, "There is already an active listener"
        self.listener.start()

    def activate(self):
        """
        Activate the game

        The game must have enough players and have already allocated the identities.
        """
        assert (
            self.listener.is_alive() == False
        ), "The game should not be waiting for players to join"
        assert not self.identityList, "Identity not fully allocated"
        assert (
            len(self.activePlayer) == self.playerCount
        ), "The number of players is not enough"
        self.running = True  # 激活游戏，不允许新的玩家进入

    def deactivate(self):
        self.running = False  # 游戏结束

    def checkStatus(self) -> int:
        """
        Check whether the game should be stopped

        ### Parameter

        None

        ### Return

        An `int` integer, value falls in `-1`, `0` and `1`

        - `-1`: The game stops and the werewoles win - either villagers or skilled villagers are eliminated
        - `0`: The game continues
        - `1`: The game stops and the villagers win - the wolves are eliminated
        """
        numVillager, numSkilled, numWolf = 0, 0, 0
        for player in self.activePlayer:
            if isinstance(self.activePlayer[player], Villager):
                numVillager += 1
            elif isinstance(self.activePlayer[player], Wolf):
                numWolf += 1
            else:
                numSkilled += 1
        if numSkilled > 0 and numVillager > 0 and numWolf > 0:
            return 0
        elif numWolf == 0:
            return 1
        else:
            return -1

    def broadcast(self, srcPlayer, content: str):
        """
        Send a packet to all the players except the `srcPlayer` (if not `None`)

        ### Parameters

        - srcPlayer: the player to skip
        - content: the content of the announcement

        ### Return

        None
        """
        for id in self.activePlayer:
            player = self.activePlayer[id]
            if player == srcPlayer:
                continue
            player.inform(content)

        # !SECTION

    def setIdentityList(self, **kwargs):
        """
        Initialize the identity configuration.

        ### Parameter

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

        ### Return

        None
        """
        self.identityList = []
        assert "Villager" in kwargs, "The `Villager` parameter is required"
        assert "Wolf" in kwargs, "The `Wolf` parameter is required"
        for identity in kwargs:
            assert identity in availableIdentity
            if identity in uniqueIdentity:
                assert kwargs[identity] <= 1, "There should be at most 1 " + identity
            else:
                assert kwargs[identity] >= 1, "There should be at least 1 " + identity
            for i in range(kwargs[identity]):
                # eval(identity) returns a class
                self.identityList.append(eval(identity))
        shuffle(self.identityList)

    def addPlayer(self, data: ChunckedData):
        """
        The server add a player to game after receiving a choose seat request.

        ### Parameter

        - data: data packet received.

        ### Return

        None
        """
        assert self.running is False
        assert data.content["type"] == 1  # The packet type must match
        # `identityList` must be initialized
        assert len(self.identityList) != 0
        # Read the content of the packet
        # Verify the seat is available
        client: Tuple[str, int] = data.getAddr("source")
        id: int = data.content["chosenSeat"]
        # Randomly allocate seat when the seat chosen is already taken
        if id not in range(1, self.playerCount + 1) or id in self.activePlayer.keys():
            id = randint(1, self.playerCount)
            while id in self.activate.keys():
                id = randint(1, self.playerCount)
        server: Tuple[str, int] = (data.getAddr(
            "destination")[0], self.ports[id])
        newplayer = self.identityList.pop()(id=id, server=server, client=client)
        self.activePlayer[id] = newplayer
        self.allPlayer[id] = newplayer
        # Send response
        identityCode: int = getIdentityCode(self.activePlayer[id])
        packet: dict = getBasePacket(server, client)
        packet["success"] = True
        packet["chosenSeat"] = id
        packet["identityCode"] = identityCode
        sendingThread: Thread = Thread(
            target=ChunckedData(-1, **
                                packet).send, args=(self.activePlayer[id].socket,)
        )
        sendingThread.start()

    def electPolice(self):
        """
        Implements the game logic before day. Workflow:

        - Elect for police (only the first day)
        - The candidate talks in sequence (only the first day)
          - The candidate could not quit the election, which is different from the offline version.
        - Vote for police (only the first day)
          - If a wolf explodes in the election period, the server announces the victim and switch to night immediately. The vote is delayed to the next day. Explosion of another wolf at this time will make the police does not exist.
          - If there are two or more candidates get the same vote, they are required to talk in sequence again. If two or more candidates get the same vote once again, the police does not exist in the game.

        ### Parameter

        None

        ### Return

        The police elected. If a wolf explodes, returns None.
        """

        # Ask for election
        electionCandidate = [(player, player.joinElection())
                             for player in self.activePlayer]
        for player, recthread in electionCandidate:
            recthread.join()
        candidate: list = []
        for player, recthread in electionCandidate:
            if recthread.getResult() is not None and recthread.getResult().content['action']:
                candidate.append(player)
        current: ReceiveThread

        # Candidate talk in sequence
        for i in range(2):
            """
            Vote for the police

            Loop variable: i - only a counter
            """
            for player in candidate:
                current = player.speak()
                current.join()
                self.broadcast(player, current.getResult().content['content'])

            # Ask for vote
            voteThread: List[ReceiveThread] = []
            for player in self.activePlayer:
                if player in candidate:
                    continue  # Candidate cannot vote
                voteThread.append(player.voteForPolice)
            for thread in voteThread:
                thread.join()

            # Get the result and count the vote
            vote: list = []
            packetContent: dict = {}
            for thread in voteThread:
                if thread.getResult() is None:
                    continue
                packetContent = thread.getResult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    vote.append(packetContent['candidate'])
            result: List[int] = getVotingResult(vote)

            del voteThread
            del vote
            del packetContent

            if (len(result) == 1):
                self.broadcast(None, "The police is player %d" % (result[0], ))
                self.police = self.activePlayer[result[0]]
                return None
            else:
                self.broadcast(
                    None,
                    "Another election is needed, candidates are %s" % ", ".join(
                        [str(_) for _ in result]
                    )
                )
                candidate.clear()
                candidate = [self.activePlayer[_] for _ in result]
        self.police = None
        return None

    def victimSkill(self):
        for id in self.victim:
            victim = self.allPlayer[id]
            victim.onDead(True if self.night == 1 or self.day ==
                          self.night else False, default_timeout())
            if isinstance(victim, Hunter) or isinstance(victim, KingOfWerewolves):
                if (self.hunterStatus and isinstance(victim, Hunter)) \
                        or (self.kingofwolfStatus and isinstance(victim, KingOfWerewolves)):
                    gunThread = victim.skill()
                    gunThread.join()
                    packetContent: dict = gunThread.getResult().content
                    if packetContent['action'] and packetContent['target'] in self.activePlayer:
                        self.broadcast(None, "the player %d has been killed by the player %d"
                                       % (packetContent['target'], id))
                        # TODO kick the player out
                        status = self.checkStatus()
                        if status != 0:
                            return status
                        victim.onDead(True, default_timeout())
                    else:
                        victim.inform(
                            "you didn't choose the target or you choose the wrong number!")
                else:
                    victim.inform("you can't open the gun!")
        # reset the status of the gun
        self.hunterStatus = True
        self.kingofwolfStatus = True

    def dayTime(self) -> int:
        """
        # Implements the game logic in daytime. Workflow:
        - Announce the victim
          - If the king of werewolves or the hunter is killed by the wolves, ask them
          - If the police exists - randomly choose a side from the police
          - If the police does not exist - randomly choose a side from the victim
          - If no or two players died at night - randomly choose a side from the police (if exist)
        - The player talks in sequence
          - If a wolf explodes, the game switch to the night at once after the wolf talks.
        - Vote for the victim
          - If there are same vote, players with the same vote talk again and vote again. If the same situation appears again, there will be no victim in day.
        - Announce the exile
          - If the exile is an idiot not voted out before, it can escape from death. But the idiot can no longer vote.

        ### Return

        An `int` integer, value falls in `-1`, `0` and `1`

        - `-1`: The game stops and the werewoles win - either villagers or skilled villagers are eliminated
        - `0`: The game continues
        - `1`: The game stops and the villagers win - the wolves are eliminated
        """
        # ANCHOR: Implement the game logic in daytime

        startpoint: int = 0
        exile: list = []

        # announce the victim and check the game status
        if len(self.victim) == 0:
            self.broadcast(None, "last night is safe")
        else:
            self.broadcast(None, "the victim last night is player: %s" %
                           ", ".join(str(s) for s in self.victim))
        status = self.checkStatus()
        if status != 0:
            return status
        # ask if the victim want to use the skill
        if len(self.victim) > 0:
            self.victimSkill()

        # ask the police (if exists) to choose the talking sequence
        talkSequence: list[int] = []
        isClockwise: bool = True
        if len(self.victim) == 0:
            i = 0
            for id in self.activePlayer:
                if i == 0:
                    startpoint = id
                if id > self.victim.pop():
                    startpoint = id
                i += 1
        else:
            startpoint = self.victim[0]

        if self.police is not None:
            police = self.activePlayer[self.police]
            policeThread = police.policeSetseq()
            policeThread.join()
            packetContent: dict = policeThread.getResult().content
            if packetContent['clockwise'] == False:
                isClockwise = False

        talkSequence = self.setSeq(startpoint, isClockwise)

        # active player talk in sequence
        for i in range(2):
            """
            Vote for the exile

            Loop variable: i - only a counter
            """
            for id in talkSequence:
                player = self.activePlayer['%d' % id]
                current = player.speak()
                current.join()
                self.broadcast(player, current.getResult().content['content'])

            # Ask for vote
            voteThread: List[ReceiveThread] = []
            for id in self.activePlayer:
                if id != self.police:
                    voteThread.append(self.activePlayer[id].vote())
            for thread in voteThread:
                thread.join()
            # police vote is special case
            policevote = None
            if self.police is not None:
                policevoteThread = self.activePlayer[self.police].vote()
                policevoteThread.join()
                packetContent = policevoteThread.getTesult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    policevote = packetContent['candidate']

            # Get the result and count the vote
            # TODO: IDIOT
            vote: list = []
            packetContent: dict = {}
            for thread in voteThread:
                if thread.getResult() is None:
                    continue
                packetContent = thread.getResult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    vote.append(packetContent['candidate'])
            result: List[int] = getVotingResult(vote, policevote)

            del voteThread
            del vote
            del packetContent

            exile = []
            if (len(result) == 1):
                self.broadcast(None, "The exile is player %d" % (result[0],))
                exile = self.activePlayer[result[0]]
                return None
            else:
                self.broadcast(
                    None,
                    "Another election is needed, exile candidates are %s" % ", ".join(
                        [str(_) for _ in result]
                    )
                )
                exile.clear()
                exile = [self.activePlayer[_] for _ in result]

        # announce the exile and check the game status
        if len(exile) == 0:
            self.broadcast(None, "no one exile!")
        else:
            self.broadcast(None, "the exile player is: %s" %
                           ", ".join(str(s) for s in self.victim))
        status = self.checkStatus()
        if status != 0:
            return status
        # ask if the victim want to use the skill
        if len(self.victim) > 0:
            self.victimSkill()

    def setSeq(self, startpoint: int, clockwise: bool):
        """

        - startpoint: the person id to start with
        - clockwise: True means clockwise, False means anti-clockwise

        - return: seq: list[int]
        """
        seq = []
        tempActive = []
        for id in self.activePlayer:
            tempActive.append(id)
        if clockwise == False:
            tempActive = tempActive.reverse()
        for i in range(0, len(tempActive)):
            if i > tempActive.index(startpoint):
                seq.append(tempActive.pop(i))
        seq += tempActive

        return seq

    def nightTime(self):
        """
        Implements the game logic at night. Workflow:

        - Wolves wake up to kill a person. The server should inform a player his peers.
        - The witch wakes up to kill a person or save a person
          - After the witch has saved a person, it would no longer knows the victim at night
          - The witch can only use a bottle of potion at night.
          - The witch can only save herself in the first night.
        - The predictor wakes up and check the identity of another player.
        - The guard wakes up, choose to guard a player at night.
          - The guard cannot guard a player in two consecutive nights.
        - The hunter wakes up. The server inform the skill status. (If not killed by the witch)
        """
        # SECTION: Implement the game logic at night

        # Parameters:
        victimByWolf: int = 0
        victimByWitch: int = 0
        predictorTarget: int = 0
        guardTarget: int = 0
        hunterStatus: bool = True

        # ANCHOR: Wolves wake up
        # Vote for a player to kill

        wolfThread: List[ReceiveThread] = []

        for player in self.activePlayer:
            if isinstance(player, (Wolf, KingOfWerewolves, WhiteWerewolf)):
                ret: Optional[ReceiveThread] = player.kill()
                if ret is not None:
                    wolfThread.append(ret)
        if wolfThread:  # Only used for indention
            for thread in wolfThread:
                thread.join()

            vote: List[int] = []
            packetContent: dict = {}

            for thread in wolfThread:
                if thread.getResult() is None:
                    continue
                packetContent: dict = thread.getResult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    vote.append(packetContent['candidate'])

            result: List[int] = getVotingResult(vote)

            # If there are more than 1 victim, randomly choose one
            shuffle(result)
            victimByWolf = result[0]

            del vote
            del packetContent
            del result
        del wolfThread

        # ANCHOR: Predictor wake up
        # The predictor ask for a player's identity

        predictorThread: Optional[ReceiveThread] = None
        predictor: Optional[Predictor] = None

        for player in self.activePlayer:
            if isinstance(player, Predictor):
                predictor = player
                predictorThread = player.skill()
        if predictor is not None and predictorThread is not None:
            packetContent: dict = predictorThread.getResult().content
            if packetContent['action'] and packetContent['target'] in self.activePlayer:
                predictorTarget = packetContent['target']

            # Notice: the server need to send a response here, and the packet type is -3
            # The 'action' field is the identity of the target.

            packetContent.update(**predictor._getBasePacket())
            packetContent['action'] = getIdentityCode(
                self.activePlayer[predictorTarget]) >= 0
            sendingThread: Thread = Thread(
                target=ChunckedData(-1, **
                                    packetContent).send, args=(predictor.socket,)
            )
            sendingThread.start()
            del packetContent
        del predictorThread

        # ANCHOR: Witch wake up
        # Witch can save or kill a person

        witchThread: Optional[ReceiveThread] = None
        witch: Optional[Witch] = None

        for player in self.activePlayer:
            if isinstance(player, Witch):
                witch = player
                witchThread = player.skill(killed=victimByWolf)
                # witchThread.join()
        if witch is not None and witchThread is not None:
            """
            Got the response
            """
            packetContent: dict = witchThread.getResult().content
            if packetContent['action']:
                """
                If the witch takes the action
                """
                if not isinstance(self.activePlayer[packetContent['target']], Witch) or self.night == 0:
                    """
                    The witch cannot save herself after the first night.
                    """
                    if packetContent['target'] == 0 and witch.used % 2 == 0:
                        victimByWolf *= -1  # wait for guard
                        witch.used += 1
                    elif packetContent['target'] in self.activePlayer and witch.used < 2:
                        victimByWitch = packetContent['target']
                        witch.used += 2
            del packetContent
        del witchThread

        # ANCHOR: Guard wake up
        # Guard protects a player, prevent him from dying from wolves.

        guardThread: Optional[ReceiveThread] = None
        guard: Optional[Guard] = None

        for player in self.activePlayer:
            if isinstance(player, Guard):
                guard = player
                guardThread = player.skill()
        if guard is not None and guardThread is not None:
            packetContent: dict = guardThread.getResult().content
            if packetContent['action']:
                if packetContent['target'] in self.activePlayer:
                    guardTarget = packetContent['target']
                    # Cannot save the same player in 2 days.
                    if (guardTarget != self.guardedLastNight):
                        victimByWolf *= -1 if guardTarget + victimByWolf == 0 else 1
                        # the situation when guard and save the same person

            del packetContent
        del guardThread

        # ANCHOR: Hunter wake up
        # The server checks the usablity of the skill

        self.hunterStatus = not isinstance(
            self.activePlayer[victimByWitch], Hunter
        )
        self.kingofwolfStatus = not isinstance(
            self.activePlayer[victimByWitch], KingOfWerewolves
        )

        # ANCHOR: Return the value
        self.victim.clear()
        if victimByWitch:
            self.victim.append(victimByWitch)
        if victimByWolf > 0:
            self.victim.append(victimByWolf)
        shuffle(self.victim)
        for id in self.victim:
            self.activePlayer.pop(id)

        if self.guardedLastNight != guardTarget:
            self.guardedLastNight = guardTarget
        else:
            self.guardedLastNight = 0

        self.night += 1


class IncomingConnection(Thread):
    """
    Create a thread that receives a handshake package.

    `Establish` packets and `EstablishResp` packets are no longer used. The server sends the port information in this packet.
    """

    def __init__(self, addr: Tuple[str, int], dest: Game):
        super(IncomingConnection, self).__init__()
        self.address: Tuple[str, int] = addr
        self.game: Game = dest

    def run(self):
        receivingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        receivingSocket.bind(self.address)
        while self.game.playerCount != len(self.game.activePlayer):
            self.game.addPlayer(_recv(receivingSocket))
