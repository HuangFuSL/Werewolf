from ..abstraction import *
from typing import Tuple, Union
from itertools import groupby


def getVotingResult(vote: List[int], policevote: Optional[int] = None) -> List[int]:
    """
    Count the vote result and the return the candidates with most votes

    ### Parameter

    - vote: `List[int]`, the vote result

    ### Return

    `List[int]`, the candidates with most votes
    """
    voteList: dict = {i: float(len(list(j))) for i, j in groupby(sorted(vote))}
    # the police case
    if policevote is not None:
        if policevote in voteList.keys():
            voteList[policevote] += 1.5
        else:
            voteList[policevote] = 1.5
    ret: List[int] = []
    max: int = 0
    for i in voteList:
        if voteList[i] > max:
            ret.clear()
        if voteList[i] >= max:
            ret.append(i)

    return ret


def getIdentityCode(
    obj: Union[Villager, Wolf, KingOfWerewolves,
               WhiteWerewolf, Hunter, Guard, Predictor, Witch, Idiot]
) -> int:
    """
    Get the identity code for the packet.
    """
    assert isinstance(obj, Person)
    assert type(obj) != Person
    assert type(obj) != SkilledPerson
    return obj.type


availableIdentity = ['Villager', 'Wolf', 'Predictor',
                     'Witch', 'Hunter', 'Guard', 'KingofWerewolf', 'WhiteWerewolf', 'KingOfWerewolves', 'Idiot']
uniqueIdentity = ['Predictor',
                  'Witch', 'Hunter', 'Guard', 'KingofWerewolf', 'WhiteWerewolf', 'KingOfWerewolves', 'Idiot']


def getBasePacket(src: Tuple[str, int], dest: Tuple[str, int]) -> dict:
    ret = {'srcAddr': src[0], 'srcPort': src[1],
           'destAddr': dest[0], 'destPort': dest[1]}
    return ret
