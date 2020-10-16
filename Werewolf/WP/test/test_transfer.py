from ..api import ChunckedData, ReceiveThread, ReceiveTimeoutError
from pytest import raises
import pytest
import json
import socket
import time
import random

def test_transfer():
    sendSocket, receiveSocket = socket.socket(), socket.socket()
    port = 0
    while port == 0:
        port = random.randint(10000, 30000)
        try:
            receiveSocket.bind(('localhost', port))
        except OSError:
            port = 0
    raw = {
        'srcAddr': '127.0.0.1',
        'srcPort': 90,
        'destAddr': '127.0.0.1',
        'destPort': port
    }
    tReceive = ReceiveThread(receiveSocket)
    tReceive.start()
    data = ChunckedData(1, **raw)
    sendSocket.connect(('localhost', port))
    data.send(sendSocket)
    tReceive.join()
    ret = tReceive.getResult()
    assert data.content == ret.content

def test_transferTimeout():
    sendSocket, receiveSocket = socket.socket(), socket.socket()
    port = 0
    while port == 0:
        port = random.randint(10000, 30000)
        try:
            receiveSocket.bind(('localhost', port))
        except OSError:
            port = 0
    raw = {
        'srcAddr': '127.0.0.1',
        'srcPort': 90,
        'destAddr': '127.0.0.1',
        'destPort': port
    }
    tReceive = ReceiveThread(receiveSocket, timeout=1)
    tReceive.start()
    data = ChunckedData(1, **raw)
    sendSocket.connect(('localhost', port))
    tReceive.join()
    with raises(ReceiveTimeoutError):
        ret = tReceive.getResult()

def test_transferPortError():
    sendSocket, receiveSocket = socket.socket(), socket.socket()
    port = 0
    while port == 0:
        port = random.randint(10000, 30000)
        try:
            receiveSocket.bind(('localhost', port))
        except OSError:
            port = 0
    raw = {
        'srcAddr': '127.0.0.1',
        'srcPort': 90,
        'destAddr': '127.0.0.1',
        'destPort': port - 1
    }
    tReceive = ReceiveThread(receiveSocket, timeout=1)
    tReceive.start()
    data = ChunckedData(1, **raw)
    sendSocket.connect(('localhost', port))
    with raises(AssertionError):
        data.send(sendSocket)
    tReceive.join()
    with raises(ReceiveTimeoutError):
        ret = tReceive.getResult()