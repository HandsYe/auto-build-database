# BioDeploy 使用手册

## 📖 目录

1. [快速开始](#快速开始)
2. [安装配置](#安装配置)
3. [基本使用](#基本使用)
4. [高级功能](#高级功能)
5. [常见问题](#常见问题)
6. [最佳实践](#最佳实践)

## 🚀 快速开始

### 系统要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+), macOS 10.14+
- **Python**: 3.8 或更高版本
- **磁盘空间**: 至少 10GB 可用空间
- **网络**: 稳定的互联网连接

### 一键安装

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/biodeploy.git
cd biodeploy

# 运行快速开始脚本
./scripts/quickstart.sh
```

### 手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装BioDeploy
pip install -e .

# 4. 验证安装
biodeploy --version
```

## ⚙️ 安装配置

### 配置文件位置

BioDeploy使用三层配置系统：

1. **全局配置**: `~/.biodeploy/config.yaml`
2. **项目配置**: `./biodeploy.yaml`
3. **命令行参数**: 临时覆盖

### 基本配置

编辑 `~/.biodeploy/config.yaml`:

```yaml
# 安装配置
install:
  default_install_path: ~/bio_databases  # 默认安装路径
  temp_path: /tmp/biodeploy              # 临时文件路径
  auto_cleanup: true                      # 自动清理临时文件

# 下载配置
download:
  max_parallel: 3        # 最大并发下载数
  resume_enabled: true   # 启用断点续传
  verify_checksum: true  # 验证文件校验和

# 日志配置
log:
  level: INFO                    # 日志级别
  log_path: ~/.biodeploy/logs    # 日志文件路径
```

### 代理配置

如果需要使用代理：

```yaml
network:
  proxy: http://proxy.example.com:8080
  timeout: 300
  max_retries: 3
```

### 镜像源配置

配置国内镜像源加速下载：

```yaml
mirrors:
  ncbi:
    - https://ftp.ncbi.nlm.nih.gov
    - https://mirrors.ustc.edu.cn/ncbi
    - https://mirrors.tuna.tsinghua.edu.cn/ncbi
  ensembl:
    - https://ftp.ensembl.org
    - https://mirrors.ustc.edu.cn/ensembl
```

## 📚 基本使用

### 查看帮助

```bash
# 查看主命令帮助
biodeploy --help

# 查看子命令帮助
biodeploy install --help
biodeploy update --help
```

### 列出数据库

```bash
# 列出所有可用数据库
biodeploy list

# 仅列出已安装的数据库
biodeploy list --installed

# 以JSON格式输出
biodeploy list --format json

# 按标签过滤
biodeploy list --filter protein
```

### 安装数据库

#### 安装单个数据库

```bash
# 安装最新版本
biodeploy install ncbi_refseq_protein

# 安装指定版本
biodeploy install ncbi_refseq_protein --version 2024.01

# 指定安装路径
biodeploy install ncbi_refseq_protein --path /data/databases

# 强制重新安装
biodeploy install ncbi_refseq_protein --force
```

#### 批量安装

```bash
# 安装多个数据库
biodeploy install ncbi_refseq_protein ensembl ucsc

# 并发安装（3个并发）
biodeploy install ncbi ensembl ucsc --parallel 3

# 从配置文件安装
biodeploy install --config databases.yaml
```

#### 安装选项

```bash
# 跳过依赖检查
biodeploy install ncbi --skip-deps

# 不构建索引
biodeploy install ncbi --no-index

# 不设置环境变量
biodeploy install ncbi --no-env

# 详细输出
biodeploy install ncbi -vvv
```

### 查看状态

```bash
# 查看所有数据库状态
biodeploy status

# 查看特定数据库状态
biodeploy status ncbi_refseq_protein

# 显示详细信息
biodeploy status ncbi --detail

# JSON格式输出
biodeploy status ncbi --json
```

### 更新数据库

```bash
# 检查更新
biodeploy update --check-only

# 更新特定数据库
biodeploy update ncbi_refseq_protein

# 更新所有数据库
biodeploy update

# 保留旧版本
biodeploy update ncbi --keep-old

# 并发更新
biodeploy update --parallel 2
```

### 卸载数据库

```bash
# 卸载数据库（会提示确认）
biodeploy remove ncbi_refseq_protein

# 强制卸载（不提示）
biodeploy remove ncbi --force

# 卸载特定版本
biodeploy remove ncbi --version 2024.01

# 保留配置文件
biodeploy remove ncbi --keep-config
```

## 🔧 高级功能

### Python API使用

```python
from biodeploy import InstallationManager
from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.models import DatabaseMetadata

# 创建适配器
adapter = NCBIAdapter(db_type="refseq_protein")

# 获取元数据
metadata = adapter.get_metadata()
print(f"数据库: {metadata.display_name}")
print(f"版本: {metadata.version}")
print(f"大小: {metadata.size / (1024**3):.2f} GB")

# 安装数据库
manager = InstallationManager()

# 定义进度回调
def progress_callback(message: str, progress: float):
    print(f"[{progress*100:.0f}%] {message}")

# 执行安装
success = manager.install(
    database="ncbi_refseq_protein",
    version="2024.01",
    install_path="/data/databases/ncbi",
    progress_callback=progress_callback
)

if success:
    print("安装成功！")
```

### 自定义安装流程

```python
from biodeploy.services import DownloadService, ChecksumService, IndexService
from biodeploy.models import DownloadSource

# 创建下载源
sources = [
    DownloadSource(
        url="https://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.protein.faa.gz",
        protocol="https",
        priority=1,
        is_mirror=False,
    ),
    DownloadSource(
        url="https://mirrors.ustc.edu.cn/ncbi/refseq/release/complete/complete.protein.faa.gz",
        protocol="https",
        priority=2,
        is_mirror=True,
    ),
]

# 下载文件
download_service = DownloadService()
result = download_service.download(
    sources=sources,
    target_path=Path("/tmp/ncbi.fa.gz"),
    options={"resume_enabled": True}
)

if result.success:
    print(f"下载成功: {result.file_path}")
    print(f"大小: {result.downloaded_size / (1024**2):.2f} MB")
    print(f"耗时: {result.elapsed_time:.2f} 秒")

# 验证校验和
checksum_service = ChecksumService()
checksum = checksum_service.calculate(result.file_path, "sha256")
print(f"SHA256: {checksum}")

# 构建索引
index_service = IndexService()
if index_service.check_tool_available("blast"):
    success = index_service.build_index(
        database_path=result.file_path.parent,
        index_type="blast",
        output_path=Path("/data/ncbi/blast_index"),
    )
    if success:
        print("BLAST索引构建成功")
```

### 批量管理

```python
from biodeploy import InstallationManager

manager = InstallationManager()

# 批量安装
databases = [
    "ncbi_refseq_protein",
    "ensembl_homo_sapiens",
    "ucsc_hg38",
]

results = manager.install_multiple(
    databases=databases,
    options={
        "parallel": True,
        "max_parallel": 3,
        "build_indexes": True,
    }
)

# 查看结果
for db, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {db}")
```

### 环境变量管理

```python
from biodeploy.services import EnvironmentService
from biodeploy.models import InstallationRecord

env_service = EnvironmentService()

# 生成环境变量脚本
record = InstallationRecord(
    name="ncbi",
    version="2024.01",
    install_path=Path("/data/ncbi"),
)

script_path = env_service.generate_export_script(record)
print(f"环境变量脚本: {script_path}")

# 使用脚本
# source ~/.biodeploy/env/ncbi_2024.01.sh
```

## ❓ 常见问题

### 1. 下载速度慢怎么办？

**解决方案**:
- 配置国内镜像源
- 使用代理
- 启用并发下载

```yaml
# config.yaml
mirrors:
  ncbi:
    - https://mirrors.ustc.edu.cn/ncbi

download:
  max_parallel: 5
```

### 2. 磁盘空间不足？

**解决方案**:
- 清理临时文件: `rm -rf /tmp/biodeploy/*`
- 卸载不用的数据库: `biodeploy remove <database>`
- 使用符号链接到其他磁盘

### 3. 依赖工具缺失？

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install wget gzip bwa blast+

# CentOS/RHEL
sudo yum install wget gzip bwa blast

# macOS
brew install wget gzip bwa blast
```

### 4. 权限错误？

**解决方案**:
```bash
# 检查权限
ls -la ~/.biodeploy/

# 修复权限
chmod -R 755 ~/.biodeploy/
chown -R $USER:$USER ~/.biodeploy/
```

### 5. 安装中断如何恢复？

**解决方案**:
BioDeploy支持断点续传，直接重新运行安装命令即可：
```bash
biodeploy install ncbi
```

## 💡 最佳实践

### 1. 目录结构建议

```
/data/
├── bio_databases/          # 数据库主目录
│   ├── ncbi/
│   ├── ensembl/
│   └── ucsc/
├── bio_indexes/            # 索引目录
│   ├── blast/
│   ├── bwa/
│   └── bowtie2/
└── bio_temp/               # 临时文件目录
```

### 2. 定期维护

```bash
# 每周检查更新
biodeploy update --check-only

# 每月清理日志
find ~/.biodeploy/logs -name "*.log" -mtime +30 -delete

# 定期备份配置
cp ~/.biodeploy/config.yaml ~/.biodeploy/config.yaml.bak
```

### 3. 版本管理

```bash
# 安装特定版本
biodeploy install ncbi --version 2024.01

# 保留多个版本
biodeploy update ncbi --keep-old

# 切换版本
biodeploy switch ncbi --version 2024.01
```

### 4. 性能优化

```yaml
# 针对高性能服务器
download:
  max_parallel: 10

install:
  temp_path: /dev/shm/biodeploy  # 使用内存盘

index:
  threads: 16  # 多线程构建索引
```

### 5. 安全建议

- 定期更新BioDeploy: `pip install --upgrade biodeploy`
- 验证下载文件的校验和
- 不要在公共网络下载数据库
- 定期检查已安装数据库的完整性

## 📞 获取帮助

- **文档**: https://biodeploy.readthedocs.io
- **问题反馈**: https://github.com/biodeploy/biodeploy/issues
- **邮件**: biodeploy@example.com
- **社区**: https://github.com/biodeploy/biodeploy/discussions

---

**版本**: v1.0.0  
**更新日期**: 2025-03-11
