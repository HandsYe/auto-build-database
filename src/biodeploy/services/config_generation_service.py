"""
配置生成服务

提供配置文件生成功能，支持为不同工具生成配置文件。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.models.state import InstallationRecord


class ConfigGenerationService:
    """配置生成服务

    为安装的数据库生成配置文件，便于其他工具使用。
    """

    def generate(
        self,
        record: InstallationRecord,
        output_dir: Optional[Path] = None,
        formats: Optional[List[str]] = None,
    ) -> List[Path]:
        """生成配置文件

        Args:
            record: 安装记录
            output_dir: 输出目录，如果为None则使用安装目录
            formats: 配置格式列表 [yaml, json, env, sh]，如果为None则生成所有格式

        Returns:
            生成的配置文件路径列表
        """
        if output_dir is None:
            output_dir = record.install_path

        output_dir.mkdir(parents=True, exist_ok=True)

        if formats is None:
            formats = ["yaml", "env", "sh"]

        generated_files: List[Path] = []

        for fmt in formats:
            if fmt == "yaml":
                path = self._generate_yaml_config(record, output_dir)
                if path:
                    generated_files.append(path)
            elif fmt == "json":
                path = self._generate_json_config(record, output_dir)
                if path:
                    generated_files.append(path)
            elif fmt == "env":
                path = self._generate_env_config(record, output_dir)
                if path:
                    generated_files.append(path)
            elif fmt == "sh":
                path = self._generate_shell_config(record, output_dir)
                if path:
                    generated_files.append(path)

        return generated_files

    def _generate_yaml_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成YAML配置文件"""
        try:
            import yaml

            config = {
                "database": {
                    "name": record.name,
                    "version": record.version,
                    "path": str(record.install_path),
                    "files": [str(f) for f in record.files],
                    "index_files": [str(f) for f in record.index_files],
                },
                "environment": record.environment_variables,
            }

            output_path = output_dir / f"{record.name}_config.yaml"
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            return output_path
        except Exception:
            return None

    def _generate_json_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成JSON配置文件"""
        try:
            import json

            config = {
                "database": {
                    "name": record.name,
                    "version": record.version,
                    "path": str(record.install_path),
                    "files": [str(f) for f in record.files],
                    "index_files": [str(f) for f in record.index_files],
                },
                "environment": record.environment_variables,
            }

            output_path = output_dir / f"{record.name}_config.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return output_path
        except Exception:
            return None

    def _generate_env_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成环境变量配置文件 (.env格式)"""
        try:
            lines = [
                f"# {record.name} {record.version}",
                f"# Installation path: {record.install_path}",
                "",
            ]

            # 添加环境变量
            env_var_name = f"{record.name.upper()}_PATH"
            lines.append(f'{env_var_name}="{record.install_path}"')

            for key, value in record.environment_variables.items():
                lines.append(f'{key}="{value}"')

            output_path = output_dir / f"{record.name}.env"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return output_path
        except Exception:
            return None

    def _generate_shell_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成Shell配置文件"""
        try:
            lines = [
                "#!/bin/bash",
                f"# {record.name} {record.version} configuration",
                f"# Source this file: source {record.name}_config.sh",
                "",
            ]

            # 添加环境变量
            env_var_name = f"{record.name.upper()}_PATH"
            lines.append(f'export {env_var_name}="{record.install_path}"')

            for key, value in record.environment_variables.items():
                lines.append(f'export {key}="{value}"')

            # 添加PATH更新（如果适用）
            bin_dir = record.install_path / "bin"
            if bin_dir.exists():
                lines.append(f'export PATH="{bin_dir}:$PATH"')

            lines.append("")
            lines.append(f'echo "{record.name} {record.version} environment loaded"')

            output_path = output_dir / f"{record.name}_config.sh"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # 设置可执行权限
            output_path.chmod(0o755)

            return output_path
        except Exception:
            return None

    def generate_blast_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成BLAST配置文件 (.ncbirc)"""
        try:
            lines = [
                "; NCBI BLAST configuration",
                f"; Database: {record.name} {record.version}",
                "",
                "[BLAST]",
                f'BLASTDB="{record.install_path}"',
                "",
            ]

            output_path = output_dir / ".ncbirc"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return output_path
        except Exception:
            return None

    def generate_bwa_config(
        self,
        record: InstallationRecord,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成BWA配置文件"""
        try:
            # 查找索引文件
            index_files = list(record.install_path.glob("*.bwt"))
            if not index_files:
                return None

            index_prefix = index_files[0].stem

            lines = [
                "# BWA Index Configuration",
                f"# Database: {record.name} {record.version}",
                f"BWA_INDEX={record.install_path}/{index_prefix}",
                "",
            ]

            output_path = output_dir / "bwa_config.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return output_path
        except Exception:
            return None
