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


