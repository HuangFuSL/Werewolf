# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 15:06:28 2020

@author: lenovo-pc
"""

from Werewolf.WP.api import KillableThread
import socket
from socket import AF_INET, SOCK_STREAM
import sys
from threading import Thread, ThreadError
from typing import Any, Dict, Optional, Tuple, Union
try:
    from .WP import ChunckedData, TimeLock, ReceiveThread, ReadInput
except ImportError:
    from WP import ChunckedData, TimeLock, ReceiveThread, ReadInput

BUFSIZE = 1024
ROLE = 0


def convertToString(code: int) -> str:
    map = {
        0: "Villager",
        -1: "Wolf",
        -2: "White Werewolf",
        -3: "King of werewolves",
        1: "Predictor",
        2: "Witch",
        3: "Hunter",
        4: "Guard",
        5: "Idiot"
    }
    return map[code]


def getBasePacket(context: dict) -> dict:
    return {
        'srcAddr': context['clientAddr'],
        'srcPort': context['clientPort'],
        'destAddr': context['serverAddr'],
        'destPort': context['serverPort']
    }


def getServerAddr(context: dict) -> Tuple[str, int]:
    return (
        context['serverAddr'],
        context['serverPort']
    )


def getClientAddr(context: dict) -> Tuple[str, int]:
    return (
        context['clientAddr'],
        context['clientPort']
    )


def ProcessPacket(toReply: ChunckedData, context: dict) -> int:
    """
    Ask for user input and build the corresponding packet.
    """
    if toReply is None:
        return 0
    if context['isalive'] == False and toReply.type != -8:
        return -2
    if toReply.type == -1:
        """
        -1: {
            'seat': int,                    # 分配的座位号
            'identity': int                # 分配的身份
        },
        Villager: 0
        Wolf: -1
        White Werewolf: -2
        King of werewolves: -3
        Predictor: 1
        Witch: 2
        Hunter: 3
        Guard: 4
        Idiot: 5
        """
        context['id'] = toReply['seat']
        context['identity'] = toReply['identity']
        context['serverPort'] = toReply['srcPort']
        context['serverAddr'] = toReply['srcAddr']
        print("Your seat number is %d" % (context['id'], ))
        print("Your identity is '%s'" %
              (convertToString(context['identity']), )
              )
    elif toReply.type == -3:
        """
        -3: {
            'action': bool,                 # 玩家是否执行操作（若回送，指玩家作用是否成功）
            'target': int                   # 玩家执行操作的目标
        },
        """
        assert context['identity'] == 1
        print("The person you checked is %s." %
              ("good" if toReply['action'] else "bad", )
              )
    elif toReply.type == 3:
        """
        3: {
            # 'identityLimit': tuple,         # 能收到消息的玩家身份列表
            # 'playerNumber': int,          # 目的玩家编号（deprecated）
            'isnight': bool,                # 是否是晚上
            'format': str,                  # 玩家应当输入的格式，示例 "int"
            'prompt': str,                  # 输入提示
            'timeLimit': int                # 时间限制
        },
        """
        readThread: ReadInput
        basePacket: dict = getBasePacket(context)

        if context['identity'] < 0 and toReply['iskill']:
            print(toReply['prompt'])
            timer = TimeLock(toReply['timeLimit'])
            timer.setDaemon(True)
            timer.start()
            ret: int = 0
            packetType: int
            receivingThread = ReceiveThread(context['socket'], 120)
            receivingThread.setDaemon(True)
            receivingThread.start()
            readThread = ReadInput("", str, toReply['timeLimit'])
            readThread.setDaemon(True)
            readThread.start()

            while timer.is_alive():

                if receivingThread.is_alive() == False:
                    ProcessPacket(receivingThread.getResult(), context=context)
                    receivingThread = ReceiveThread(context['socket'], 120)
                    receivingThread.setDaemon(True)
                    receivingThread.start()

                if readThread.is_alive() == False:

                    basePacket = getBasePacket(context)

                    try:
                        ret = int(readThread.getResult())
                    except ValueError:
                        """
                        5: {
                            'content': str                 # 自由交谈的内容
                            # 'type': tuple                   # 能收到消息的身份列表，空列表指全部玩家
                        },
                        """
                        if type(readThread.getResult()) == str:
                            basePacket['content'] = readThread.getResult()
                            packetType = 5
                        else:
                            basePacket['action'] = False
                            packetType = -3
                    else:
                        """
                        -3: {
                            'action': bool,                 # 玩家是否执行操作（若回送，指玩家作用是否成功）
                            'target': int                   # 玩家执行操作的目标
                        },
                        """
                        basePacket['action'] = ret > 0
                        basePacket['target'] = ret
                        packetType = -3

                    packetSend = ChunckedData(packetType, **basePacket)
                    sendingThread = Thread(
                        target=packetSend.send, args=(context['socket'], )
                    )
                    sendingThread.start()
                    if packetType == -3:
                        receivingThread.kill()
                        break
                    elif packetType == 5:
                        readThread = ReadInput("", str, toReply['timeLimit'])
                        readThread.setDaemon(True)
                        readThread.start()

            readThread.kill()
            receivingThread.kill()

        else:
            print(toReply['prompt'])
            print("You have to enter a(n) %s" % (toReply['format'], ))
            print('You have %d seconds to choose' % (toReply['timeLimit'], ))

            readThread = ReadInput("", toReply['format'], toReply['timeLimit'])
            readThread.setDaemon(True)
            readThread.start()
            readThread.join()

            basePacket['target'] = readThread.getResult()
            basePacket['action'] = readThread.getResult() >= 0
            packetType = -3

            packetSend = ChunckedData(packetType, **basePacket)
            sendingThread = Thread(
                target=packetSend.send, args=(context['socket'], )
            )
            sendingThread.start()

    elif toReply.type == 4:
        """
        4: {
            'content': str,             # 要公布的消息
        },
        """
        print(toReply['content'])
    elif toReply.type == 5:
        """
        5: {
            'content': str                 # 自由交谈的内容
            # 'type': tuple                   # 能收到消息的身份列表，空列表指全部玩家
        },
        """
        print(toReply['content'])
    elif toReply.type == 6:
        """
        6: {'timeLimit': int},              # 时间限制
        """
        print("It's your turn.")
        print('You have %d seconds to speak' % (toReply['timeLimit'], ))

        readThread = ReadInput("", str, toReply['timeLimit'])
        readThread.setDaemon(True)
        readThread.start()
        readThread.join()
        basePacket: dict = getBasePacket(context)
        if isinstance(readThread.getResult(), str):
            basePacket['content'] = readThread.getResult()
        elif isinstance(readThread.getResult(), KeyboardInterrupt):
            raise readThread.getResult()
        packetType = -6

        packetSend = ChunckedData(packetType, **basePacket)
        sendingThread = Thread(
            target=packetSend.send, args=(context['socket'], )
        )
        sendingThread.start()
    elif toReply.type == 7:
        """
        7: {
            'prompt': str
        },
        """
        readThread = ReadInput(toReply['prompt'], int, toReply['timeLimit'])
        readThread.setDaemon(True)
        readThread.start()
        readThread.join()

        basePacket: dict = getBasePacket(context)
        if type(readThread.getResult()) == int:
            basePacket['vote'] = True
            basePacket['candidate'] = readThread.getResult()
        else:
            basePacket['vote'] = False
            basePacket['candidate'] = 0
        packetType = -7

        packetSend = ChunckedData(packetType, **basePacket)
        sendingThread = Thread(
            target=packetSend.send, args=(context['socket'], )
        )
        sendingThread.start()

    elif toReply.type == 8:
        """
        8: {},
        """
        context['isalive'] = False
        return -2

    elif toReply.type == -8:
        """
        -8: {
            'result': bool  # The result of the game
        }
        """
        if toReply['result'] == context['identity'] >= 0:
            return 1
        else:
            return -1
    return 0


def launchClient(argv: list):
    context: Dict[str, Any] = {'isalive': True}
    context["serverAddr"] = input(
        "Please enter the IP address of the server:\n")
    if not context["serverAddr"]:
        context["serverAddr"] = "localhost"
    try:
        context['serverPort'] = int(
            input("Please enter the port of the server:\n"))
    except:
        context['serverPort'] = 21567
    sock = socket.socket(AF_INET, SOCK_STREAM)
    sock.connect(getServerAddr(context=context))
    context['socket'] = sock
    context['serverAddr'], context['serverPort'] = sock.getpeername()
    context['clientAddr'], context['clientPort'] = sock.getsockname()

    basePacket: dict = getBasePacket(context)
    packetSend = ChunckedData(1, **basePacket)
    sendingThread = Thread(target=packetSend.send, args=(sock,))
    receivingThread = ReceiveThread(sock, 120)
    receivingThread.start()
    sendingThread.start()
    receivingThread.join()
    curPacket = receivingThread.getResult()

    assert curPacket is not None, "Failed to connect to the server."
    ret: int = 0
    while ret ** 2 != 1:
        try:
            assert curPacket is not None, "Lost connection to the server."
            tempThread = KillableThread(ProcessPacket, *(curPacket, context))
            tempThread.start()
            tempThread.join()
            ret = tempThread.getResult()
            del tempThread
            receivingThread = ReceiveThread(sock, 180)
            receivingThread.start()
            receivingThread.join()
            curPacket = receivingThread.getResult()
        except KeyboardInterrupt:
            if context['identity'] >= 0:
                continue
            if context["isalive"] == False:
                print("You hace already died, please wait for the result.")
                continue
            else:
                basePacket: dict = getBasePacket(context)
                basePacket['id'] = context['id']
                packetSend = ChunckedData(9, **basePacket)
                sock = socket.socket(AF_INET, SOCK_STREAM)
                sendingThread = Thread(
                    target=packetSend.send, args=(sock, )
                )
                sendingThread.start()

    if ret == 1:
        print("You won!")
    elif ret == -1:
        print("You lost!")
