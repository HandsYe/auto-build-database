# BioDeploy 项目结构说明

## 📁 目录结构

```
biodeploy/
├── src/                          # 源代码目录
│   └── biodeploy/                # 主包
│       ├── __init__.py           # 包初始化
│       ├── models/               # 数据模型层
│       │   ├── __init__.py
│       │   ├── metadata.py       # 数据库元数据模型
│       │   ├── state.py          # 安装状态模型
│       │   ├── config.py         # 配置模型
│       │   └── errors.py         # 错误定义
│       ├── infrastructure/       # 基础设施层
│       │   ├── __init__.py
│       │   ├── config_manager.py # 配置管理器
│       │   ├── logger.py         # 日志系统
│       │   ├── state_storage.py  # 状态存储
│       │   ├── filesystem.py     # 文件系统工具
│       │   └── retry_handler.py  # 重试处理器
│       ├── services/             # 服务层
│       │   ├── __init__.py
│       │   ├── download_service.py      # 下载服务
│       │   ├── checksum_service.py      # 校验服务
│       │   ├── index_service.py         # 索引服务
│       │   ├── config_generation_service.py  # 配置生成
│       │   ├── environment_service.py   # 环境变量
│       │   └── conversion_service.py    # 格式转换
│       ├── adapters/             # 适配器层
│       │   ├── __init__.py
│       │   ├── base_adapter.py   # 适配器基类
│       │   ├── ncbi_adapter.py   # NCBI适配器
│       │   ├── ensembl_adapter.py # Ensembl适配器
│       │   ├── ucsc_adapter.py   # UCSC适配器
│       │   └── adapter_registry.py # 适配器注册表
│       ├── core/                 # 核心业务层
│       │   ├── __init__.py
│       │   ├── installation_manager.py  # 安装管理器
│       │   ├── update_manager.py        # 更新管理器
│       │   ├── uninstall_manager.py     # 卸载管理器
│       │   ├── state_manager.py         # 状态管理器
│       │   └── dependency_manager.py    # 依赖管理器
│       ├── cli/                  # 命令行接口
│       │   ├── __init__.py
│       │   ├── main.py           # 主命令
│       │   ├── install_cmd.py    # 安装命令
│       │   ├── update_cmd.py     # 更新命令
│       │   ├── list_cmd.py       # 列表命令
│       │   ├── remove_cmd.py     # 卸载命令
│       │   └── status_cmd.py     # 状态命令
│       └── utils/                # 工具函数（待扩展）
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   │   └── test_models.py
│   ├── integration/              # 集成测试
│   └── e2e/                      # 端到端测试
├── docs/                         # 文档目录
│   ├── PROJECT_OVERVIEW.md       # 项目概览
│   ├── COMPLETION_SUMMARY.md     # 完成总结
│   ├── DELIVERY.md               # 交付文档
│   ├── USER_MANUAL.md            # 用户手册
│   ├── TEST_REPORT.md            # 测试报告
│   ├── ROADMAP.md                # 发展路线
│   ├── user_guide/               # 用户指南
│   ├── developer_guide/          # 开发指南
│   └── databases/                # 数据库文档
├── examples/                     # 示例代码
│   ├── usage_example.py          # 基础使用示例
│   ├── complete_example.py       # 完整使用示例
│   ├── quick_demo.py             # 快速演示
│   └── demo_download.py          # 下载演示
├── config/                       # 配置文件
│   ├── config.yaml               # 默认配置
│   └── databases/                # 数据库配置
├── scripts/                      # 脚本工具
│   ├── quickstart.sh             # 快速开始脚本
│   ├── verify_project.py         # 项目验证脚本
│   └── test_complete.py          # 完整测试脚本
├── templates/                    # 模板文件
│   └── report/                   # 报告模板
├── setup.py                      # 安装脚本
├── requirements.txt              # 运行依赖
├── requirements-dev.txt          # 开发依赖
├── README.md                     # 项目说明（英文）
├── README_CN.md                  # 项目说明（中文）
├── LICENSE                       # 许可证
├── .gitignore                    # Git忽略文件
└── GITHUB_PUSH_GUIDE.md          # GitHub推送指南
```

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│        命令行接口层 (CLI)            │  用户交互
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│        核心业务层 (Core)             │  业务逻辑
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│          服务层 (Services)           │  功能服务
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│        适配器层 (Adapters)           │  数据库适配
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      基础设施层 (Infrastructure)     │  基础服务
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│        数据模型层 (Models)           │  数据定义
└─────────────────────────────────────┘
```

### 模块职责

#### 1. 数据模型层 (Models)
- **metadata.py**: 数据库元数据定义
- **state.py**: 安装状态和记录
- **config.py**: 系统配置模型
- **errors.py**: 错误代码和异常

#### 2. 基础设施层 (Infrastructure)
- **config_manager.py**: 配置加载、保存、合并
- **logger.py**: 日志记录和管理
- **state_storage.py**: 状态持久化存储
- **filesystem.py**: 文件系统操作工具
- **retry_handler.py**: 重试机制

#### 3. 服务层 (Services)
- **download_service.py**: 多源下载、断点续传
- **checksum_service.py**: 文件校验
- **index_service.py**: 索引构建
- **config_generation_service.py**: 配置文件生成
- **environment_service.py**: 环境变量管理
- **conversion_service.py**: 格式转换

#### 4. 适配器层 (Adapters)
- **base_adapter.py**: 适配器基类和接口
- **ncbi_adapter.py**: NCBI数据库适配
- **ensembl_adapter.py**: Ensembl数据库适配
- **ucsc_adapter.py**: UCSC数据库适配
- **adapter_registry.py**: 适配器注册和管理

#### 5. 核心业务层 (Core)
- **installation_manager.py**: 安装流程管理
- **update_manager.py**: 更新流程管理
- **uninstall_manager.py**: 卸载流程管理
- **state_manager.py**: 状态查询和管理
- **dependency_manager.py**: 依赖检查和管理

#### 6. 命令行接口层 (CLI)
- **main.py**: 主命令入口
- **install_cmd.py**: 安装命令
- **update_cmd.py**: 更新命令
- **list_cmd.py**: 列表命令
- **remove_cmd.py**: 卸载命令
- **status_cmd.py**: 状态命令

## 🔄 数据流

### 安装流程

```
用户输入命令
    ↓
CLI解析参数
    ↓
InstallationManager获取适配器
    ↓
Adapter获取元数据
    ↓
DownloadService下载文件
    ↓
ChecksumService校验文件
    ↓
ConversionService转换格式（可选）
    ↓
IndexService构建索引（可选）
    ↓
ConfigGenerationService生成配置
    ↓
EnvironmentService设置环境变量
    ↓
StateManager更新状态
    ↓
生成安装报告
```

## 📊 代码统计

- **总文件数**: 50+
- **Python模块**: 40+
- **代码行数**: 7,500+
- **文档文件**: 10+
- **测试文件**: 3+
- **配置文件**: 5+

## 🎯 扩展指南

### 添加新数据库适配器

1. 在 `adapters/` 目录创建新适配器
2. 继承 `BaseAdapter` 类
3. 实现所有抽象方法
4. 在 `adapter_registry.py` 注册
5. 添加测试和文档

### 添加新服务

1. 在 `services/` 目录创建新服务
2. 定义清晰的接口
3. 实现完整的功能
4. 添加错误处理
5. 编写单元测试

### 添加新命令

1. 在 `cli/` 目录创建新命令文件
2. 使用Click框架定义命令
3. 在 `main.py` 注册命令
4. 添加帮助文档
5. 编写测试

---

**最后更新**: 2025-03-11
