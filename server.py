import socket
from time import ctime
from threading import Thread

from Werewolf.server.logic import Game
from Werewolf.server.util import getIdentityCode, getBasePacket
from random import shuffle, randint
from Werewolf.server.abstraction import *
from Werewolf.WP import api


HOST = ''
SERVER_PORT = 21567
BUFSIZ = 1024
ADDR = (HOST, SERVER_PORT)

tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

playerCount: int = 6
# input the number of clients
# playerCount: int = int(input('> '))
# while (not(type(playerCount) == int and playerCount >= 6 and playerCount <= 12)):
#     print('Please input the right number between 6 and 12!')
#     playerCount = int(input('> '))
print('the number of players is: %d' % playerCount)

# initialize a new game
game = Game(HOST, SERVER_PORT, playerCount)

# input the identityList
# identityList = eval(input('> '))
identityList = {"Villager": 2, "Witch": 1, "Wolf": 2, "Predictor": 1}
game.setIdentityList(**identityList)

# wait for client connection and create the connection
game.startListening()
game.activate()
# start the game
game.launch()
