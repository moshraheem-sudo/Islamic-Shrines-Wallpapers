"""
Adapters package for Islamic Shrines Wallpapers.
Provides unified interfaces for multiple holy shrine media centers.
"""
from .base import BaseAdapter, DiscoveredItem
from .imamali import ImamAliAdapter
from .alaskarian import AlAskarianAdapter

ADAPTER_MAP = {
    "ImamAliAdapter": ImamAliAdapter,
    "AlAskarianAdapter": AlAskarianAdapter,
}

def get_adapter(name: str):
    return ADAPTER_MAP.get(name)
