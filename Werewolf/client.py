from Werewolf.WP.api import KillableThread
import socket
from socket import AF_INET, AF_INET6, SOCK_STREAM
from threading import Thread
from typing import Any, Dict, Optional, Tuple
from time import sleep
try:
    from .WP import ChunckedData, TimeLock, ReceiveThread, ReadInput
except ImportError:
    from WP import ChunckedData, TimeLock, ReceiveThread, ReadInput

BUFSIZE = 1024
ROLE = 0


def convertToString(code: int) -> str:
    map = {
        0: "村民",
        -1: "狼人",
        -2: "白狼王",
        -3: "狼王",
        1: "预言家",
        2: "女巫",
        3: "猎人",
        4: "守卫",
        5: "白痴"
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


def ProcessPacket(toReply: ChunckedData, context: dict) -> bool:
    """
    Ask for user input and build the corresponding packet.
    """
    if toReply is None:
        return False
    if context['isalive'] == False and toReply.type != -8:
        return False
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
        print("你的座位号是%d" % (context['id'], ))
        print("你的身份是%s" %
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
        print("你查验的玩家是%s" %
              ("好人" if toReply['action'] else "狼人", )
              )
    elif toReply.type == 3:
        """
        3: {
            # 'identityLimit': tuple,       # 能收到消息的玩家身份列表
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
            ret: int = 0
            packetType: int
            readThread = ReadInput("", str, toReply['timeLimit'], True)
            readThread.setDaemon(True)
            readThread.start()
            readThread.join()

            basePacket = getBasePacket(context)

            try:
                if isinstance(readThread.getResult(), KeyboardInterrupt):
                    if context['identity'] >= 0:
                        return True
                    else:
                        raise readThread.getResult()
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
            packetSend.send(context['socket'])

            return packetType == 5

        else:
            print(toReply['prompt'])
            print("你需要输入一个%s" % (toReply['format'], ))
            print('你有%d秒的时间进行选择' % (toReply['timeLimit'], ))

            readThread = ReadInput("", toReply['format'], toReply['timeLimit'])
            readThread.setDaemon(True)
            readThread.start()
            readThread.join()

            basePacket['target'] = readThread.getResult()
            basePacket['action'] = readThread.getResult() >= 0
            packetType = -3

            packetSend = ChunckedData(packetType, **basePacket)
            packetSend.send(context['socket'])

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
        print("轮到你进行发言：")
        print('你有%d秒的发言时间' % (toReply['timeLimit'], ))

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
        packetSend.send(context['socket'])

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
        packetSend.send(context['socket'])

    return False


def packetProcessWrapper(curPacket: ChunckedData, context: dict):
    try:
        timer = TimeLock(curPacket['timeLimit'])
        timer.setDaemon(True)
        timer.start()
        while not timer.getStatus() and ProcessPacket(curPacket, context):
            pass
            # REVIEW for debugging
            # print("Process Wrapper loop")
    except KeyError:
        # If no 'timeLimit' provided...
        ProcessPacket(curPacket, context)


def launchClient(hostIP: str = "localhost", hostPort: int = 21567):
    context: Dict[str, Any] = {'isalive': True}
    context['serverAddr'] = hostIP
    context['serverPort'] = hostPort

    sockType = AF_INET6 if ":" in hostIP else AF_INET
    sock = socket.socket(sockType, SOCK_STREAM)
    sock.connect(getServerAddr(context=context))
    context['socket'] = sock
    context['serverAddr'], context['serverPort'] = sock.getpeername()[:2]
    context['clientAddr'], context['clientPort'] = sock.getsockname()[:2]

    basePacket: dict = getBasePacket(context)
    packetSend = ChunckedData(1, **basePacket)
    receivingThread = ReceiveThread(sock, 120)
    receivingThread.setDaemon(True)
    receivingThread.start()
    packetSend.send(context['socket'])
    receivingThread.join()
    curPacket: Optional[ChunckedData] = None
    actionPacket: Optional[ChunckedData] = None

    ret: int = 0
    temp: Optional[KillableThread] = None
    while ret ** 2 != 1:
        """
        不巧，有时候按下Ctrl+C的时候程序恰好执行到这里，无法捕获到异常
        """
        try:
            if isinstance(curPacket, ChunckedData):
                if curPacket.type == 8:
                    print("你死了")
                    ret = 2
                elif curPacket.type == -8:
                    print("村民胜利" if curPacket['result'] else "狼人胜利")
                    ret = 1 if curPacket['result'] == (
                        context['identity'] >= 0
                    ) else -1
                    break
                else:
                    ret = 0
                if curPacket.type in [4, 5]:
                    """
                    Only print the message, does not change the loop status
                    """
                    packetProcessWrapper(curPacket, context)
                elif curPacket.type == 9:
                    """
                    监听到有玩家发生自爆，杀掉当前线程
                    """
                    print(str(curPacket['id']) + "号玩家自爆")
                    if temp is not None and temp.is_alive():
                        temp.kill()
                else:
                    """
                    Enter the wrapper loop. First check the running status of the wrapper.
                    """
                    if temp is not None and temp.is_alive():
                        temp.kill()
                    temp = KillableThread(packetProcessWrapper,
                                          *(curPacket, context))
                    temp.setDaemon(True)
                    temp.start()

                curPacket = None

            if not receivingThread.is_alive():
                curPacket = receivingThread.getResult()
                receivingThread = ReceiveThread(sock, 1024)
                receivingThread.setDaemon(True)
                receivingThread.start()

            sleep(0.05)

        except KeyboardInterrupt:
            if context['identity'] >= 0:
                continue
            if context["isalive"] == False:
                print("你已经死了，请等待游戏结果")
                continue
            else:
                basePacket: dict = getBasePacket(context)
                basePacket['id'] = context['id']
                packetSend = ChunckedData(9, **basePacket)
                try:
                    sockTemp = socket.socket(sockType, SOCK_STREAM)
                    sockTemp.connect((hostIP, hostPort + 1))
                    packetSend.send(sockTemp)
                    del sockTemp
                except ConnectionRefusedError:
                    """
                    The server is not ready for receiving messages
                    """
                    print("你现在不能自爆")

        except ConnectionResetError:
            print("与服务器断开连接")
            break

    if ret == 1:
        print("你赢了")
    elif ret == -1:
        print("你输了")
