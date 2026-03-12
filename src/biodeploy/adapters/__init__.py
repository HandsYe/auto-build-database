"""
适配器层

提供数据库适配器。
"""

from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.adapters.ncbi_adapter import NCBIAdapter

__all__ = [
    "BaseAdapter",
    "NCBIAdapter",
]
