# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 15:06:28 2020

@author: lenovo-pc
"""

import socket
import time
from threading import Thread
from .WP import ChunckedData, _recv

HOST = '127.0.0.1'
PORT = 21567
BUFSIZE = 1024
ADDR = (HOST, PORT)
ROLE = 0


class IoThread(Thread):
    def __init__(self, threadID, ChunkedData):
        super().__init__()
        self.threadID = threadID
        self.packet = ChunkedData

    def run(self):
        '''
        prprpr777's code
        '''


class Player():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(ADDR)

    def _getBasePacket(self) -> dict:
        ret = {}
        ret['srcAddr'] = self.client[0]
        ret['srcPort'] = self.client[1]
        ret['destAddr'] = self.server[0]
        ret['destPort'] = self.server[1]
        return ret

    def _register(self):
        global ADDR, ROLE
        packet = self._getBasePacket()
        packetSend = ChunckedData(1, **packet)
        packetSend.send(self.socket, ADDR)
        regInfo = _recv(self.socket)
        self.id = regInfo.content['Seat']
        ROLE = regInfo.content['identity']
        print("Your identity is %d/n " % ROLE)

        self.police = False
        self.alive = True

    def playing(self):
        k = 0
        try:
            while(1):
                reqPacket = _recv(self.socket)
                k += 1
                IoThread(k, reqPacket)
        except KeyboardInterrupt:
            # 编号：
            #   村民：0
            #   狼人：-1
            #   狼王：-3
            #   白狼王：-2
            #   预言家：1
            #   女巫：2
            #   猎人：3
            #   守卫：4
            #   白痴：5
            if ROLE != -1:
                pass
            else:
                packet = self._getBasePacket()
                packetSend = ChunckedData(1, **packet)
                packetSend.send(self.socket, ADDR)
                self.alive = False