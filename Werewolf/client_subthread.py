from .abstraction import *
from .WP import ChunckedData
from threading import Thread
from .util import getIndentity, getBasePacket
from .WP.utils import _checkParam, _packetType


class ReceiveTimeoutError(Exception):

    def __init__(self, timeout: int):
        self.timeout = timeout
        super(ReceiveTimeoutError).__init__()

    def __str__(self):
        return "Data receive timeout."

# 为什么要加下面这一堆函数呢，直接调构造函数不好吗？


def comPack2(seat) -> ChunckedData:
    """
    compress the return packet of -1,
    whose packetType number is 2
    """
    ret = ChunckedData(2, chosenSeat=seat)
    return ret


def comPack_3(target) -> ChunckedData:
    """
   compress the return packet of 3,
   which is -3
    """

    ret = ChunckedData(-3, target=target)
    return ret


def comPack_4() -> ChunckedData:
    ret = ChunckedData(-4, ACK=True)
    return ret


def comPack_6(content) -> ChunckedData:
    ret = ChunckedData(-6, content=content)
    return ret


def comPack_7(candidate) -> ChunckedData:
    if(candidate.isspace() == True):
        ret = ChunckedData(-7, vote=False, candidate=0)
    else:
        ret = ChunckedData(-7, vote=True, candidate=candidate)

    return ret


def playerResponse(ret):
    type = int(ret.packetType)

    if (type == -1):
        """
        -1是服务器发出的建立连接的信息
        """
        print("%d seat(s) remained and the seats you can choose are :" %
              (ret.content['playerRemaining']))
        for x in ret.content['playerSeats']:
            print(x, end=' ')
        print("Please enter the number of seat you choose: ")
        chosenSeat = input()

        return comPack2(chosenSeat)

    elif(type == -2):
        """
        -2是服务器发出的选座信息，不需要回复
        """
        if (ret.content['success'] == True):
            print("Successfully chose the seat! ")
        else:
            print("The seat you chose was taken.")

        print("your seat is %d and your identity is %d" %
              (ret.content['chosenSeat'], ret.content['identity']))

    elif(type == 3):
        """
        3是服务器发出的请求玩家执行的操作
        """
        print("the format for you to enter is ")
        print(ret.content['format'])
        print('\n')
        print(ret.content['prompt'])
        print("the time limit is %d" % (ret.content['timeLimit']))

        ReceiveTimeoutError(timeout=ret.content['timeLimit'])

        target = input()

        return comPack_3(target)

    elif(type == 4):
        """
        4是服务器公布的信息，-4 response
        不太确定这个packet中的parameter是啥意思，就先打出来了
        """
        print(ret.content['description'])
        print(ret.content['parameter'])

        return comPack_4()

    elif(type == 5):
        """
        自由发言阶段，全部转发显示
        """
        print(ret.content['content'])

    elif(type == 6):
        print("the time for you to speak is %d" % (ret.content['timeLimit']))
        ReceiveTimeoutError(timeout=ret.content['timeLimit'])
        content = input()

        return comPack_6(content)

    elif(type == 7):
        print(ret.content['prompt'])
        candidate = input()

        return comPack_7(candidate)

    elif(type == 8):
        pass
