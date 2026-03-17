"""
适配器注册表

管理所有数据库适配器的注册和查找。
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Type

from biodeploy.adapters.base_adapter import BaseAdapter


class AdapterRegistry:
    """适配器注册表

    管理所有数据库适配器的注册和查找，支持动态加载适配器。
    """

    _instance: Optional["AdapterRegistry"] = None
    _adapters: Dict[str, Type[BaseAdapter]] = {}
    _builtins_loaded: bool = False

    def __new__(cls) -> "AdapterRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_builtins_loaded(self) -> None:
        """确保内置适配器已加载并注册。

        CLI/服务端代码经常只实例化 AdapterRegistry 而不显式 import `biodeploy.adapters`，
        这会导致注册表为空。这里做一次惰性导入以确保内置适配器注册发生。
        """
        if self._builtins_loaded:
            return
        try:
            # 触发 `biodeploy/adapters/__init__.py` 中的注册逻辑
            import biodeploy.adapters  # noqa: F401
        finally:
            self._builtins_loaded = True

    def register(self, adapter_class: Type[BaseAdapter]) -> None:
        """注册适配器

        Args:
            adapter_class: 适配器类
        """
        self._ensure_builtins_loaded()
        # 创建临时实例获取名称
        temp_instance = adapter_class()
        name = temp_instance.database_name
        self._adapters[name] = adapter_class

    def unregister(self, name: str) -> bool:
        """注销适配器

        Args:
            name: 数据库名称

        Returns:
            如果成功注销返回True，否则返回False
        """
        if name in self._adapters:
            del self._adapters[name]
            return True
        return False

    def get(self, name: str) -> Optional[BaseAdapter]:
        """获取适配器实例

        Args:
            name: 数据库名称

        Returns:
            适配器实例，如果未找到返回None
        """
        self._ensure_builtins_loaded()
        adapter_class = self._adapters.get(name)
        if adapter_class:
            return adapter_class()
        return self._resolve_dynamic_adapter(name)

    def _resolve_dynamic_adapter(self, name: str) -> Optional[BaseAdapter]:
        """解析“动态适配器名称”并返回实例。

        许多适配器支持多种变体（如 `ncbi_refseq_protein`、`kegg_pathway` 等），
        但注册表只会注册默认构造参数对应的名称。这里补一层解析，使得：
        - `biodeploy list` 能列出全部可下载变体
        - `biodeploy install <name>` 能直接安装这些变体
        """
        try:
            if name.startswith("ncbi_"):
                from biodeploy.adapters.ncbi_adapter import NCBIAdapter

                db_type = name.removeprefix("ncbi_")
                if db_type in getattr(NCBIAdapter, "DATABASE_TYPES", {}):
                    return NCBIAdapter(db_type=db_type)

            if name.startswith("eggnog_"):
                from biodeploy.adapters.eggnog_adapter import EggNOGAdapter

                db_type = name.removeprefix("eggnog_")
                if db_type in getattr(EggNOGAdapter, "DATABASE_TYPES", {}):
                    return EggNOGAdapter(db_type=db_type)

            if name.startswith("kegg_"):
                from biodeploy.adapters.kegg_adapter import KEGGAdapter

                db_type = name.removeprefix("kegg_")
                if db_type in getattr(KEGGAdapter, "DATABASE_TYPES", {}):
                    return KEGGAdapter(db_type=db_type)

            if name.startswith("ensembl_"):
                from biodeploy.adapters.ensembl_adapter import EnsemblAdapter

                db_type = name.removeprefix("ensembl_")
                if db_type in getattr(EnsemblAdapter, "DATABASE_TYPES", {}):
                    return EnsemblAdapter(db_type=db_type)

            if name.startswith("ucsc_"):
                from biodeploy.adapters.ucsc_adapter import UCSCAdapter

                rest = name.removeprefix("ucsc_")
                parts = rest.split("_", 1)
                if len(parts) == 2:
                    db_name, genome = parts
                    if db_name in getattr(UCSCAdapter, "DATABASES", {}):
                        return UCSCAdapter(db_name=db_name, genome=genome)

        except Exception:
            # 动态解析不应影响主流程；失败则返回None，让上层报“未找到适配器”
            return None

        return None

    def list_adapters(self) -> List[str]:
        """列出所有已注册的适配器

        Returns:
            数据库名称列表
        """
        self._ensure_builtins_loaded()
        names = set(self._adapters.keys())

        # 生成常见“变体名称”，让用户可 discover
        try:
            from biodeploy.adapters.ncbi_adapter import NCBIAdapter

            names.update({f"ncbi_{k}" for k in getattr(NCBIAdapter, "DATABASE_TYPES", {}).keys()})
        except Exception:
            pass

        try:
            from biodeploy.adapters.eggnog_adapter import EggNOGAdapter

            names.update({f"eggnog_{k}" for k in getattr(EggNOGAdapter, "DATABASE_TYPES", {}).keys()})
        except Exception:
            pass

        try:
            from biodeploy.adapters.kegg_adapter import KEGGAdapter

            names.update({f"kegg_{k}" for k in getattr(KEGGAdapter, "DATABASE_TYPES", {}).keys()})
        except Exception:
            pass

        try:
            from biodeploy.adapters.ensembl_adapter import EnsemblAdapter

            names.update({f"ensembl_{k}" for k in getattr(EnsemblAdapter, "DATABASE_TYPES", {}).keys()})
        except Exception:
            pass

        try:
            from biodeploy.adapters.ucsc_adapter import UCSCAdapter

            # UCSC 的 genome 种类很多，这里只列常用基因组版本，保证“简单易用”
            popular_genomes = ["hg38", "hg19", "mm39", "mm10"]
            for db_name in getattr(UCSCAdapter, "DATABASES", {}).keys():
                for genome in popular_genomes:
                    names.add(f"ucsc_{db_name}_{genome}")
        except Exception:
            pass

        return sorted(names)

    def is_registered(self, name: str) -> bool:
        """检查适配器是否已注册

        Args:
            name: 数据库名称

        Returns:
            如果已注册返回True，否则返回False
        """
        return name in self._adapters

    def get_all_adapters(self) -> Dict[str, BaseAdapter]:
        """获取所有适配器实例

        Returns:
            数据库名称到适配器实例的映射
        """
        return {
            name: adapter_class()
            for name, adapter_class in self._adapters.items()
        }


def register_adapter(adapter_class: Type[BaseAdapter]) -> Type[BaseAdapter]:
    """适配器注册装饰器

    使用此装饰器自动注册适配器类。

    Example:
        @register_adapter
        class NCBIAdapter(BaseAdapter):
            pass
    """
    registry = AdapterRegistry()
    registry.register(adapter_class)
    return adapter_class


# 全局注册表实例
adapter_registry = AdapterRegistry()
