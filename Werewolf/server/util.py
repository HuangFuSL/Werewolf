from .abstraction import *
from typing import Tuple, Union, List, Optional, Dict
from itertools import groupby


def mergeVotingResult(vote: List[int], policevote: Optional[int] = None) -> Dict[int, float]:
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

    return voteList


def getVotingResult(merged: Dict[int, float]) -> List[int]:
    ret: List[int] = []
    maxV: float = 0
    for i in merged:
        if merged[i] > maxV:
            maxV = merged[i]
            ret.clear()
        if merged[i] >= maxV:
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
