"""
The protocol for the werewolf game
"""

import os
import socket
import sys
from .api import ChunckedData, ReceiveThread, _recv, TimeLock, KillableThread, ReadInput
