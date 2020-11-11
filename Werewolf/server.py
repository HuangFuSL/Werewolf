from socket import *
from time import ctime
from threading import Thread

from server.logic import Game
from util import getIdentityCode, getBasePacket
from random import shuffle, randint
from abstraction import *
from WP import api
from server import logic


HOST = ''
SERVER_PORT = 21567
BUFSIZ = 1024
ADDR = (HOST,SERVER_PORT)

tcpSerSock = socket(AF_INET,SOCK_STREAM)

#input the number of clients
playerCount = input('>')
while(not(type(playerCount) == int and playerCount >= 6 and playerCount <= 12)):
    print('Please input the right number between 6 and 12!')
    playerCount = input('>')
print('the number of players is: %d' % playerCount)

#wait for client connection and create the connection
game = Game(playerCount)
for idclient in range(1, int(playerCount) + 1):
    tcpSerSock.bind(ADDR)
    tcpSerSock.listen(5)
    print('waiting for client %d connection...' % idclient)
    tcpCliSock, addr = tcpSerSock.accept()
    print('...connnecting client %d from:'% idclient, addr)
    game.addAddr(addr[1], addr[0])

#allocate the identity and tell to the corresponding client
game.allocateIdentity(ADDR)

#if the game not ends

    #prompt for action of werewolves

    #prompt for action of witch

    #prompt for action of predictor

    #prompt for action of guard

    #if is the first night

        #prompt for the election of police

        #the candidate talks

        #vote

        #announce the police

    #announce the victim

    #prompt and wait for the conversation

    #vote

    #announce the exile

"""
set connections with clients and distribute identity
set corresponding threads
"""
"""while (newgame.notend()):
    #for night

    #for day

while True:
    data = tcpCliSock.recv(BUFSIZ)
    if not data:
        break
    #tcpCliSock.send('[%s] %s' %(bytes(ctime(),'utf-8'),data))
    tcpCliSock.send(('[%s] %s' % (ctime(), data)).encode())
tcpCliSock.close()
tcpSerSock.close()"""