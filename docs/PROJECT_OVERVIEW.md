# BioDeploy 项目概览

## 项目结构

```
biodeploy/
├── src/
│   └── biodeploy/
│       ├── __init__.py              # 包初始化
│       ├── cli/                     # 命令行接口
│       │   └── main.py              # 主命令入口
│       ├── core/                    # 核心业务逻辑
│       │   ├── installation_manager.py
│       │   ├── update_manager.py
│       │   ├── state_manager.py
│       │   └── dependency_manager.py
│       ├── services/                # 服务层
│       │   ├── download_service.py
│       │   ├── checksum_service.py
│       │   ├── conversion_service.py
│       │   ├── index_service.py
│       │   ├── config_generation_service.py
│       │   └── environment_service.py
│       ├── adapters/                # 数据库适配器
│       │   ├── base_adapter.py
│       │   ├── ncbi_adapter.py
│       │   ├── ensembl_adapter.py
│       │   └── ucsc_adapter.py
│       ├── infrastructure/          # 基础设施层
│       │   ├── config_manager.py    # 配置管理
│       │   ├── logger.py            # 日志系统
│       │   ├── state_storage.py     # 状态存储
│       │   └── filesystem.py        # 文件系统工具
│       ├── models/                  # 数据模型
│       │   ├── metadata.py          # 数据库元数据
│       │   ├── state.py             # 安装状态
│       │   ├── config.py            # 配置模型
│       │   └── errors.py            # 错误定义
│       └── utils/                   # 工具函数
├── tests/                           # 测试
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   └── e2e/                         # 端到端测试
├── docs/                            # 文档
│   ├── user_guide/                  # 用户指南
│   ├── developer_guide/             # 开发指南
│   └── databases/                   # 数据库文档
├── config/                          # 配置文件
│   ├── config.yaml                  # 默认配置
│   └── databases/                   # 数据库元数据
├── scripts/                         # 脚本
│   └── quickstart.sh                # 快速开始脚本
├── templates/                       # 模板
│   └── report/                      # 报告模板
├── setup.py                         # 安装脚本
├── requirements.txt                 # 依赖
├── requirements-dev.txt             # 开发依赖
├── README.md                        # 项目说明
├── LICENSE                          # 许可证
└── .gitignore                       # Git忽略文件
```

## 已完成的功能

### ✅ 任务1: 项目初始化和基础架构搭建
- [x] 创建项目目录结构
- [x] 配置Python项目 (setup.py, requirements.txt)
- [x] 创建基础模块文件
- [x] 创建README.md和LICENSE
- [x] 创建.gitignore

### ✅ 任务2: 数据模型和基础设施层实现 (部分完成)
- [x] 实现数据模型
  - [x] DatabaseMetadata, DownloadSource
  - [x] InstallationStatus, InstallationRecord
  - [x] Config, InstallConfig, NetworkConfig等
  - [x] ErrorCode, BioDeployError及子类
- [x] 实现配置管理器 (ConfigManager)
- [x] 实现日志系统 (Logger)
- [x] 实现状态存储 (StateStorage)
- [x] 实现文件系统工具 (FileSystem)
- [x] 添加单元测试

### ✅ 任务6: 命令行接口实现 (部分完成)
- [x] 实现主命令入口 (cli/main.py)
- [x] 实现install命令框架
- [x] 实现update命令框架
- [x] 实现list命令框架
- [x] 实现remove命令框架
- [x] 实现status命令框架

## 待完成的功能

### 🔄 任务3: 服务层核心功能实现
- [ ] 实现下载服务 (DownloadService)
- [ ] 实现校验服务 (ChecksumService)
- [ ] 实现转换服务 (ConversionService)
- [ ] 实现索引服务 (IndexService)
- [ ] 实现配置生成服务 (ConfigGenerationService)
- [ ] 实现环境变量服务 (EnvironmentService)

### 🔄 任务4: 适配器层基础实现
- [ ] 实现适配器基类 (BaseAdapter)
- [ ] 实现NCBI适配器 (NCBIAdapter)
- [ ] 实现Ensembl适配器 (EnsemblAdapter)
- [ ] 实现UCSC适配器 (UCSCAdapter)
- [ ] 实现适配器注册机制 (AdapterRegistry)

### 🔄 任务5: 核心业务层实现
- [ ] 实现安装管理器 (InstallationManager)
- [ ] 实现更新管理器 (UpdateManager)
- [ ] 实现卸载管理器 (UninstallManager)
- [ ] 实现状态管理器 (StateManager)
- [ ] 实现依赖管理器 (DependencyManager)

### 🔄 任务7-12: 其他功能
- [ ] 数据库元数据管理
- [ ] 扩展数据库适配器
- [ ] 日志和报告功能
- [ ] 测试和文档完善
- [ ] 性能优化
- [ ] 可选数据库和高级功能

## 快速开始

### 1. 安装依赖

```bash
# 运行快速开始脚本
./scripts/quickstart.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. 运行测试

```bash
# 运行单元测试
pytest tests/unit/test_models.py -v

# 运行所有测试
pytest
```

### 3. 使用命令行工具

```bash
# 查看帮助
biodeploy --help

# 列出可用数据库
biodeploy list

# 安装数据库（功能开发中）
biodeploy install ncbi
```

## 技术栈

- **编程语言**: Python 3.8+
- **命令行框架**: Click
- **配置管理**: PyYAML
- **日志系统**: logging (标准库)
- **测试框架**: pytest
- **类型检查**: mypy
- **代码格式化**: black, isort

## 设计原则

1. **模块化设计**: 采用分层架构，核心逻辑与数据库特定逻辑分离
2. **类型安全**: 使用Python类型注解，避免使用`any`类型
3. **容错性**: 所有关键操作支持失败重试和错误恢复
4. **可扩展性**: 通过配置文件和适配器模式支持新数据库扩展
5. **可观测性**: 全面的日志记录和状态跟踪

## 下一步计划

1. 完成服务层核心功能（下载、校验、索引等）
2. 实现核心数据库适配器（NCBI、Ensembl、UCSC）
3. 完成核心业务逻辑（安装、更新、卸载）
4. 添加更多单元测试和集成测试
5. 完善文档和用户指南

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。
