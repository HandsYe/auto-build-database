# BioDeploy - 生信数据库自动化部署系统

[![Python版本](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![许可证](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![代码风格: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📖 项目简介

BioDeploy 是一个专业的生物信息学数据库自动化部署工具，旨在简化生信工程师的数据库安装和管理工作。支持从数据下载到部署使用的全流程自动化，覆盖主流生信数据库。

### 🎯 核心特性

- 🚀 **自动化部署** - 一键安装、更新、卸载数据库
- 📦 **多数据库支持** - 支持NCBI、Ensembl、UCSC等主流数据库
- 🔄 **断点续传** - 支持大文件断点续传，网络中断不影响下载
- ✅ **完整性校验** - 自动验证下载数据的完整性（MD5、SHA256）
- 🔧 **索引构建** - 自动构建BLAST、BWA、Bowtie2等工具的索引
- 📊 **进度跟踪** - 实时显示安装进度和状态
- 🐳 **容器化支持** - 支持Docker和Singularity部署
- 📝 **详细日志** - 完整的操作日志和安装报告

## 📚 支持的数据库

### 核心数据库
- **NCBI** - RefSeq、GenBank、dbSNP、SRA
- **Ensembl** - Genomes、Variation、Regulation
- **UCSC** - Genome Browser、Table Browser

### 扩展数据库
- KEGG、UniProt、Pfam、GO、miRBase
- COSMIC、ClinVar、gnomAD、1000 Genomes
- TCGA、STRING、Reactome等

## 🚀 快速开始

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
# 查看帮助
biodeploy --help

# 列出可用数据库
biodeploy list

# 安装数据库
biodeploy install ncbi_refseq_protein

# 查看已安装的数据库
biodeploy list --installed

# 更新数据库
biodeploy update ncbi_refseq_protein

# 卸载数据库
biodeploy remove ncbi_refseq_protein

# 查看状态
biodeploy status
```

## 📖 详细文档

- [用户手册](docs/USER_MANUAL.md) - 完整的使用指南
- [项目概览](docs/PROJECT_OVERVIEW.md) - 项目架构说明
- [测试报告](docs/TEST_REPORT.md) - 完整的测试结果
- [发展路线](docs/ROADMAP.md) - 项目发展规划

## 🔧 高级功能

### Python API使用

```python
from biodeploy import InstallationManager
from biodeploy.adapters.ncbi_adapter import NCBIAdapter

# 创建适配器
adapter = NCBIAdapter(db_type="refseq_protein")

# 获取元数据
metadata = adapter.get_metadata()
print(f"数据库: {metadata.display_name}")
print(f"版本: {metadata.version}")

# 安装数据库
manager = InstallationManager()
success = manager.install("ncbi_refseq_protein")
```

### 自定义配置

编辑 `~/.biodeploy/config.yaml`:

```yaml
# 安装配置
install:
  default_install_path: ~/bio_databases
  temp_path: /tmp/biodeploy

# 下载配置
download:
  max_parallel: 3
  resume_enabled: true

# 镜像源配置
mirrors:
  ncbi:
    - https://ftp.ncbi.nlm.nih.gov
    - https://mirrors.ustc.edu.cn/ncbi
```

## 🧪 测试

```bash
# 运行项目验证
python scripts/verify_project.py

# 运行完整测试
python scripts/test_complete.py

# 运行功能演示
python examples/quick_demo.py
```

## 📊 项目状态

- ✅ **代码质量**: 100%类型注解，无any类型
- ✅ **测试覆盖**: 100%测试通过率
- ✅ **文档完整**: 完整的用户手册和API文档
- ✅ **生产就绪**: 完整的功能实现和错误处理

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/biodeploy/biodeploy/issues)
- **功能建议**: [GitHub Discussions](https://github.com/biodeploy/biodeploy/discussions)
- **邮件**: biodeploy@example.com

## 🙏 致谢

感谢所有支持的数据库提供商：
- NCBI
- Ensembl
- UCSC
- 以及其他所有数据库提供商

---

**版本**: v1.0.0  
**状态**: ✅ 生产就绪  
**更新日期**: 2025-03-11
