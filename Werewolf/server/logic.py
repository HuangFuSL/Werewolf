import ctypes
import threading
from random import randint, shuffle
from threading import Thread
from typing import Any, Callable, Dict, Tuple

from .abstraction import *
from ..WP import ChunckedData, _recv
from .util import *


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
        self.allPlayer: Dict[int, Any] = {}
        self.activePlayer: Dict[int, Any] = {}
        self.listeningAddr: Tuple[str, int] = (ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.listeningAddr)
        self.socket.listen(10)
        self.running: bool = False
        self.identityList: List[Any] = []
        self.listener: IncomingConnection = IncomingConnection(
            self.socket, self)
        # Further initialization
        self.listener.setName("Incoming connection receiver")

        # Game parameters
        self.day: int = 0
        self.night: int = 0
        self.status: int = 0

        self.victim: List[int] = []
        self.guardedLastNight: int = 0
        self.hunterStatus: bool = True
        self.kingofwolfStatus: bool = True
        # Verbose

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
        self.listener.join()

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
        assert self.status == 0, "The game is already finished"
        assert self.day == 0 and self.night == 0
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
            self.status = 0
            return 0
        elif numWolf == 0:
            self.status = 1
            return 1
        else:
            self.status = -1
            return -1

    def broadcast(self, srcPlayer: Any, content: str):
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
            if player is srcPlayer:
                continue
            player.inform(content)

    def setIdentityList(self, **kwargs: int):
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
                i + 1
        shuffle(self.identityList)

    def addPlayer(self, connection: socket.socket, data: ChunckedData):
        """
        The server add a player to game after receiving a choose seat request.

        ### Parameter

        - data: data packet received.

        ### Return

        None
        """
        assert self.running is False
        assert data.type == 1  # The packet type must match
        # `identityList` must be initialized
        assert len(self.identityList) != 0
        # Read the content of the packet
        # Verify the seat is available
        # Randomly allocate seat when the seat chosen is already taken
        id = randint(1, self.playerCount)
        while id in self.activePlayer.keys():
            id = randint(1, self.playerCount)
        newplayer = self.identityList.pop()(id=id, connection=connection)
        self.activePlayer[id] = newplayer
        self.allPlayer[id] = newplayer
        # Send response
        identityCode: int = getIdentityCode(self.activePlayer[id])
        # REVIEW: Print message here.
        print("The player %d get the %d identity" % (id, identityCode))
        packet: Dict[str, Any] = getBasePacket(
            newplayer.server, newplayer.client)
        packet["seat"] = id
        packet["identity"] = identityCode
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
        electionCandidate: List[Tuple[int, ReceiveThread]]
        electionCandidate = [(player, self.activePlayer[player].joinElection())
                             for player in self.activePlayer]
        for player, recthread in electionCandidate:
            recthread.join()
        candidate: List[int] = []
        for player, recthread in electionCandidate:
            if recthread.getResult() is not None and \
                    recthread.getResult().content['action'] and \
                    recthread.getResult().content['target']:
                candidate.append(player)
        current: ReceiveThread

        # Candidate talk in sequence
        for i in range(2):
            """
            Vote for the police

            Loop variable: i - only a counter
            """
            for player in candidate:
                current = self.activePlayer[player].speak()
                current.join()
                if current.getResult() is not None:
                    self.broadcast(
                        player,
                        "Player %d said" % (player,) +
                        current.getResult().content['content']
                    )

            # Ask for vote
            voteThread: List[ReceiveThread] = []
            thread: Optional[ReceiveThread] = None
            for player in self.activePlayer:
                if player in candidate:
                    continue  # Candidate cannot vote
                thread = self.activePlayer[player].voteForPolice()
                if thread:
                    voteThread.append(thread)
            del thread
            for thread in voteThread:
                thread.join()

            # Get the result and count the vote
            vote: List[int] = []
            packetContent: Dict[str, Any] = {}
            for thread in voteThread:
                if thread.getResult() is not None:
                    packetContent = thread.getResult().content
                else:
                    continue
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    vote.append(packetContent['candidate'])
            result: List[int] = getVotingResult(vote)

            del voteThread
            del vote
            del packetContent

            if (len(result) == 1):
                self.broadcast(None, "The police is player %d" % (result[0], ))
                self.activePlayer[result[0]].police = True
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
        self.broadcast(None, "No police in the game")
        return None

    def victimSkill(self):
        """
        After a player has died, the victim should take the following actions in sequence:

        - If police dies, he should decide the next police.
        - Anyone died during the day or the first night can have their last words.
        - If the guard or the king of werewolves dies and not dying from the poison, he can kill a person at this time.
        """
        for id in self.victim:
            victim = self.allPlayer[id]
            retMsg = victim.onDead(True if self.night == 1 or self.day ==
                                   self.night else default_timeout())
            if retMsg[0] and retMsg[0].content['vote'] and retMsg[0].content['candidate'] in self.activePlayer:
                self.activePlayer[retMsg[0].content['candidate']] = True
            if retMsg[1]:
                self.broadcast(None, retMsg[1].content['content'])
            if isinstance(victim, Hunter) or isinstance(victim, KingOfWerewolves):
                if (self.hunterStatus and isinstance(victim, Hunter)) \
                        or (self.kingofwolfStatus and isinstance(victim, KingOfWerewolves)):
                    gunThread = victim.skill()
                    gunThread.join()
                    if gunThread.getResult() is not None:
                        packetContent: Dict[str, Any]
                        packetContent = gunThread.getResult().content
                    else:
                        break
                    if packetContent['action'] and packetContent['target'] in self.activePlayer:
                        self.broadcast(None, "the player %d has been killed by the player %d"
                                       % (packetContent['target'], id))
                        self.activePlayer.pop(packetContent['target'])
                        status = self.checkStatus()
                        if status != 0:
                            return status
                        victim.onDead(True, default_timeout(None))
                    else:
                        victim.inform(
                            "you didn't choose the target or you choose the wrong number!")
                else:
                    victim.inform("you can't shoot the gun!")
        self.victim.clear()

    def dayTime(self) -> int:
        """
        Implements the game logic in daytime. Workflow:

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
        exile: List[int] = []

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
        talkSequence: List[int] = []
        isClockwise: bool = True
        packetContent: Dict[str, Any] = {}
        policeID: int = 0

        for player in self.activePlayer:
            """
            Find the police
            """
            if self.activePlayer[player].police:
                policeID = player

        startpoint = self.victim[0] \
            if len(self.victim) == 1 \
            else (policeID if policeID else min(self.activePlayer.keys()))

        # Police choose the direction
        if policeID:
            police = self.activePlayer[policeID]
            policeThread = police.policeSetseq()
            policeThread.join()
            isClockwise = policeThread.getResult().content['clockwise'] \
                if policeThread.getResult() is not None \
                else True

        talkSequence: List[int] = self.setSeq(startpoint, isClockwise)
        exile: List[int] = []

        # active player talk in sequence
        policeVoteThread: Optional[ReceiveThread] = None
        policeVote: Optional[int] = None
        for i in range(2):
            """
            Vote for the exile

            Loop variable: i - only a counter
            """
            for id in talkSequence:
                if id not in exile:
                    player = self.activePlayer[id]
                    current = player.speak()
                    current.join()
                    self.broadcast(
                        player, current.getResult().content['content'])

            # Ask for vote
            voteThread: List[ReceiveThread] = []
            for id in self.activePlayer:
                if isinstance(self.activePlayer[id], Idiot) and self.activePlayer[id].used:
                    """
                    An idiot cannot vote
                    """
                    continue
                if id != policeID:
                    voteThread.append(self.activePlayer[id].vote())
                else:
                    policeVoteThread = self.activePlayer[id].vote()

            for thread in voteThread:
                thread.join()
            if policeVoteThread is not None:
                policeVoteThread.join()
            if policeVoteThread is not None and policeVoteThread.getResult() is not None:
                packetContent = policeVoteThread.getResult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    policeVote = packetContent['candidate']

            # Get the result and count the vote
            vote: List[int] = []
            packetContent: Dict[str, Any] = {}
            for thread in voteThread:
                if thread.getResult() is None:
                    continue
                packetContent = thread.getResult().content
                if packetContent['vote'] and packetContent['candidate'] in self.activePlayer:
                    vote.append(packetContent['candidate'])
            result: List[int] = getVotingResult(vote, policeVote)

            del voteThread
            del vote
            del packetContent

            if (len(result) == 1):
                """
                Check the identity of the exiled. Idiot can escape from dying.
                """
                if not isinstance(self.activePlayer[result[0]], Idiot) or self.activePlayer[result[0]].used:
                    self.broadcast(
                        None, "The exiled is player %d" % (result[0],)
                    )
                    exile.append(result[0])
                else:
                    self.activePlayer[result[0]].used = 1
                    self.broadcast(
                        None, "Player %d is the idiot." % (result[0],)
                    )
                    exile.pop()
                break
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
        # REVIEW
        print(self.activePlayer)
        if len(exile) == 0:
            self.broadcast(None, "No one exile!")
        else:
            del self.activePlayer[exile[0]]
            self.victim.clear()
            self.victim.extend(exile)
            for id in self.victim:
                if id in self.activePlayer:
                    self.activePlayer.pop(id)
            self.broadcast(None, "the exile player is: %s" %
                           ", ".join(str(s) for s in self.victim))
        status = self.checkStatus()
        if status:
            return status
        # ask if the victim want to use the skill
        while self.victim:  # 极端情况可能会开两次枪
            self.victimSkill()
        status = self.checkStatus()
        return status

    def setSeq(self, startpoint: int, clockwise: bool) -> List[int]:
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
            tempActive.reverse()
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

        # REVIEW
        print("Night")

        # Parameters:
        victimByWolf: int = 0
        victimByWitch: int = 0
        predictorTarget: int = 0
        guardTarget: int = 0

        # ANCHOR: Wolves wake up
        # Vote for a player to kill

        wolfThread: List[ReceiveThread] = []

        for player in self.activePlayer:
            if isinstance(self.activePlayer[player], (Wolf, KingOfWerewolves, WhiteWerewolf)):
                ret: Optional[ReceiveThread] = self.activePlayer[player].kill()
                if ret is not None:
                    wolfThread.append(ret)
        if wolfThread:  # Only used for indention
            for thread in wolfThread:
                thread.join()

            vote: List[int] = []
            packetContent: Dict[str, Any] = {}

            for thread in wolfThread:
                if thread.getResult() is None:
                    continue
                packetContent = thread.getResult().content
                if packetContent['action'] and packetContent['target'] in self.activePlayer:
                    vote.append(packetContent['target'])

            result: List[int] = getVotingResult(vote)

            # If there are more than 1 victim, randomly choose one
            shuffle(result)
            victimByWolf = result[0] if result else 0

            del vote
            del packetContent
            del result
        del wolfThread

        # ANCHOR: Predictor wake up
        # The predictor ask for a player's identity

        predictorThread: Optional[ReceiveThread] = None
        predictor: Optional[Predictor] = None

        for player in self.activePlayer:
            if isinstance(self.activePlayer[player], Predictor):
                predictor = self.activePlayer[player]
                predictorThread = self.activePlayer[player].skill()
            if predictorThread:
                predictorThread.join()
        if predictor is not None and predictorThread is not None and predictorThread.getResult() is not None:
            packetContent: Dict[str, Any] = predictorThread.getResult().content
            if packetContent['action'] and packetContent['target'] in self.activePlayer:
                predictorTarget = packetContent['target']

            # Notice: the server need to send a response here, and the packet type is -3
            # The 'action' field is the identity of the target.

            packetContent.update(**predictor._getBasePacket())
            packetContent['action'] = getIdentityCode(
                self.activePlayer[predictorTarget]) >= 0
            packetContent['target'] = -1024
            sendingThread: Thread = Thread(
                target=ChunckedData(-3, **
                                    packetContent).send, args=(predictor.socket, predictor.client)
            )
            sendingThread.start()
            del packetContent
        del predictorThread

        # ANCHOR: Witch wake up
        # Witch can save or kill a person

        witchThread: Optional[ReceiveThread] = None
        witch: Optional[Witch] = None

        for player in self.activePlayer:
            if isinstance(self.activePlayer[player], Witch):
                witch = self.activePlayer[player]
                witchThread = witch.skill(
                    killed=victimByWolf
                )
                if witchThread:
                    witchThread.join()
        if witch is not None and witchThread is not None and witchThread.getResult() is not None:
            """
            Got the response
            """
            packetContent: Dict[int, Any] = witchThread.getResult().content
            if packetContent['action']:
                """
                If the witch takes the action
                """
                if packetContent['target'] == 0 or \
                        not isinstance(self.activePlayer[packetContent['target']], Witch) or \
                        self.night == 0:
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
            if isinstance(self.activePlayer[player], Guard):
                guard = self.activePlayer[player]
                guardThread = self.activePlayer[player].skill()
            if guardThread:
                guardThread.join()
        if guard is not None and guardThread is not None and guardThread.getResult is not None:
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

        if victimByWitch in self.activePlayer:
            self.hunterStatus = not isinstance(
                self.activePlayer[victimByWitch], Hunter
            )
            self.kingofwolfStatus = not isinstance(
                self.activePlayer[victimByWitch], KingOfWerewolves
            )

        # ANCHOR: Return the value
        self.victim.clear()
        if victimByWitch in self.activePlayer:
            self.victim.append(victimByWitch)
        if victimByWolf in self.activePlayer:
            self.victim.append(victimByWolf)
        shuffle(self.victim)
        for id in self.victim:
            self.activePlayer.pop(id)

        if self.guardedLastNight != guardTarget:
            self.guardedLastNight = guardTarget
        else:
            self.guardedLastNight = 0

        self.night += 1

    def preLaunch(self, addr: Tuple[str, int]):
        while self.identityList:
            ReceiveThread = IncomingConnection(self.socket, self)
            ReceiveThread.start()
            ReceiveThread.join()

    def launch(self):
        assert self.running, "The game must be activated!"
        while not self.status:
            self.nightTime()
            if self.day == 0:
                self.electPolice()
            self.dayTime()
        self.broadcast(
            None,
            "The villagers won" if self.status == 1 else "The wolves won"
        )


class IncomingConnection(Thread):
    """
    Create a thread that receives a handshake package.

    `Establish` packets and `EstablishResp` packets are no longer used. The server sends the port information in this packet.
    """

    def __init__(self, connection: socket.socket, dest: Game):
        super(IncomingConnection, self).__init__()
        self.socket = connection
        self.game: Game = dest

    def run(self):
        # REVIEW
        while self.game.playerCount != len(self.game.activePlayer):
            # REVIEW
            print("Listening for additional player...")
            c, addr = self.socket.accept()
            # REVIEW
            print(c.getpeername())
            print(c.getsockname())
            print("Client connected")
            self.game.addPlayer(c, _recv(c))


class killableThread(Thread):
    """
    A thread class extending threading.Thread, provides a kill() method to stop the thread and a getResult() method to get the return value of the thread.
    """

    def __init__(self, func: Callable, **kwargs):
        super().__init__()
        self.func: Callable = func
        self.funcArg: dict = kwargs
        self.result: Any = None

    def run(self):
        """
        Executes the function here
        """
        self.result = self.func(**self.funcArg)

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
        return self.result
