# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 15:06:28 2020

@author: lenovo-pc
"""

import socket
import time
from threading import Thread
from typing import Optional
from .WP import ChunckedData, _recv

BUFSIZE = 1024
ROLE = 0


class ReceiveTimeoutError(Exception):

    def __init__(self, timeout: int):
        self.timeout = timeout
        super(ReceiveTimeoutError).__init__()

    def __str__(self):
        return "Data receive timeout."


class IoThread(Thread):
    def __init__(self, ChunkedData, ADDR):
        super().__init__()
        self.packet: ChunckedData = ChunkedData
        self.ADDR = ADDR

    def run(self):
        type = int(self.packet.type)
        ret: Optional[ChunckedData] = None
        if (type == -1):
            """
            -1是服务器发出的建立连接的信息
            """
            print("%d seat(s) remained and the seats you can choose are :" %
                  (self.packet.content['playerRemaining']))
            for x in self.packet.content['playerSeats']:
                print(x, end=' ')
            print("Please enter the number of seat you choose: ")
            chosenSeat = input()
            ret = ChunckedData(2, chosenSeat=chosenSeat)

        elif(type == -2):
            """
            -2是服务器发出的选座信息，不需要回复
            """
            if (self.packet.content['success'] == True):
                print("Successfully chose the seat! ")
            else:
                print("The seat you chose was taken.")

            print("your seat is %d and your identity is %d" %
                  (self.packet.content['chosenSeat'], self.packet.content['identity']))

        elif(type == 3):
            """
            3是服务器发出的请求玩家执行的操作
            """
            print("the format for you to enter is ")
            print(self.packet.content['format'])
            print('\n')
            print(self.packet.content['prompt'])
            print("the time limit is %d" % (self.packet.content['timeLimit']))

            ReceiveTimeoutError(timeout=self.packet.content['timeLimit'])

            target = input()
            if self.packet.content['format'] == 'str':
                ret = ChunckedData(-3, target=target)
            else:
                ret = ChunckedData(-3, target=eval(target))

        elif(type == 4):
            """
            4是服务器公布的信息，-4 response
            不太确定这个packet中的parameter是啥意思，就先打出来了
            """
            print(self.packet.content['description'])
            print(self.packet.content['parameter'])

            ret = ChunckedData(-4, ACK=True)

        elif(type == 5):
            """
            自由发言阶段，全部转发显示
            """
            print(self.packet.content['content'])

        elif(type == 6):
            '''
            限制时间发言阶段
            '''
            print("the time for you to speak is %d" %
                  (self.packet.content['timeLimit']))
            ReceiveTimeoutError(timeout=self.packet.content['timeLimit'])
            content = input()

            ret = ChunckedData(-6, content=content)

        elif(type == 7):
            '''
            投票阶段
            '''
            print(self.packet.content['prompt'])
            candidate = input()

            if (candidate.isspace() == True):
                ret = ChunckedData(-7, vote=False, candidate=0)
            else:
                ret = ChunckedData(-7, vote=True, candidate=candidate)

        elif(type == 8):
            pass

        if ret:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ret.send(self.socket, self.ADDR)


class Player():
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ADDR = (host, port)
        self.socket.connect(self.ADDR)

    def _getBasePacket(self) -> dict:
        ret = {}
        ret['srcAddr'] = self.client[0]
        ret['srcPort'] = self.client[1]
        ret['destAddr'] = self.server[0]
        ret['destPort'] = self.server[1]
        return ret

    def _register(self):
        global ROLE
        packet = self._getBasePacket()
        packetSend = ChunckedData(1, **packet)
        packetSend.send(self.socket, self.ADDR)
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
            #   白狼王：-2
            #   狼王：-3
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
                packetSend.send(self.socket, self.ADDR)
                self.alive = False
