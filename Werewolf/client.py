# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 15:06:28 2020

@author: lenovo-pc
"""

import socket
import time
from threading import Thread
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
        self.packet = ChunkedData
        self.ADDR = ADDR

    def run(self):
        type = (int)ret.packetType

        if (type == -1):
            """
            -1是服务器发出的建立连接的信息
            """
            print("%d seat(s) remained and the seats you can choose are :" %(ret.content['playerRemaining']))
            for x in ret.content['playerSeats']:
                print(x, end=' ')
            print("Please enter the number of seat you choose: ")
            chosenSeat = input()
    
            return ChunckedData(2,chosenSeat = seatChosed)
    
        elif(type == -2):
            """
            -2是服务器发出的选座信息，不需要回复
            """
            if (ret.content['success'] == True):
                print("Successfully chose the seat! ")
            else
                print("The seat you chose was taken.")
    
            print("your seat is %d and your identity is %d" %(ret.content['chosenSeat'],ret.content['identity']))

        elif(type == 3):
            """
            3是服务器发出的请求玩家执行的操作
            """
            print("the format for you to enter is ")
            print(ret.content['format'])
            print('\n')
            print(ret.content['prompt'])
            print("the time limit is %d" %(ret.content['timeLimit']))
    
            ReceiveTimeoutError(timeout=ret.content['timeLimit'])
    
            target = input()
    
            return ChunckedData(-3,target = target)

      elif(type == 4):
            """
            4是服务器公布的信息，-4 response
            不太确定这个packet中的parameter是啥意思，就先打出来了
            """
            print(ret.content['description'])
            print(ret.content['parameter'])
    
            return ChunckedData(-4, ACK = True)
    
        elif(type == 5):
            """
            自由发言阶段，全部转发显示
            """
            print(ret.content['content'])

        elif(type == 6):
            '''
            限制时间发言阶段
            '''
            print("the time for you to speak is %d" %(ret.content['timeLimit']))
            ReceiveTimeoutError(timeout=ret.content['timeLimit'])
            content = input()

            return ChunckedData(-6, content = content)

        elif(type == 7):
            '''
            投票阶段
            '''
            print(ret.content['prompt'])
            candidate = input()

            if (candidate.isspace() == True):
                ret = ChunckedData(-7, vote=False, candidate=0)
            else:
                ret = ChunckedData(-7, vote=True, candidate=candidate)
    
            return ret
    
        elif(type == 8):
            pass
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ret.send(self, self.socket, ADDR)
        

class Player():
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ADDR = (host, post)
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
