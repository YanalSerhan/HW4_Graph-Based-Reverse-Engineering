"""
Main package initialization for graph_rev_eng.
"""
from .shared.version import __version__
from .sdk.sdk import ReverseEngineeringSDK

__all__ = ["__version__", "ReverseEngineeringSDK"]
