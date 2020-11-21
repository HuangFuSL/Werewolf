from typing import Dict
from .preset6 import *
from .preset8 import *
from .preset10 import *
from .preset12 import *
from ..server.util import availableIdentity as a, uniqueIdentity as u


def customizePreset() -> Dict[str, int]:
    ret: Dict[str, int] = {}
    val: int = 0
    for identity in a:
        if identity in u:
            val = 2
            while val >= 1:
                val = int(
                    input("Please enter the number of %s(s).\n" % (identity,)))
        else:
            val = 0
            while val == 0:
                val = int(
                    input("Please enter the number of %s(s).\n" % (identity,)))

        ret[identity] = val

    return ret
