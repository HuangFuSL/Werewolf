from ..abstraction import *
from typing import Tuple, Union


def getIdentityCode(
    obj: Union[Villager, Wolf, KingOfWerewolves, WhiteWerewolf, Hunter, Guard, Predictor, Witch, Idiot]
    ) -> int:
    assert isinstance(obj, Person)
    assert type(obj) != Person
    assert type(obj) != SkilledPerson
    return obj.type


availableIdentity = ['Villager', 'Wolf', 'Predictor',
                     'Witch', 'Hunter', 'Guard', 'KingofWerewolf', 'WhiteWerewolf', 'KingOfWerewolves', 'Idiot']
uniqueIdentity = ['Predictor',
                  'Witch', 'Hunter', 'Guard', 'KingofWerewolf', 'WhiteWerewolf', 'KingOfWerewolves', 'Idiot']


def getBasePacket(src: Tuple[str, int], dest: Tuple[str, int]) -> dict:
    ret = {}
    ret['srcAddr'] = src[0]
    ret['srcPort'] = src[1]
    ret['destAddr'] = dest[0]
    ret['destPort'] = dest[1]
    return ret
