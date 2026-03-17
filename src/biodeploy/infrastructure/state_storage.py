"""
状态存储

负责保存和加载数据库安装状态。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from biodeploy.models.errors import ErrorCode, StateError
from biodeploy.models.state import InstallationRecord, InstallationStatus
from biodeploy.infrastructure.logger import get_logger


class StateStorage:
    """状态存储

    负责管理数据库安装状态的持久化存储。

    Attributes:
        DEFAULT_STATE_FILE: 默认状态文件路径
    """

    DEFAULT_STATE_FILE = Path.home() / ".biodeploy" / "state.json"

    def __init__(self, state_file: Optional[Path] = None) -> None:
        """初始化状态存储

        Args:
            state_file: 状态文件路径，如果为None则使用默认路径
        """
        self.state_file = state_file or self.DEFAULT_STATE_FILE
        self.logger = get_logger("state_storage")

    def save(self, record: InstallationRecord) -> None:
        """保存单个安装记录

        Args:
            record: 安装记录

        Raises:
            StateError: 保存状态失败
        """
        try:
            # 加载现有记录
            records = self.load()

            # 查找并更新或添加记录
            found = False
            for i, existing in enumerate(records):
                if existing.name == record.name and existing.version == record.version:
                    records[i] = record
                    found = True
                    break

            if not found:
                records.append(record)

            # 确保目录存在
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典列表
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "databases": [r.to_dict() for r in records],
            }

            # 保存到文件
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"状态已保存到 {self.state_file}")

        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            raise StateError(
                f"保存状态失败: {e}",
                ErrorCode.STATE_SAVE_ERROR,
                {"path": str(self.state_file), "error": str(e)},
            )

    def save_all(self, records: List[InstallationRecord]) -> None:
        """保存所有状态

        Args:
            records: 安装记录列表

        Raises:
            StateError: 保存状态失败
        """
        try:
            # 确保目录存在
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典列表
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "databases": [record.to_dict() for record in records],
            }

            # 保存到文件
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"状态已保存到 {self.state_file}")

        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            raise StateError(
                f"保存状态失败: {e}",
                ErrorCode.STATE_SAVE_ERROR,
                {"path": str(self.state_file), "error": str(e)},
            )

    def load(
        self, name: Optional[str] = None, version: Optional[str] = None
    ) -> List[InstallationRecord]:
        """加载状态

        Args:
            name: 数据库名称，如果指定则只返回该数据库的记录
            version: 数据库版本，如果指定则只返回该版本的记录

        Returns:
            安装记录列表

        Raises:
            StateError: 加载状态失败
        """
        if not self.state_file.exists():
            self.logger.info("状态文件不存在，返回空列表")
            return []

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 验证数据格式
            if not isinstance(data, dict) or "databases" not in data:
                raise StateError(
                    "状态文件格式错误",
                    ErrorCode.STATE_CORRUPTED,
                    {"path": str(self.state_file)},
                )

            # 转换为安装记录列表
            records = []
            for db_data in data["databases"]:
                try:
                    record = InstallationRecord.from_dict(db_data)
                    # 过滤
                    if name and record.name != name:
                        continue
                    if version and record.version != version:
                        continue
                    records.append(record)
                except Exception as e:
                    self.logger.warning(f"跳过无效的安装记录: {e}")
                    continue

            self.logger.info(f"已加载 {len(records)} 个数据库状态")
            return records

        except json.JSONDecodeError as e:
            self.logger.error(f"状态文件格式错误: {e}")
            raise StateError(
                f"状态文件格式错误: {e}",
                ErrorCode.STATE_CORRUPTED,
                {"path": str(self.state_file), "error": str(e)},
            )
        except StateError:
            raise
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            raise StateError(
                f"加载状态失败: {e}",
                ErrorCode.STATE_LOAD_ERROR,
                {"path": str(self.state_file), "error": str(e)},
            )

    def load_by_name(self, name: str) -> List[InstallationRecord]:
        """按名称加载数据库的所有版本

        Args:
            name: 数据库名称

        Returns:
            该数据库的所有版本记录列表
        """
        return self.load(name=name)

    def update_status(
        self,
        name: str,
        version: str,
        status: InstallationStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """更新数据库状态

        Args:
            name: 数据库名称
            version: 数据库版本
            status: 新状态
            progress: 进度 (0.0 - 1.0)
            error_message: 错误信息

        Returns:
            如果更新成功返回True，否则返回False
        """
        try:
            records = self.load()

            for record in records:
                if record.name == name and record.version == version:
                    record.status = status
                    if progress is not None:
                        record.progress = progress
                    if error_message:
                        record.error_message = error_message
                    record.last_updated = datetime.now()
                    self.save_all(records)
                    return True

            return False
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
            return False

    def remove(self, name: str, version: Optional[str] = None) -> bool:
        """移除数据库状态

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则移除所有版本

        Returns:
            如果成功移除返回True，否则返回False
        """
        try:
            records = self.load()
            original_count = len(records)

            # 过滤掉要移除的记录
            if version:
                records = [
                    r for r in records if not (r.name == name and r.version == version)
                ]
            else:
                records = [r for r in records if r.name != name]

            if len(records) < original_count:
                self.save_all(records)
                return True

            return False
        except Exception as e:
            self.logger.error(f"移除状态失败: {e}")
            return False

    def update(self, record: InstallationRecord) -> None:
        """更新单个数据库状态

        Args:
            record: 安装记录
        """
        # 加载现有状态
        records = self.load()

        # 查找并更新记录
        found = False
        for i, existing_record in enumerate(records):
            if existing_record.name == record.name:
                records[i] = record
                found = True
                break

        # 如果没找到，添加新记录
        if not found:
            records.append(record)

        # 保存状态
        self.save_all(records)

    def get(self, name: str) -> Optional[InstallationRecord]:
        """获取单个数据库状态

        Args:
            name: 数据库名称

        Returns:
            安装记录，如果不存在则返回None
        """
        records = self.load()
        for record in records:
            if record.name == name:
                return record
        return None

    def exists(self, name: str) -> bool:
        """检查数据库是否存在

        Args:
            name: 数据库名称

        Returns:
            如果存在返回True，否则返回False
        """
        return self.get(name) is not None
