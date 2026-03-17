"""
适配器层

提供数据库适配器。
"""

from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.adapters.ensembl_adapter import EnsemblAdapter
from biodeploy.adapters.ucsc_adapter import UCSCAdapter
from biodeploy.adapters.eggnog_adapter import EggNOGAdapter
from biodeploy.adapters.kegg_adapter import KEGGAdapter
from biodeploy.adapters.common_adapters import (
    CAZyAdapter,
    CARDAdapter,
    VFDBAdapter,
    GOAdapter,
    COGAdapter,
    SwissProtAdapter,
)
from biodeploy.adapters.adapter_registry import AdapterRegistry

# 自动注册适配器
registry = AdapterRegistry()
registry.register(NCBIAdapter)
registry.register(EnsemblAdapter)
registry.register(UCSCAdapter)
registry.register(EggNOGAdapter)
registry.register(KEGGAdapter)
registry.register(CAZyAdapter)
registry.register(CARDAdapter)
registry.register(VFDBAdapter)
registry.register(GOAdapter)
registry.register(COGAdapter)
registry.register(SwissProtAdapter)

__all__ = [
    "BaseAdapter",
    "NCBIAdapter",
    "EnsemblAdapter",
    "UCSCAdapter",
    "EggNOGAdapter",
    "KEGGAdapter",
    "CAZyAdapter",
    "CARDAdapter",
    "VFDBAdapter",
    "GOAdapter",
    "COGAdapter",
    "SwissProtAdapter",
    "AdapterRegistry",
]
