"""
依赖管理器

检查和安装系统依赖和Python依赖。
"""

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from biodeploy.infrastructure.logger import get_logger


class DependencyManager:
    """依赖管理器

    负责检查和安装系统依赖。
    """

    # 常见的系统依赖
    COMMON_DEPENDENCIES = {
        "wget": {
            "description": "File download utility",
            "check_cmd": ["wget", "--version"],
            "ubuntu": "wget",
            "centos": "wget",
            "macos": "wget",
        },
        "curl": {
            "description": "Command line tool for transferring data",
            "check_cmd": ["curl", "--version"],
            "ubuntu": "curl",
            "centos": "curl",
            "macos": "curl",
        },
        "tar": {
            "description": "Archiving utility",
            "check_cmd": ["tar", "--version"],
            "ubuntu": "tar",
            "centos": "tar",
            "macos": "gnu-tar",
        },
        "gzip": {
            "description": "Compression utility",
            "check_cmd": ["gzip", "--version"],
            "ubuntu": "gzip",
            "centos": "gzip",
            "macos": "gzip",
        },
        "pigz": {
            "description": "Parallel gzip",
            "check_cmd": ["pigz", "--version"],
            "ubuntu": "pigz",
            "centos": "pigz",
            "macos": "pigz",
        },
        "rsync": {
            "description": "Remote file sync",
            "check_cmd": ["rsync", "--version"],
            "ubuntu": "rsync",
            "centos": "rsync",
            "macos": "rsync",
        },
    }

    # 生物信息学工具依赖
    BIOINFO_DEPENDENCIES = {
        "blast": {
            "description": "BLAST sequence alignment",
            "check_cmd": ["blastn", "-version"],
            "ubuntu": "ncbi-blast+",
            "centos": "ncbi-blast+",
            "macos": "blast",
        },
        "bwa": {
            "description": "BWA sequence aligner",
            "check_cmd": ["bwa"],
            "ubuntu": "bwa",
            "centos": "bwa",
            "macos": "bwa",
        },
        "bowtie2": {
            "description": "Bowtie2 sequence aligner",
            "check_cmd": ["bowtie2", "--version"],
            "ubuntu": "bowtie2",
            "centos": "bowtie2",
            "macos": "bowtie2",
        },
        "samtools": {
            "description": "SAM/BAM file processing",
            "check_cmd": ["samtools", "--version"],
            "ubuntu": "samtools",
            "centos": "samtools",
            "macos": "samtools",
        },
        "hisat2": {
            "description": "HISAT2 splice-aware aligner",
            "check_cmd": ["hisat2", "--version"],
            "ubuntu": "hisat2",
            "centos": "hisat2",
            "macos": "hisat2",
        },
    }

    def __init__(self):
        self._logger = get_logger("dependency_manager")

    def check_dependency(self, name: str) -> bool:
        """检查单个依赖是否可用

        Args:
            name: 依赖名称

        Returns:
            如果可用返回True，否则返回False
        """
        dep_info = self.COMMON_DEPENDENCIES.get(name) or self.BIOINFO_DEPENDENCIES.get(name)
        if not dep_info:
            # 尝试直接检查命令
            return shutil.which(name) is not None

        try:
            result = subprocess.run(
                dep_info["check_cmd"],
                capture_output=True,
                check=False,
            )
            return result.returncode in [0, 1]  # 有些工具返回1表示没有参数
        except Exception:
            return False

    def check_dependencies(self, dependencies: List[str]) -> Tuple[List[str], List[str]]:
        """检查多个依赖

        Args:
            dependencies: 依赖名称列表

        Returns:
            (可用依赖列表, 缺失依赖列表)
        """
        available = []
        missing = []

        for dep in dependencies:
            if self.check_dependency(dep):
                available.append(dep)
            else:
                missing.append(dep)

        return available, missing

    def get_missing_dependencies(
        self,
        include_bioinfo: bool = False,
    ) -> List[str]:
        """获取所有缺失的依赖

        Args:
            include_bioinfo: 是否包括生物信息学工具

        Returns:
            缺失依赖名称列表
        """
        dependencies = list(self.COMMON_DEPENDENCIES.keys())
        if include_bioinfo:
            dependencies.extend(self.BIOINFO_DEPENDENCIES.keys())

        _, missing = self.check_dependencies(dependencies)
        return missing

    def get_install_command(
        self,
        dependency: str,
        platform: str = "ubuntu",
    ) -> Optional[str]:
        """获取依赖安装命令

        Args:
            dependency: 依赖名称
            platform: 平台 (ubuntu, centos, macos)

        Returns:
            安装命令，如果不支持返回None
        """
        dep_info = self.COMMON_DEPENDENCIES.get(dependency) or self.BIOINFO_DEPENDENCIES.get(dependency)
        if not dep_info:
            return None

        package_name = dep_info.get(platform)
        if not package_name:
            return None

        if platform == "ubuntu":
            return f"sudo apt-get install -y {package_name}"
        elif platform == "centos":
            return f"sudo yum install -y {package_name}"
        elif platform == "macos":
            return f"brew install {package_name}"

        return None

    def check_system_requirements(
        self,
        min_disk_space: int = 0,
        min_memory: int = 0,
    ) -> Dict[str, Any]:
        """检查系统要求

        Args:
            min_disk_space: 最小磁盘空间（字节）
            min_memory: 最小内存（字节）

        Returns:
            系统要求检查结果
        """
        import shutil

        result = {
            "disk_space_ok": True,
            "memory_ok": True,
            "details": {},
        }

        # 检查磁盘空间
        if min_disk_space > 0:
            disk_usage = shutil.disk_usage(".")
            result["disk_space_ok"] = disk_usage.free >= min_disk_space
            result["details"]["disk_free"] = disk_usage.free
            result["details"]["disk_required"] = min_disk_space

        # 检查内存
        if min_memory > 0:
            try:
                import psutil
                memory = psutil.virtual_memory()
                result["memory_ok"] = memory.available >= min_memory
                result["details"]["memory_available"] = memory.available
                result["details"]["memory_required"] = min_memory
            except ImportError:
                result["memory_ok"] = None

        return result

    def validate_before_install(
        self,
        dependencies: List[str],
        min_disk_space: int = 0,
    ) -> Tuple[bool, List[str]]:
        """安装前验证

        Args:
            dependencies: 所需依赖列表
            min_disk_space: 最小磁盘空间

        Returns:
            (是否通过验证, 错误信息列表)
        """
        errors = []

        # 检查依赖
        available, missing = self.check_dependencies(dependencies)
        if missing:
            errors.append(f"Missing dependencies: {', '.join(missing)}")
            for dep in missing:
                cmd = self.get_install_command(dep)
                if cmd:
                    errors.append(f"  Install {dep}: {cmd}")

        # 检查磁盘空间
        if min_disk_space > 0:
            import shutil
            disk_usage = shutil.disk_usage(".")
            if disk_usage.free < min_disk_space:
                errors.append(
                    f"Insufficient disk space: {disk_usage.free / (1024**3):.2f} GB available, "
                    f"{min_disk_space / (1024**3):.2f} GB required"
                )

        return len(errors) == 0, errors
