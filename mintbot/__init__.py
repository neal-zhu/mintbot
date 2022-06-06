"""
A simple mint rebot inspired by mycointool(mainly for study)
"""

from .block_listener import BlockListener as BlockListener
from .contract_verifier import ContractVerifier
from .types import *
from .storage import backend

__version__ = "0.0.1"
