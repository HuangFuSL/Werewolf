#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from socket import *
from time import ctime
from abstraction import *
from random import shuffle, randint
from WP import ChunckedData
from threading import Thread
from util import getIdentityCode, getBasePacket

HOST = ''
SERVER_PORT = 21567 #you can change it
BUFSIZ = 1024
ADDR = (HOST,SERVER_PORT)

tcpSerSock = socket(AF_INET,SOCK_STREAM)
tcpSerSock.bind(ADDR)
tcpSerSock.listen(5)


# In[ ]:


class Game():

    def __init__(playerCount: int, identityList: list):
        self.playerCount = playerCount
        self.activePlayer = {}
        self.ports = list(range(50000, 50000 + playerCount + 1))
        self.running = False
        self.identityList = identityList.copy()
        shuffle(self.identityList)

    def activate(self):
        self.running = True

    def deactivate(self):
        self.running = False

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
    
    def notend(self):

# In[ ]:       

class IncomingConnection(Thread):

    def __init__(self, addr: tuple, dest: Game,id: int):
        super(EstablishConnThread, self).__init__()
        self.result = None
        self.address = addr
        self.id = id

    def run(self):

while True:
    #first particpant set the number of players
    print('waiting for first client connection...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('...connnecting from:', addr)
    #??? how to receive the number of players ???
    N = 12
    newgame = Game(N,identityList)
    for i in range(1,N+1):
        newgame.addPlayer(data)
    """
    set connections with clients and distribute identity
    set corresponding threads
    """
    while (newgame.notend()):
        #for night
        
        #for day

    while True:
        data = tcpCliSock.recv(BUFSIZ)
        if not data:
            break
        #tcpCliSock.send('[%s] %s' %(bytes(ctime(),'utf-8'),data))
        tcpCliSock.send(('[%s] %s' % (ctime(), data)).encode())
    tcpCliSock.close()
tcpSerSock.close()


