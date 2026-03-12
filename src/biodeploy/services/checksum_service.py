"""
校验和服务

提供文件校验和计算和验证功能。
"""

import hashlib
from pathlib import Path
from typing import Dict

from biodeploy.models.errors import DownloadError, ErrorCode
from biodeploy.infrastructure.logger import get_logger


class ChecksumService:
    """校验和服务

    提供文件校验和的计算和验证功能，支持多种哈希算法。

    Attributes:
        chunk_size: 读取文件的块大小
        supported_algorithms: 支持的哈希算法列表
    """

    SUPPORTED_ALGORITHMS = ["md5", "sha1", "sha256", "sha512"]

    def __init__(self, chunk_size: int = 8192) -> None:
        """初始化校验和服务

        Args:
            chunk_size: 读取文件的块大小（字节）
        """
        self.chunk_size = chunk_size
        self.logger = get_logger("checksum_service")

    def calculate(self, file_path: Path, algorithm: str = "sha256") -> str:
        """计算文件校验和

        Args:
            file_path: 文件路径
            algorithm: 哈希算法 (md5, sha1, sha256, sha512)

        Returns:
            校验和字符串（十六进制）

        Raises:
            DownloadError: 文件不存在或算法不支持
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise DownloadError(
                f"文件不存在: {file_path}",
                ErrorCode.FILE_NOT_FOUND,
                {"path": str(file_path)},
            )

        algorithm = algorithm.lower()
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise DownloadError(
                f"不支持的哈希算法: {algorithm}",
                ErrorCode.INVALID_ARGUMENT,
                {"algorithm": algorithm, "supported": self.SUPPORTED_ALGORITHMS},
            )

        self.logger.debug(f"计算文件校验和: {file_path}, 算法: {algorithm}")

        # 创建哈希对象
        hash_obj = hashlib.new(algorithm)

        # 分块读取文件并更新哈希
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)

        checksum = hash_obj.hexdigest()
        self.logger.debug(f"校验和: {checksum}")

        return checksum

    def verify(
        self, file_path: Path, algorithm: str, expected_checksum: str
    ) -> bool:
        """验证文件校验和

        Args:
            file_path: 文件路径
            algorithm: 哈希算法
            expected_checksum: 期望的校验和

        Returns:
            如果校验和匹配返回True，否则返回False
        """
        try:
            actual_checksum = self.calculate(file_path, algorithm)

            if actual_checksum.lower() == expected_checksum.lower():
                self.logger.info(f"校验和验证通过: {file_path}")
                return True
            else:
                self.logger.warning(
                    f"校验和不匹配: {file_path}\n"
                    f"期望: {expected_checksum}\n"
                    f"实际: {actual_checksum}"
                )
                return False

        except Exception as e:
            self.logger.error(f"校验和验证失败: {e}")
            return False

    def verify_multiple(
        self, file_path: Path, checksums: Dict[str, str]
    ) -> bool:
        """验证多个校验和

        Args:
            file_path: 文件路径
            checksums: 校验和字典 {algorithm: checksum}

        Returns:
            如果所有校验和都匹配返回True，否则返回False
        """
        all_passed = True

        for algorithm, expected_checksum in checksums.items():
            if not self.verify(file_path, algorithm, expected_checksum):
                all_passed = False

        return all_passed

    def calculate_file_md5(self, file_path: Path) -> str:
        """计算文件MD5校验和

        Args:
            file_path: 文件路径

        Returns:
            MD5校验和
        """
        return self.calculate(file_path, "md5")

    def calculate_file_sha256(self, file_path: Path) -> str:
        """计算文件SHA256校验和

        Args:
            file_path: 文件路径

        Returns:
            SHA256校验和
        """
        return self.calculate(file_path, "sha256")
