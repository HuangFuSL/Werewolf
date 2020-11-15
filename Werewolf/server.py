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

# input the number of clients
playerCount = input('>')
while (not(type(playerCount) == int and playerCount >= 6 and playerCount <= 12)):
    print('Please input the right number between 6 and 12!')
    playerCount = input('>')
print('the number of players is: %d' % playerCount)

# initialize a new game
game = Game(HOST, SERVER_PORT, playerCount)

# input the identityList
identityList = input('>')
game.setIdentityList(identityList)

# wait for client connection and create the connection
game.startListening()
for i in range(0, playerCount):
    game.addPlayer()

# start the game
gameStatus = 0
while gameStatus == 0:
    game.nightTime()
    gameStatus = game.dayTime()
if gameStatus == 1:
    game.broadcast(None, "Villagers win!")
else:
    game.broadcast(None, "werewolves win!")
