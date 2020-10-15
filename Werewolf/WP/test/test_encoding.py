from ..api import ChunckedData
import json

def test_packet1():
    input = {
        'srcAddr': 'localhost',
        'srcPort': 90,
        'destAddr': 'localhost',
        'destPort': 120
    }
    output = input.copy()
    Data = ChunckedData(1, **input)
    mid = Data.toBytesArray()
    Data = ChunckedData(0, rawData=mid)
    assert Data.content == output
    
def test_packet1Resp():
    input = {
        'srcAddr': 'localhost',
        'srcPort': 120,
        'destAddr': 'localhost',
        'destPort': 90,
        'playerRemaining': 10,
        'playerSeats': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    output = input.copy()
    Data = ChunckedData(-1, **input)
    mid = Data.toBytesArray()
    Data = ChunckedData(0, rawData=mid)
    assert Data.content == output

def test_packet2():
    input = {
        'srcAddr': 'localhost',
        'srcPort': 90,
        'destAddr': 'localhost',
        'destPort': 120,
        'chosenSeat': 5
    }
    output = input.copy()
    Data = ChunckedData(1, **input)
    mid = Data.toBytesArray()
    Data = ChunckedData(0, rawData=mid)
    assert Data.content == output

def test_packet2Resp():
    input = {
        'srcAddr': 'localhost',
        'srcPort': 90,
        'destAddr': 'localhost',
        'destPort': 120,
        'chosenSeat': 5,
        'success': True,
        'identity': 5
    }
    output = input.copy()
    Data = ChunckedData(1, **input)
    mid = Data.toBytesArray()
    Data = ChunckedData(0, rawData=mid)
    assert Data.content == output