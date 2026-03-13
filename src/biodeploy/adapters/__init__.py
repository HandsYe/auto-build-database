"""
适配器层

提供数据库适配器。
"""

from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.adapters.ensembl_adapter import EnsemblAdapter
from biodeploy.adapters.ucsc_adapter import UCSCAdapter
from biodeploy.adapters.adapter_registry import AdapterRegistry

# 自动注册适配器
registry = AdapterRegistry()
registry.register(NCBIAdapter)
registry.register(EnsemblAdapter)
registry.register(UCSCAdapter)

__all__ = [
    "BaseAdapter",
    "NCBIAdapter",
    "EnsemblAdapter",
    "UCSCAdapter",
    "AdapterRegistry",
]
