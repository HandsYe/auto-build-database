"""
配置管理器

负责加载、保存和管理系统配置。
"""

import yaml
from pathlib import Path
from string import Template
from typing import Any, Dict, Optional

from biodeploy.models.config import Config
from biodeploy.models.errors import ConfigError, ErrorCode


class ConfigManager:
    """配置管理器

    负责管理系统配置，包括全局配置、项目配置和命令行参数的合并。

    Attributes:
        DEFAULT_CONFIG_PATH: 默认配置文件路径
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".biodeploy" / "config.yaml"

    def __init__(self) -> None:
        """初始化配置管理器"""
        self._global_config: Optional[Config] = None
        self._project_config: Optional[Dict[str, Any]] = None

    def load_global_config(self, config_path: Optional[Path] = None) -> Config:
        """加载全局配置

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径

        Returns:
            配置对象

        Raises:
            ConfigError: 配置文件不存在或格式错误
        """
        if config_path is None:
            config_path = self.DEFAULT_CONFIG_PATH

        if not config_path.exists():
            # 创建默认配置
            return self._create_default_config(config_path)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            self._global_config = Config.from_dict(data)
            return self._global_config

        except yaml.YAMLError as e:
            raise ConfigError(
                f"配置文件格式错误: {e}",
                ErrorCode.CONFIG_PARSE_ERROR,
                {"path": str(config_path), "error": str(e)},
            )
        except Exception as e:
            raise ConfigError(
                f"加载配置文件失败: {e}",
                ErrorCode.CONFIG_PARSE_ERROR,
                {"path": str(config_path), "error": str(e)},
            )

    def load_project_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """加载项目配置

        Args:
            config_path: 配置文件路径，如果为None则使用当前目录的biodeploy.yaml

        Returns:
            项目配置字典
        """
        if config_path is None:
            config_path = Path.cwd() / "biodeploy.yaml"

        if not config_path.exists():
            self._project_config = {}
            return self._project_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._project_config = yaml.safe_load(f) or {}
            return self._project_config

        except yaml.YAMLError as e:
            raise ConfigError(
                f"项目配置文件格式错误: {e}",
                ErrorCode.CONFIG_PARSE_ERROR,
                {"path": str(config_path), "error": str(e)},
            )

    def merge_configs(self, cli_args: Optional[Dict[str, Any]] = None) -> Config:
        """合并配置

        合并全局配置、项目配置和命令行参数。

        Args:
            cli_args: 命令行参数字典

        Returns:
            合并后的配置对象
        """
        # 加载全局配置
        if self._global_config is None:
            global_config = self.load_global_config()
        else:
            global_config = self._global_config

        # 加载项目配置
        if self._project_config is None:
            self.load_project_config()

        # 合并项目配置到全局配置
        merged = self._merge_dicts(global_config.to_dict(), self._project_config or {})

        # 合并命令行参数
        if cli_args:
            merged = self._merge_dicts(merged, cli_args)

        # 转换为Config对象
        return Config.from_dict(merged)

    def get_database_config(
        self, database: str, global_config: Optional[Config] = None
    ) -> Dict[str, Any]:
        """获取数据库特定配置

        Args:
            database: 数据库名称
            global_config: 全局配置，如果为None则使用已加载的配置

        Returns:
            数据库配置字典
        """
        if global_config is None:
            global_config = self._global_config or self.load_global_config()

        # 从全局配置中获取
        db_config = global_config.databases.get(database, {})

        # 从项目配置中获取
        if self._project_config:
            project_db_config = self._project_config.get("databases", {}).get(database, {})
            db_config = self._merge_dicts(db_config, project_db_config)

        # 展开变量
        db_config = self._expand_variables(db_config, global_config)

        return db_config

    def save_config(self, config: Config, config_path: Path) -> None:
        """保存配置

        Args:
            config: 配置对象
            config_path: 配置文件路径

        Raises:
            ConfigError: 保存配置失败
        """
        try:
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            raise ConfigError(
                f"保存配置文件失败: {e}",
                ErrorCode.CONFIG_SAVE_ERROR,
                {"path": str(config_path), "error": str(e)},
            )

    def _create_default_config(self, config_path: Path) -> Config:
        """创建默认配置

        Args:
            config_path: 配置文件路径

        Returns:
            默认配置对象
        """
        config = Config()

        # 保存默认配置
        self.save_config(config, config_path)

        self._global_config = config
        return config

    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并字典

        递归合并两个字典，override中的值会覆盖base中的值。

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            合并后的字典
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def _expand_variables(self, config: Dict[str, Any], global_config: Config) -> Dict[str, Any]:
        """展开变量

        展开配置中的变量引用，如 ${install_path}。

        Args:
            config: 配置字典
            global_config: 全局配置

        Returns:
            展开变量后的配置字典
        """
        variables = {
            "install_path": str(global_config.install.default_install_path),
            "temp_path": str(global_config.install.temp_path),
            "home": str(Path.home()),
        }

        return self._expand_dict(config, variables)

    def _expand_dict(self, data: Any, variables: Dict[str, str]) -> Any:
        """递归展开字典中的变量

        Args:
            data: 数据
            variables: 变量字典

        Returns:
            展开变量后的数据
        """
        if isinstance(data, str):
            template = Template(data)
            return template.safe_substitute(variables)
        elif isinstance(data, dict):
            return {k: self._expand_dict(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_dict(item, variables) for item in data]
        else:
            return data
