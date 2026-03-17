# BioDeploy 快速使用指南

## 安装所有常用数据库

### 一键安装所有数据库
```bash
biodeploy install ncbi_refseq_protein ensembl_genomes ucsc_genome_hg38 eggnog_eggnog kegg_full cazy card_rgi vfdb go cog swissprot
```

### 按类别安装

#### 1. 核心数据库（必需）
```bash
biodeploy install ncbi_refseq_protein ensembl_genomes ucsc_genome_hg38
```

#### 2. 功能注释数据库（推荐）
```bash
biodeploy install eggnog_eggnog kegg_full go swissprot cog
```

#### 3.  Specialty 数据库（根据研究方向选择）
```bash
# 宏基因组/耐药性研究
biodeploy install card_rgi vfdb cazy

# 真菌研究
biodeploy install eggnog_fungi cazy

# 细菌研究
biodeploy install eggnog_bacteria card_rgi vfdb
```

## 常用命令

### 查看可用数据库
```bash
# 列出所有可用数据库
biodeploy list

# 以 JSON 格式输出
biodeploy list --format json
```

### 查看已安装数据库
```bash
# 查看已安装的数据库
biodeploy list --installed

# 查看数据库详细状态
biodeploy status eggnog_eggnog

# 查看所有数据库状态
biodeploy status
```

### 安装数据库
```bash
# 安装单个数据库
biodeploy install eggnog_eggnog

# 指定版本安装
biodeploy install kegg_full --version latest

# 指定安装路径
biodeploy install card_rgi --path /data/databases

# 强制重新安装
biodeploy install go --force

# 跳过依赖检查
biodeploy install vfdb --skip-deps
```

### 更新数据库
```bash
# 检查所有数据库更新
biodeploy update --check-only

# 更新所有数据库
biodeploy update

# 更新指定数据库
biodeploy update eggnog_eggnog kegg_full

# 保留旧版本更新
biodeploy update card_rgi --keep-old
```

### 卸载数据库
```bash
# 卸载单个数据库
biodeploy remove eggnog_eggnog

# 批量卸载
biodeploy remove cazy vfdb

# 强制卸载（不确认）
biodeploy remove go --force

# 保留配置文件
biodeploy remove card_rgi --keep-config
```

## 推荐安装组合

### 宏基因组分析全套
```bash
biodeploy install ncbi_refseq_protein eggnog_eggnog kegg_full card_rgi vfdb cazy go
```
**总大小**: ~20GB

### 转录组分析全套
```bash
biodeploy install ncbi_refseq_protein ensembl_genomes eggnog_eggnog kegg_pathway go swissprot
```
**总大小**: ~25GB

### 耐药性研究全套
```bash
biodeploy install card_rgi eggnog_bacteria vfdb ncbi_refseq_protein
```
**总大小**: ~8GB

### 真菌研究全套
```bash
biodeploy install eggnog_fungi cazy go kegg_full ucsc_genome_hg38
```
**总大小**: ~15GB

### 最小安装（仅必需）
```bash
biodeploy install ncbi_refseq_protein eggnog_eggnog go
```
**总大小**: ~8GB

## 环境变量配置

安装完成后，数据库会自动生成环境变量配置脚本：

```bash
# 加载环境变量
source ~/bio_databases/eggnog_eggnog/5.0.2/env.sh

# 或添加到 ~/.bashrc
echo 'source ~/bio_databases/eggnog_eggnog/5.0.2/env.sh' >> ~/.bashrc
```

## 验证安装

```bash
# 检查数据库完整性
biodeploy status eggnog_eggnog --detail

# 检查所有已安装数据库
biodeploy list --installed
```

## 故障排除

### 下载失败
```bash
# 使用代理
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080
biodeploy install kegg_full

# 使用指定镜像
biodeploy install ncbi_refseq_protein --mirror https://mirrors.ustc.edu.cn/ncbi
```

### 磁盘空间不足
```bash
# 清理临时文件
rm -rf /tmp/biodeploy/*

# 卸载不常用的数据库
biodeploy remove cog
```

### 依赖缺失
```bash
# 安装系统依赖（Ubuntu/Debian）
sudo apt-get install wget tar gzip

# 安装生物信息学工具
sudo apt-get install ncbi-blast+ samtools
```

## 性能优化

### 并行下载
```bash
# 并发安装多个数据库
biodeploy install eggnog_eggnog kegg_full card_rgi --parallel 3
```

### 使用更快的镜像
编辑配置文件 `~/.biodeploy/config.yaml`：

```yaml
mirrors:
  ncbi:
    - https://mirrors.ustc.edu.cn/ncbi
    - https://mirrors.tuna.tsinghua.edu.cn/ncbi
  kegg:
    - https://www.kegg.jp/kegg/
```

## 日志和调试

```bash
# 显示详细日志
biodeploy install eggnog_eggnog -vvv

# 静默模式（仅错误）
biodeploy install kegg_full --quiet

# 查看日志文件
tail -f ~/.biodeploy/logs/biodeploy.log
```

## 配置文件位置

- 全局配置：`~/.biodeploy/config.yaml`
- 状态文件：`~/.biodeploy/state.json`
- 日志文件：`~/.biodeploy/logs/biodeploy.log`
- 默认安装路径：`~/bio_databases/`

## 帮助信息

```bash
# 查看帮助
biodeploy --help

# 查看命令帮助
biodeploy install --help
biodeploy list --help
biodeploy update --help
```

## 版本信息

```bash
biodeploy --version
```
