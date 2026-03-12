"""
状态存储

负责保存和加载数据库安装状态。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from biodeploy.models.errors import ErrorCode, StateError
from biodeploy.models.state import InstallationRecord
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

    def save(self, records: List[InstallationRecord]) -> None:
        """保存状态

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

    def load(self) -> List[InstallationRecord]:
        """加载状态

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
        self.save(records)

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

    def remove(self, name: str) -> bool:
        """移除数据库状态

        Args:
            name: 数据库名称

        Returns:
            如果成功移除返回True，否则返回False
        """
        records = self.load()
        original_count = len(records)

        # 过滤掉要移除的记录
        records = [r for r in records if r.name != name]

        if len(records) < original_count:
            self.save(records)
            return True

        return False

    def exists(self, name: str) -> bool:
        """检查数据库是否存在

        Args:
            name: 数据库名称

        Returns:
            如果存在返回True，否则返回False
        """
        return self.get(name) is not None
