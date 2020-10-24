import socket
import abc

from Werewolf.Werewolf.Werewolf.WP.api import ChunckedData


class Person:
    def __init__(self):
        # AF_INET：使用TCP/IP-IPv4协议簇；SOCK_STREAM：使用TCP流
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        # id和police的值由服务器进行分配，在__init__()方法中分别被初始化为0和False
        self.id = 0
        self.police = False
        # 如果某个客户端是狼人，则innocent的值为False；否则为True
        self.innocent = True

    # 客户端判断自己接收到的分组类型是否为-2的代码先于verifyIdentity()实现，因此没有写到这个方法里
    def verifyIdentity(self, receivedPacket):
        if receivedPacket.content['success'] == True:
            self.id = receivedPacket.content['chosenSeat']
            # 1代表狼人，2代表狼王，3代表白狼王
            if receivedPacket.content['identity'] in [1, 2, 3]:
                self.innocent = False
        else:
            print("Failed in verifying your identity.")

    def vote(self):
        content = {}
        id = int(input("Please enter the seat number of the player you want to vote for: "))
        content['vote'] = True
        content['candidate'] = id
        votePacket = ChunckedData(-7, content)
        votePacket.send(self.client)
        return id

    def joinElection(self):
        content = {}
        resp = input("Do you want to be the policeman? (y / n) ")
        if resp == 'y':
            content['action'] = True
        elif resp == 'n':
            content['action'] = False
        content['target'] = -1
        joinElectionPacket = ChunckedData(-3, content)
        joinElectionPacket.send(self.client)
        return content['action']

    def voteForPolice(self):
        content = {}
        id = int(input("Please enter the seat number of the player you want to be the police: "))
        content['vote'] = True
        content['candidate'] = id
        voteForPolicePacket = ChunckedData(-7, content)
        voteForPolicePacket.send(self.client)
        return id

    """
    如果某个客户端被指定为警长，这个方法用来将该客户端Person实例的police设置为True
    客户端判断自己接收到的分组类型是否为4的代码先于verifyIdentity()实现，因此没有写到这个方法里
    键"parameter"对应的元组中保存了被指定为警长的玩家的id
    """
    def setPolice(self, receivedPacket):
        if receivedPacket.content['parameter'][0] == self.id:
            self.police = True
            print("You are chosen to be the police.")
        else:
            print("You are not chosen to be the police.")

    # 此方法用于发言阶段，不用于自由交谈阶段
    def speak(self):
        print("Input your thoughts. Enter an empty line to finish.")
        content = {}
        raw_text = []
        text = ""
        for line in iter(input, ''):
            raw_text.append(line)
        for string in raw_text:
            text += string
        content['content'] = text
        speakPacket = ChunckedData(-6, content)
        speakPacket.send(self.client)


class Villager(Person):
    def __init__(self):
        super().__init__()


class Wolf(Person):
    def __init__(self):
        super().__init__()

    def kill(self):
        content = {}
        content['action'] = True
        id = int(print("Who do you want to kill? Enter his/her id: "))
        content['target'] = id
        killPacket = ChunckedData(-3, content)
        killPacket.send(self.client)
        return id

    # 本来想把这个方法命名为suicide的，后来感觉影响不好
    def selfDestruct(self):
        content = {}
        message = "I am a wolf!"
        content['content'] = message
        speakPacket = ChunckedData(-6, content)
        speakPacket.send(self.client)


class KingOfWerewolves(Wolf):
    def __init__(self):
        super().__init__()


class WhiteWerewolf(Wolf):
    def __init__(self):
        super().__init__()


class SkilledPerson(Person):
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def skill(self):
        pass


class Predictor(SkilledPerson):
    def __init__(self):
        super().__init__()

    def skill(self):
        content = {}
        id = int(input("Whose identity do you want to know? Enter his/her id: "))
        content['action'] = True
        content['target'] = id
        predictPacket = ChunckedData(-3, content)
        predictPacket.send(self.client)
        return id


class Witch(SkilledPerson):
    def __init__(self):
        super().__init__()

    """
    因为女巫不但需要决定是否发动技能，还需要决定技能是救人还是杀人，以及确定技能发动的对象。而-3分组只有两个变量。
    为了解决这个问题，做出如下规定：如果'target'键对应的值为-1，则表示女巫不发动技能。如果'target'键对应的值
    为某个用户的座位编号，那么'active'键对应的值为True时，表示女巫救人；值为False时表示女巫杀人
    """
    def skill(self):
        content = {}
        prompt = "Do you want to save someone who's been dead, or do you want to kill "
        prompt += "someone with your poison? (s / k) "
        option_1 = input("Do you want to use your skill? (y / n)")
        if option_1 == 'n':
            content['target'] = -1
        elif option_1 == "y":
            option_2 = input(prompt)
            if option_2 == "s":
                content['active'] = True
            elif option_2 == 'k':
                content['active'] = False
            id = int(input("Please enter the id of the player whom you want to use skill onto: "))
            content['target'] = id
        predictPacket = ChunckedData(-3, content)
        predictPacket.send(self.client)
        return id


class Hunter(SkilledPerson):
    def __init__(self):
        super().__init__()

    def skill(self):
        content = {}
        id = int(input("Who do you want to shoot at? Enter his/her id: "))
        content['action'] = True
        content['target'] = id
        predictPacket = ChunckedData(-3, content)
        predictPacket.send(self.client)
        return id


class Guard(SkilledPerson):
    def __init__(self):
        super().__init__()

    def skill(self):
        content = {}
        id = int(input("Who do you want to guard tonight? Enter his/her id: "))
        content['action'] = True
        content['target'] = id
        predictPacket = ChunckedData(-3, content)
        predictPacket.send(self.client)
        return id


class Idiot(SkilledPerson):
    def __init__(self):
        super().__init__()

    def skill(self):
        content = {}
        message = "I am an idiot!"
        content['content'] = message
        speakPacket = ChunckedData(-6, content)
        speakPacket.send(self.client)
