from abstraction import *
from random import shuffle, randint
from WP import ChunckedData
from threading import Thread
from util import getIdentityCode, getBasePacket

class Game():

    def __init__(playerCount: int):
        self.playerCount = playerCount
        self.activePlayer = {}
        self.ports = list(range(50000, 50000 + playerCount + 1))
        self.running = False
        self.identityList = {}

    def activate(self):
        self.running = True

    def deactivate(self):
        self.running = False

    def addAddr(self, idclient: int, recport: int, recip: str):
        self.identityList['%d port'% idclient] = recport
        self.identityList['%d ip'% idclient] = recip

    def allocateIdentity(self, server: tuple):
        playercount = self.playerCount
        idList = self.identityList
        idused = []
        for i in range(1, playercount + 1):
            #choose the id of client randomly
            idclient = randint(1, playercount + 1)
            while idclient in idused:
                idclient = randint(1, playercount + 1)
            idused.append(idclient)
            #allocate the identity
            if (i <= int(playercount / 3 + 0.5)):
                self.identityList['%d identity'% idclient] = 'wolf'
                self.identityList['%d client'% idclient] = Wolf(idclient, (idList['%d ip'], idList['%d port']), server)
            elif (i <= 2 * int(playercount / 3 + 0.5)):
                cut = int(playercount / 3 + 0.5)
                if (i == cut + 1):
                    self.identityList['%d identity'% idclient] = 'predictor'
                    self.identityList['%d client'% idclient] = Predictor(idclient, (idList['%d ip'], idList['%d port']), server)
                if (i == cut + 2):
                    self.identityList['%d identity'% idclient] = 'witch'
                    self.identityList['%d client'% idclient] = Witch(idclient, (idList['%d ip'], idList['%d port']), server)
                if (i == cut + 3):
                    self.identityList['%d identity'% idclient] = 'hunter'
                    self.identityList['%d client'% idclient] = Hunter(idclient, (idList['%d ip'], idList['%d port']), server)
                if (i == cut + 4):
                    self.identityList['%d identity'% idclient] = 'guard'
                    self.identityList['%d client'% idclient] = Guard(idclient, (idList['%d ip'], idList['%d port']), server)
            else:
                self.identityList['%d identity'% idclient] = 'villager'
                self.identityList['%d client'% idclient] = Villager(idclient, (idList['%d ip'], idList['%d port']), server)

    def tellIdentity(self):
        playercount = self.playerCount
        idList = self.identityList
        for i in range(1, playercount + 1):


    def addPlayer(self, data: ChunckedData):
        assert self.running == False
        assert data.content['type'] == 2
        assert len(identityList) != 0
        server = data.getAddr('destination')
        client = data.getAddr('source')
        id = data.content['chosenSeat']
        if id in range(1, self.playerCount + 1) and id not in self.activePlayer.keys():
            self.activePlayer[id] = self.identityList.pop()(id=id, server=server, client=client)
        else:
            id = randint(1, self.playerCount)
            while id in self.activate.keys():
                id = randint(1, self.playerCount)
            self.activePlayer[id] = self.identityList.pop()(id=id, server=server, client=client)
        identity = getIdentityCode(self.activePlayer[id])
        packet = getBasePacket(server, client)
        packet['success'] = True
        packet['chosenSeat'] = id
        packet['identity'] = identity
        sendingThread = Thread(target=ChunckedData(-2, **packet).send(), args=(self.activePlayer[id].socket, ))
        sendingThread.start()

class IncomingConnection(Thread):

    def __init__(self, addr: tuple, dest: Game):
        super(EstablishConnThread, self).__init__()
        self.result = None
        self.address = addr

    def run(self):