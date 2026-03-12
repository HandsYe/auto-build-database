"""
BioDeploy - 生信数据库自动化部署系统

这是一个用于生物信息学数据库自动化部署的工具，支持从数据下载到部署使用的全流程自动化。
"""

__version__ = "1.0.0"
__author__ = "BioDeploy Team"
__email__ = "biodeploy@example.com"

from biodeploy.core.installation_manager import InstallationManager
from biodeploy.core.update_manager import UpdateManager
from biodeploy.core.uninstall_manager import UninstallManager
from biodeploy.core.state_manager import StateManager
from biodeploy.core.dependency_manager import DependencyManager

__all__ = [
    "InstallationManager",
    "UpdateManager",
    "UninstallManager",
    "StateManager",
    "DependencyManager",
]
