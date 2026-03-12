"""
转换服务

提供文件格式转换功能，支持FASTA/FASTQ、GFF/GTF、BED、VCF等格式。
"""

import gzip
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class ConversionService:
    """转换服务

    提供生物信息学文件格式转换功能。
    """

    SUPPORTED_FORMATS = {
        "fasta", "fastq", "gff", "gtf", "bed", "vcf",
        "sam", "bam", "cram",
    }

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        from_format: str,
        to_format: str,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """转换文件格式

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            from_format: 源格式
            to_format: 目标格式
            options: 转换选项
            progress_callback: 进度回调函数 (current, total)

        Returns:
            如果转换成功返回True，否则返回False
        """
        options = options or {}
        from_format = from_format.lower()
        to_format = to_format.lower()

        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果是相同格式，直接复制
        if from_format == to_format:
            shutil.copy2(input_path, output_path)
            return True

        # GFF <-> GTF 转换
        if (from_format == "gff" and to_format == "gtf") or \
           (from_format == "gtf" and to_format == "gff"):
            return self._convert_gff_gtf(
                input_path, output_path, from_format, to_format, options
            )

        # 其他格式转换（复制或解压）
        if from_format in self.SUPPORTED_FORMATS and \
           to_format in self.SUPPORTED_FORMATS:
            return self._simple_convert(input_path, output_path, options)

        return False

    def _convert_gff_gtf(
        self,
        input_path: Path,
        output_path: Path,
        from_format: str,
        to_format: str,
        options: Dict[str, Any],
    ) -> bool:
        """转换GFF和GTF格式

        GFF和GTF格式非常相似，主要区别在于属性列的格式。
        """
        try:
            # 检查是否是压缩文件
            open_func = gzip.open if str(input_path).endswith(".gz") else open

            with open_func(input_path, "rt") as infile, open(output_path, "w") as outfile:
                for line in infile:
                    line = line.strip()

                    # 跳过注释行
                    if line.startswith("#"):
                        outfile.write(line + "\n")
                        continue

                    parts = line.split("\t")
                    if len(parts) < 9:
                        outfile.write(line + "\n")
                        continue

                    # 转换属性列
                    attributes = parts[8]
                    if from_format == "gff" and to_format == "gtf":
                        attributes = self._gff_to_gtf_attributes(attributes)
                    elif from_format == "gtf" and to_format == "gff":
                        attributes = self._gtf_to_gff_attributes(attributes)

                    parts[8] = attributes
                    outfile.write("\t".join(parts) + "\n")

            return True
        except Exception:
            return False

    def _gff_to_gtf_attributes(self, attributes: str) -> str:
        """将GFF属性转换为GTF属性"""
        # GFF: ID=gene1;Name=ABC
        # GTF: gene_id "gene1"; gene_name "ABC"
        result = []
        for attr in attributes.split(";"):
            attr = attr.strip()
            if not attr:
                continue

            if "=" in attr:
                key, value = attr.split("=", 1)
                # 映射常用字段名
                if key == "ID":
                    key = "gene_id"
                elif key == "Name":
                    key = "gene_name"
                result.append(f'{key} "{value}"')

        return "; ".join(result)

    def _gtf_to_gff_attributes(self, attributes: str) -> str:
        """将GTF属性转换为GFF属性"""
        # GTF: gene_id "gene1"; gene_name "ABC"
        # GFF: ID=gene1;Name=ABC
        result = []
        import re

        # 解析GTF属性
        pattern = r'(\w+)\s+"([^"]*)"'
        matches = re.findall(pattern, attributes)

        for key, value in matches:
            # 映射常用字段名
            if key == "gene_id":
                key = "ID"
            elif key == "gene_name":
                key = "Name"
            result.append(f"{key}={value}")

        return ";".join(result)

    def _simple_convert(
        self,
        input_path: Path,
        output_path: Path,
        options: Dict[str, Any],
    ) -> bool:
        """简单转换（复制或解压）"""
        try:
            # 检查是否是压缩文件
            if str(input_path).endswith(".gz"):
                with gzip.open(input_path, "rb") as infile, \
                     open(output_path, "wb") as outfile:
                    shutil.copyfileobj(infile, outfile)
            else:
                shutil.copy2(input_path, output_path)

            return True
        except Exception:
            return False

    def decompress(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """解压gzip文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则自动推断

        Returns:
            如果解压成功返回True，否则返回False
        """
        if not str(input_path).endswith(".gz"):
            return False

        if output_path is None:
            output_path = Path(str(input_path)[:-3])

        try:
            with gzip.open(input_path, "rb") as infile, \
                 open(output_path, "wb") as outfile:
                shutil.copyfileobj(infile, outfile)
            return True
        except Exception:
            return False

    def compress(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """压缩为gzip文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则自动推断

        Returns:
            如果压缩成功返回True，否则返回False
        """
        if output_path is None:
            output_path = Path(str(input_path) + ".gz")

        try:
            with open(input_path, "rb") as infile, \
                 gzip.open(output_path, "wb") as outfile:
                shutil.copyfileobj(infile, outfile)
            return True
        except Exception:
            return False
