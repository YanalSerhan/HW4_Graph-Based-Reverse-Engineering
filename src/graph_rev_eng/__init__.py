"""
Main package initialization for graph_rev_eng.
"""

from .sdk.sdk import ReverseEngineeringSDK
from .shared.version import __version__

__all__ = ["__version__", "ReverseEngineeringSDK"]
