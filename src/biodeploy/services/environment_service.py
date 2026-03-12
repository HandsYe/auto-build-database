"""
环境变量服务

提供环境变量设置和管理功能。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from biodeploy.infrastructure.logger import logger
from biodeploy.models.state import InstallationRecord


class EnvironmentService:
    """环境变量服务

    负责设置和管理环境变量。
    """

    SHELL_CONFIG_FILES = {
        "bash": ".bashrc",
        "zsh": ".zshrc",
        "fish": ".config/fish/config.fish",
    }

    def __init__(self):
        self._logger = logger.get_logger("environment_service")

    def set_environment(
        self,
        variables: Dict[str, str],
        persist: bool = False,
        shell: Optional[str] = None,
    ) -> bool:
        """设置环境变量

        Args:
            variables: 环境变量字典
            persist: 是否持久化到shell配置文件
            shell: Shell类型 (bash, zsh, fish)，如果为None则自动检测

        Returns:
            如果设置成功返回True，否则返回False
        """
        try:
            # 设置当前进程的环境变量
            for key, value in variables.items():
                os.environ[key] = value
                self._logger.debug(f"设置环境变量: {key}={value}")

            # 持久化到shell配置文件
            if persist:
                return self._persist_to_shell_config(variables, shell)

            return True
        except Exception as e:
            self._logger.error(f"设置环境变量失败: {e}")
            return False

    def get_environment(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值，如果不存在返回默认值
        """
        return os.environ.get(key, default)

    def unset_environment(self, key: str, persist: bool = False) -> bool:
        """取消设置环境变量

        Args:
            key: 环境变量名
            persist: 是否从shell配置文件中移除

        Returns:
            如果移除成功返回True，否则返回False
        """
        try:
            if key in os.environ:
                del os.environ[key]

            if persist:
                return self._remove_from_shell_config(key)

            return True
        except Exception as e:
            self._logger.error(f"取消设置环境变量失败: {e}")
            return False

    def generate_export_script(
        self,
        record: InstallationRecord,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """生成环境变量导出脚本

        Args:
            record: 安装记录
            output_path: 输出路径，如果为None则使用默认路径

        Returns:
            生成的脚本路径，如果失败返回None
        """
        if output_path is None:
            output_path = record.install_path / f"{record.name}_env.sh"

        try:
            lines = [
                "#!/bin/bash",
                f"# {record.name} {record.version} environment setup",
                "",
            ]

            # 添加安装路径环境变量
            env_var_name = f"{self._sanitize_name(record.name)}_PATH"
            lines.append(f'export {env_var_name}="{record.install_path}"')

            # 添加其他环境变量
            for key, value in record.environment_variables.items():
                lines.append(f'export {key}="{value}"')

            # 添加PATH更新
            bin_dirs = [
                record.install_path / "bin",
                record.install_path / "scripts",
            ]
            for bin_dir in bin_dirs:
                if bin_dir.exists():
                    lines.append(f'export PATH="{bin_dir}:$PATH"')

            # 添加索引路径（如果存在）
            index_dirs = list(record.install_path.glob("*_index"))
            if index_dirs:
                index_path = index_dirs[0]
                index_var_name = f"{self._sanitize_name(record.name)}_INDEX"
                lines.append(f'export {index_var_name}="{index_path}"')

            lines.append("")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            output_path.chmod(0o755)
            self._logger.info(f"生成环境变量脚本: {output_path}")

            return output_path
        except Exception as e:
            self._logger.error(f"生成环境变量脚本失败: {e}")
            return None

    def update_shell_config(
        self,
        record: InstallationRecord,
        shell: Optional[str] = None,
    ) -> bool:
        """更新shell配置文件

        Args:
            record: 安装记录
            shell: Shell类型，如果为None则自动检测

        Returns:
            如果更新成功返回True，否则返回False
        """
        try:
            config_path = self._get_shell_config_path(shell)
            if not config_path:
                self._logger.warning("无法确定shell配置文件路径")
                return False

            # 生成要添加的内容
            lines = [
                "",
                f"# >>> {record.name} {record.version} >>>",
                f'# Added by BioDeploy',
            ]

            # 添加source命令
            env_script = record.install_path / f"{record.name}_env.sh"
            if env_script.exists():
                lines.append(f'if [ -f "{env_script}" ]; then')
                lines.append(f'    source "{env_script}"')
                lines.append('fi')

            lines.append(f"# <<< {record.name} <<<")
            lines.append("")

            content = "\n".join(lines)

            # 检查是否已存在
            if config_path.exists():
                existing_content = config_path.read_text(encoding="utf-8")
                if f"# >>> {record.name}" in existing_content:
                    self._logger.info(f"{record.name} 已在shell配置中")
                    return True

            # 追加到配置文件
            with open(config_path, "a", encoding="utf-8") as f:
                f.write(content)

            self._logger.info(f"更新shell配置文件: {config_path}")
            return True

        except Exception as e:
            self._logger.error(f"更新shell配置文件失败: {e}")
            return False

    def remove_from_shell_config(
        self,
        record: InstallationRecord,
        shell: Optional[str] = None,
    ) -> bool:
        """从shell配置文件中移除数据库配置

        Args:
            record: 安装记录
            shell: Shell类型，如果为None则自动检测

        Returns:
            如果移除成功返回True，否则返回False
        """
        try:
            config_path = self._get_shell_config_path(shell)
            if not config_path or not config_path.exists():
                return True

            content = config_path.read_text(encoding="utf-8")

            # 使用正则表达式移除标记块
            pattern = rf"\n# >>> {record.name}.*?# <<< {record.name} <<<\n"
            new_content = re.sub(pattern, "", content, flags=re.DOTALL)

            if new_content != content:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self._logger.info(f"从shell配置中移除 {record.name}")

            return True

        except Exception as e:
            self._logger.error(f"从shell配置文件移除失败: {e}")
            return False

    def _get_shell_config_path(self, shell: Optional[str] = None) -> Optional[Path]:
        """获取shell配置文件路径"""
        home = Path.home()

        if shell:
            config_file = self.SHELL_CONFIG_FILES.get(shell)
            if config_file:
                return home / config_file
            return None

        # 自动检测shell
        shell_path = os.environ.get("SHELL", "")
        if "zsh" in shell_path:
            return home / self.SHELL_CONFIG_FILES["zsh"]
        elif "fish" in shell_path:
            return home / self.SHELL_CONFIG_FILES["fish"]
        else:
            # 默认bash
            return home / self.SHELL_CONFIG_FILES["bash"]

    def _persist_to_shell_config(
        self,
        variables: Dict[str, str],
        shell: Optional[str] = None,
    ) -> bool:
        """持久化环境变量到shell配置文件"""
        config_path = self._get_shell_config_path(shell)
        if not config_path:
            return False

        try:
            lines = ["# BioDeploy environment variables"]
            for key, value in variables.items():
                lines.append(f'export {key}="{value}"')
            lines.append("")

            content = "\n".join(lines)

            # 检查是否已存在
            if config_path.exists():
                existing_content = config_path.read_text(encoding="utf-8")
                if "# BioDeploy environment variables" in existing_content:
                    # 更新现有配置
                    pattern = r"# BioDeploy environment variables.*?\n(?=#|$)"
                    new_content = re.sub(pattern, content, existing_content, flags=re.DOTALL)
                    content = new_content
                else:
                    content = existing_content + "\n" + content

            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True
        except Exception as e:
            self._logger.error(f"持久化环境变量失败: {e}")
            return False

    def _remove_from_shell_config(self, key: str) -> bool:
        """从shell配置文件中移除环境变量"""
        for shell, config_file in self.SHELL_CONFIG_FILES.items():
            config_path = Path.home() / config_file
            if not config_path.exists():
                continue

            try:
                content = config_path.read_text(encoding="utf-8")
                lines = content.split("\n")
                new_lines = [line for line in lines if not line.strip().startswith(f"export {key}=")]

                if len(lines) != len(new_lines):
                    with open(config_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(new_lines))
                    return True
            except Exception:
                continue

        return False

    def _sanitize_name(self, name: str) -> str:
        """将数据库名称转换为合法的环境变量名"""
        # 替换非法字符为下划线，转换为大写
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name).upper()
        # 确保不以数字开头
        if sanitized and sanitized[0].isdigit():
            sanitized = "DB_" + sanitized
        return sanitized
