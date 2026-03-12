# BioDeploy - 生信数据库自动化部署系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 项目简介

BioDeploy 是一个用于生物信息学数据库自动化部署的工具，旨在简化生信工程师的数据库安装和管理工作。支持从数据下载到部署使用的全流程自动化，覆盖主流生信数据库。

## 主要特性

- 🚀 **自动化部署**: 一键安装、更新、卸载数据库
- 📦 **多数据库支持**: 支持120+个生信数据库
- 🔄 **断点续传**: 支持大文件断点续传，网络中断不影响下载
- ✅ **完整性校验**: 自动验证下载数据的完整性
- 🔧 **索引构建**: 自动构建BLAST、BWA、Bowtie2等工具的索引
- 📊 **进度跟踪**: 实时显示安装进度和状态
- 🐳 **容器化支持**: 支持Docker和Singularity部署
- 📝 **详细日志**: 完整的操作日志和安装报告

## 支持的数据库

### 核心数据库
- NCBI (RefSeq, GenBank, dbSNP, SRA)
- Ensembl (Genomes, Variation, Regulation)
- UCSC (Genome Browser, Table Browser)

### 扩展数据库
- KEGG
- UniProt
- Pfam
- GO
- miRBase
- COSMIC
- ClinVar
- gnomAD
- 1000 Genomes
- TCGA

### 可选数据库
支持100+个可选数据库，详见文档。

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/biodeploy/biodeploy.git
cd biodeploy
pip install -e .

# 或使用pip安装（发布后可用）
pip install biodeploy
```

### 基本使用

```bash
# 安装数据库
biodeploy install ncbi

# 安装多个数据库
biodeploy install ncbi ensembl ucsc

# 查看已安装的数据库
biodeploy list --installed

# 更新数据库
biodeploy update ncbi

# 卸载数据库
biodeploy remove ncbi
```

## 文档

- [安装指南](docs/user_guide/installation.md)
- [快速开始](docs/user_guide/quickstart.md)
- [使用手册](docs/user_guide/user_manual.md)
- [API文档](docs/developer_guide/api_reference.md)
- [适配器开发指南](docs/developer_guide/adapter_development.md)

## 开发

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/biodeploy/biodeploy.git
cd biodeploy

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black src tests
isort src tests

# 类型检查
mypy src
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_models.py

# 生成覆盖率报告
pytest --cov=biodeploy --cov-report=html
```

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 致谢

感谢所有支持的数据库提供商：
- NCBI
- Ensembl
- UCSC
- 以及其他所有数据库提供商

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/biodeploy/biodeploy/issues)
- 邮件: biodeploy@example.com
