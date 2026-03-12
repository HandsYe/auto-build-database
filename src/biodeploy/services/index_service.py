"""
索引服务

提供数据库索引构建功能。
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.models.errors import IndexError, ErrorCode
from biodeploy.infrastructure.logger import get_logger


class IndexService:
    """索引服务

    提供数据库索引构建功能，支持BLAST、BWA、Bowtie2、Hisat2等工具。

    Attributes:
        supported_index_types: 支持的索引类型列表
    """

    SUPPORTED_INDEX_TYPES = [
        "blast",
        "bwa",
        "bowtie2",
        "hisat2",
        "samtools",
        "star",
    ]

    def __init__(self) -> None:
        """初始化索引服务"""
        self.logger = get_logger("index_service")

    def build_index(
        self,
        database_path: Path,
        index_type: str,
        output_path: Optional[Path] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """构建数据库索引

        Args:
            database_path: 数据库路径
            index_type: 索引类型
            output_path: 输出路径，如果为None则在database_path下创建
            options: 索引构建选项

        Returns:
            如果成功构建返回True，否则返回False
        """
        database_path = Path(database_path)
        options = options or {}

        if index_type not in self.SUPPORTED_INDEX_TYPES:
            raise IndexError(
                f"不支持的索引类型: {index_type}",
                ErrorCode.INDEX_TYPE_NOT_SUPPORTED,
                {"index_type": index_type, "supported": self.SUPPORTED_INDEX_TYPES},
            )

        if not database_path.exists():
            raise IndexError(
                f"数据库路径不存在: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 设置输出路径
        if output_path is None:
            output_path = database_path / "indexes" / index_type
        else:
            output_path = Path(output_path)

        output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"开始构建 {index_type} 索引: {database_path}")

        try:
            if index_type == "blast":
                return self._build_blast_index(database_path, output_path, options)
            elif index_type == "bwa":
                return self._build_bwa_index(database_path, output_path, options)
            elif index_type == "bowtie2":
                return self._build_bowtie2_index(database_path, output_path, options)
            elif index_type == "hisat2":
                return self._build_hisat2_index(database_path, output_path, options)
            elif index_type == "samtools":
                return self._build_samtools_index(database_path, output_path, options)
            elif index_type == "star":
                return self._build_star_index(database_path, output_path, options)
            else:
                return False

        except Exception as e:
            self.logger.error(f"构建索引失败: {e}")
            return False

    def _build_blast_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建BLAST索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查makeblastdb是否可用
        if not shutil.which("makeblastdb"):
            raise IndexError(
                "makeblastdb工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "makeblastdb"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.faa")) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 为每个FASTA文件构建索引
        for fasta_file in fasta_files:
            db_name = output_path / fasta_file.stem

            cmd = [
                "makeblastdb",
                "-in",
                str(fasta_file),
                "-dbtype",
                options.get("dbtype", "prot"),
                "-out",
                str(db_name),
                "-parse_seqids",
            ]

            self.logger.debug(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise IndexError(
                    f"makeblastdb执行失败: {result.stderr}",
                    ErrorCode.INDEX_BUILD_FAILED,
                    {"command": " ".join(cmd), "error": result.stderr},
                )

        self.logger.info(f"BLAST索引构建完成: {output_path}")
        return True

    def _build_bwa_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建BWA索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查bwa是否可用
        if not shutil.which("bwa"):
            raise IndexError(
                "bwa工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "bwa"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 为每个FASTA文件构建索引
        for fasta_file in fasta_files:
            # BWA索引文件会创建在FASTA文件所在目录
            # 我们需要将FASTA文件链接到输出目录
            link_file = output_path / fasta_file.name
            if not link_file.exists():
                link_file.symlink_to(fasta_file)

            cmd = ["bwa", "index", str(link_file)]

            self.logger.debug(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise IndexError(
                    f"bwa index执行失败: {result.stderr}",
                    ErrorCode.INDEX_BUILD_FAILED,
                    {"command": " ".join(cmd), "error": result.stderr},
                )

        self.logger.info(f"BWA索引构建完成: {output_path}")
        return True

    def _build_bowtie2_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建Bowtie2索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查bowtie2-build是否可用
        if not shutil.which("bowtie2-build"):
            raise IndexError(
                "bowtie2-build工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "bowtie2-build"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 为每个FASTA文件构建索引
        for fasta_file in fasta_files:
            db_name = output_path / fasta_file.stem

            cmd = ["bowtie2-build", str(fasta_file), str(db_name)]

            self.logger.debug(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise IndexError(
                    f"bowtie2-build执行失败: {result.stderr}",
                    ErrorCode.INDEX_BUILD_FAILED,
                    {"command": " ".join(cmd), "error": result.stderr},
                )

        self.logger.info(f"Bowtie2索引构建完成: {output_path}")
        return True

    def _build_hisat2_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建Hisat2索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查hisat2-build是否可用
        if not shutil.which("hisat2-build"):
            raise IndexError(
                "hisat2-build工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "hisat2-build"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 为每个FASTA文件构建索引
        for fasta_file in fasta_files:
            db_name = output_path / fasta_file.stem

            cmd = ["hisat2-build", str(fasta_file), str(db_name)]

            self.logger.debug(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise IndexError(
                    f"hisat2-build执行失败: {result.stderr}",
                    ErrorCode.INDEX_BUILD_FAILED,
                    {"command": " ".join(cmd), "error": result.stderr},
                )

        self.logger.info(f"Hisat2索引构建完成: {output_path}")
        return True

    def _build_samtools_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建Samtools索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查samtools是否可用
        if not shutil.which("samtools"):
            raise IndexError(
                "samtools工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "samtools"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # 为每个FASTA文件构建索引
        for fasta_file in fasta_files:
            # 将FASTA文件链接到输出目录
            link_file = output_path / fasta_file.name
            if not link_file.exists():
                link_file.symlink_to(fasta_file)

            cmd = ["samtools", "faidx", str(link_file)]

            self.logger.debug(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise IndexError(
                    f"samtools faidx执行失败: {result.stderr}",
                    ErrorCode.INDEX_BUILD_FAILED,
                    {"command": " ".join(cmd), "error": result.stderr},
                )

        self.logger.info(f"Samtools索引构建完成: {output_path}")
        return True

    def _build_star_index(
        self,
        database_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """构建STAR索引

        Args:
            database_path: 数据库路径
            output_path: 输出路径
            options: 选项

        Returns:
            成功返回True
        """
        # 检查STAR是否可用
        if not shutil.which("STAR"):
            raise IndexError(
                "STAR工具未找到",
                ErrorCode.INDEX_TOOL_NOT_FOUND,
                {"tool": "STAR"},
            )

        # 查找FASTA文件
        fasta_files = list(database_path.glob("*.fa")) + list(
            database_path.glob("*.fasta")
        ) + list(database_path.glob("*.fna"))

        if not fasta_files:
            raise IndexError(
                f"未找到FASTA文件: {database_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(database_path)},
            )

        # STAR需要一个基因组目录
        genome_dir = output_path
        genome_dir.mkdir(parents=True, exist_ok=True)

        # 合并所有FASTA文件（STAR需要一个文件）
        combined_fasta = genome_dir / "genome.fa"
        with open(combined_fasta, "wb") as outfile:
            for fasta_file in fasta_files:
                with open(fasta_file, "rb") as infile:
                    outfile.write(infile.read())

        cmd = [
            "STAR",
            "--runMode",
            "genomeGenerate",
            "--genomeDir",
            str(genome_dir),
            "--genomeFastaFiles",
            str(combined_fasta),
            "--runThreadN",
            str(options.get("threads", 1)),
        ]

        self.logger.debug(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise IndexError(
                f"STAR执行失败: {result.stderr}",
                ErrorCode.INDEX_BUILD_FAILED,
                {"command": " ".join(cmd), "error": result.stderr},
            )

        self.logger.info(f"STAR索引构建完成: {output_path}")
        return True

    def check_tool_available(self, tool_name: str) -> bool:
        """检查工具是否可用

        Args:
            tool_name: 工具名称

        Returns:
            如果工具可用返回True，否则返回False
        """
        return shutil.which(tool_name) is not None

    def list_available_tools(self) -> List[str]:
        """列出可用的索引工具

        Returns:
            可用工具列表
        """
        tool_mapping = {
            "blast": "makeblastdb",
            "bwa": "bwa",
            "bowtie2": "bowtie2-build",
            "hisat2": "hisat2-build",
            "samtools": "samtools",
            "star": "STAR",
        }

        available_tools = []
        for index_type, tool_name in tool_mapping.items():
            if self.check_tool_available(tool_name):
                available_tools.append(index_type)

        return available_tools
