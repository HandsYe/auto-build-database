"""
适配器注册表

管理所有数据库适配器的注册和查找。
"""

from typing import Dict, List, Optional, Type

from biodeploy.adapters.base_adapter import BaseAdapter


class AdapterRegistry:
    """适配器注册表

    管理所有数据库适配器的注册和查找，支持动态加载适配器。
    """

    _instance: Optional["AdapterRegistry"] = None
    _adapters: Dict[str, Type[BaseAdapter]] = {}

    def __new__(cls) -> "AdapterRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, adapter_class: Type[BaseAdapter]) -> None:
        """注册适配器

        Args:
            adapter_class: 适配器类
        """
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
        adapter_class = self._adapters.get(name)
        if adapter_class:
            return adapter_class()
        return None

    def list_adapters(self) -> List[str]:
        """列出所有已注册的适配器

        Returns:
            数据库名称列表
        """
        return list(self._adapters.keys())

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
