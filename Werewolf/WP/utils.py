# 判断Python版本
try:
    xrange(10)
except NameError:
    py2 = False
else:
    py2 = True


_packetType = {
    # 对于所有的packetType，内容都应包括收发双方的IP+端口号
    # 对于Resp类型的packetType，还需要包括对对应请求的ACK
    "EncodedData": 0,
    "Establish": 1,    # 客户端建立与服务器的连接时发送
    "EstablishResp": -1,   # 服务器回送连接建立信息，内容包括当前房间剩余的人数，及可供选择的座位
    "ActionPrompt": 3,    # 服务器请求玩家执行操作，内容包括玩家身份限制、输入格式限制、参数与文本提示
    "ActionResp": -3,   # 客户端回送执行的操作，内容包括是否执行操作，操作目标等
    "InformationPublishing": 4,    # 服务器公布信息，如猎人开枪状态、死讯等
    "FreeConversation": 5,    # 自由交谈状态，服务器自动转发所有符合条件的包，内容包括交谈内容及目标，服务器会发送一个空包作为请求
    "LimitedConversation": 6,    # 发言阶段，在开始前服务器会发送一个空包作为请求，内容包含交谈内容及时间限制
    "LimitedConversationResp": -6,   # 发言阶段，服务器确认收到信息
    "Vote": 7,    # 服务器发起投票
    "VoteResp": -7,   # 客户端回送投票结果
    "Death": 8     # 服务器提示客户端出局
}

_checkParam = {
    '': {
        'srcAddr': str,                 # 源地址
        'destAddr': str,                # 目的地址
        'srcPort': int,                 # 源端口
        'destPort': int                 # 目的端口
    },
    0: {
        'rawData': bytearray            # 发送的原始数据，这一项本身不会被用到
    },
    1: {},
    -1: {
        'seat': int,                    # 分配的座位号
        'identity': int                # 分配的身份
    },
    3: {
        # 'identityLimit': tuple,         # 能收到消息的玩家身份列表
        # 'playerNumber': int,          # 目的玩家编号（deprecated）
        'iskill': bool,                # 是否是晚上
        'format': str,                  # 玩家应当输入的格式，示例 "int"
        'prompt': str,                  # 输入提示
        'timeLimit': float                # 时间限制
    },
    -3: {
        'action': bool,                 # 玩家是否执行操作（若回送，指玩家作用是否成功）
        'target': int                   # 玩家执行操作的目标
    },
    4: {
        'content': str,             # 要公布的消息
    },
    5: {
        'content': str                 # 自由交谈的内容
        # 'type': tuple                   # 能收到消息的身份列表，空列表指全部玩家
    },
    6: {'timeLimit': int},              # 时间限制
    -6: {'content': str},               # 发送的消息
    7: {
        'prompt': str
    },                   # 当服务器第一次发送时，指是否可以投票，当第二次发送时，指投票是否有效
    -7: {
        'vote': bool,                   # 是否投票
        'candidate': int                # 投票候选人
    },
    8: {},
    -8: {
        'result': bool  # The result of the game
    },
    9: {
        'id': int
    }
}
