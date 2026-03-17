# BioDeploy 支持的数据库

## 已实现的数据库适配器

以下是 BioDeploy 工具支持的所有数据库（包含多种“变体名称”，例如 `ncbi_genbank`、`kegg_pathway` 等），可以直接使用 `biodeploy install <name>` 命令进行安装。

你可以用下面的命令获取**与当前代码版本严格一致**的“可下载数据库清单”：

```bash
# 以 JSON 导出全部可下载数据库（推荐，便于脚本化）
biodeploy list --available --format json -o biodeploy-catalog.json

# 以表格在终端查看
biodeploy list --available
```

### 核心数据库

#### 1. NCBI 数据库
- **适配器名称**: `ncbi_refseq_protein`, `ncbi_refseq_genomic`, `ncbi_genbank`
- **描述**: NCBI Reference Sequence 和 GenBank 数据库
- **大小**: ~5GB
- **用途**: 蛋白质和基因组序列
- **安装命令**:
  ```bash
  biodeploy install ncbi_refseq_protein
  biodeploy install ncbi_refseq_genomic
  biodeploy install ncbi_genbank
  ```

#### 2. Ensembl 数据库
- **适配器名称**: `ensembl_genomes`, `ensembl_variation`, `ensembl_regulation`
- **描述**: Ensembl 基因组、变异和调控数据库
- **大小**: ~10GB
- **用途**: 基因组注释、变异分析
- **安装命令**:
  ```bash
  biodeploy install ensembl_genomes
  biodeploy install ensembl_variation
  ```

#### 3. UCSC 数据库
- **适配器名称**: `ucsc_genome_hg38`, `ucsc_genome_hg19`, `ucsc_tables`
- **描述**: UCSC Genome Browser 数据
- **大小**: ~50GB (取决于基因组版本)
- **用途**: 基因组浏览器数据
- **安装命令**:
  ```bash
  biodeploy install ucsc_genome_hg38
  biodeploy install ucsc_genome_hg19
  ```

### 功能注释数据库

#### 4. eggNOG 数据库 ⭐⭐⭐⭐⭐
- **适配器名称**: `eggnog_eggnog`, `eggnog_fungi`, `eggnog_bacteria`, `eggnog_archaea`, `eggnog_metazoa`
- **描述**: 正交群和功能注释数据库
- **大小**: ~2GB
- **用途**: 最全面的非监督功能注释首选
- **常用工具**: eggNOG-mapper
- **安装命令**:
  ```bash
  biodeploy install eggnog_eggnog
  biodeploy install eggnog_fungi
  biodeploy install eggnog_bacteria
  ```

#### 5. KEGG 数据库 ⭐⭐⭐⭐⭐
- **适配器名称**: `kegg_full`, `kegg_genes`, `kegg_genome`, `kegg_pathway`, `kegg_reaction`, `kegg_compound`
- **描述**: 京都基因与基因组百科全书
- **大小**: ~10GB
- **用途**: 代谢通路可视化必备
- **常用工具**: KEGG Mapper, pathview
- **安装命令**:
  ```bash
  biodeploy install kegg_full
  biodeploy install kegg_pathway
  ```

#### 6. GO 数据库 ⭐⭐⭐⭐
- **适配器名称**: `go`
- **描述**: Gene Ontology 数据库
- **大小**: ~100MB
- **用途**: 通用功能富集分析
- **常用工具**: clusterProfiler, topGO
- **安装命令**:
  ```bash
  biodeploy install go
  ```

#### 7. COG 数据库 ⭐⭐⭐
- **适配器名称**: `cog`
- **描述**: 正交群分类数据库
- **大小**: ~50MB
- **用途**: 老牌正交群分类（仍在使用，但逐渐被 eggNOG 取代）
- **安装命令**:
  ```bash
  biodeploy install cog
  ```

#### 8. Swiss-Prot 数据库 ⭐⭐⭐⭐
- **适配器名称**: `swissprot`
- **描述**: 高质量手动注释蛋白质数据库
- **大小**: ~5GB
- **用途**: 精确注释时常用
- **常用工具**: BLAST, InterProScan
- **安装命令**:
  ```bash
  biodeploy install swissprot
  ```

###  specialty 数据库

#### 9. CAZy 数据库 ⭐⭐⭐⭐☆
- **适配器名称**: `cazy`
- **描述**: 碳水化合物活性酶数据库
- **大小**: ~500MB
- **用途**: 降解、纤维素酶等研究必备
- **常用工具**: dbCAN2
- **安装命令**:
  ```bash
  biodeploy install cazy
  ```

#### 10. CARD/RGI 数据库 ⭐⭐⭐⭐⭐
- **适配器名称**: `card_rgi`
- **描述**: 综合抗生素抗性基因数据库
- **大小**: ~1GB
- **用途**: 耐药性研究最权威
- **常用工具**: RGI (Resistance Gene Identifier)
- **安装命令**:
  ```bash
  biodeploy install card_rgi
  ```

#### 11. VFDB 数据库 ⭐⭐⭐⭐
- **适配器名称**: `vfdb`
- **描述**: 毒力因子数据库
- **大小**: ~800MB
- **用途**: 致病性研究
- **常用工具**: VFDB Blast
- **安装命令**:
  ```bash
  biodeploy install vfdb
  ```

## 使用示例

### 安装单个数据库
```bash
# 安装 eggNOG 数据库
biodeploy install eggnog_eggnog

# 安装 KEGG 数据库
biodeploy install kegg_full

# 安装 CARD 抗性基因数据库
biodeploy install card_rgi
```

### 实际使用（推荐最小可验证流程）

```bash
# 1) 先列出全部可下载数据库（可选导出）
biodeploy list --available --format json -o biodeploy-catalog.json

# 2) 选择一个体量较小/下载快的库做验证（例如 go / cog）
biodeploy install go --path ~/bio_databases

# 3) 查看安装状态并确认文件落盘
biodeploy status go --detail
```

### 批量安装多个数据库
```bash
# 安装所有功能注释数据库
biodeploy install eggnog_eggnog kegg_full go swissprot

# 安装所有 specialty 数据库
biodeploy install cazy card_rgi vfdb
```

### 查看已安装的数据库
```bash
# 查看所有已安装的数据库
biodeploy list --installed

# 查看数据库状态
biodeploy status eggnog_eggnog
```

### 更新数据库
```bash
# 检查更新
biodeploy update --check-only

# 更新所有数据库
biodeploy update

# 更新指定数据库
biodeploy update eggnog_eggnog kegg_full
```

### 卸载数据库
```bash
# 卸载单个数据库
biodeploy remove eggnog_eggnog

# 批量卸载
biodeploy remove cazy vfdb
```

## 数据库推荐组合

### 宏基因组分析推荐
```bash
biodeploy install eggnog_eggnog kegg_full card_rgi vfdb cazy go
```

### 转录组分析推荐
```bash
biodeploy install eggnog_eggnog kegg_pathway go swissprot
```

### 耐药性研究推荐
```bash
biodeploy install card_rgi eggnog_bacteria vfdb
```

### 真菌研究推荐
```bash
biodeploy install eggnog_fungi cazy go kegg_full
```

## 系统要求

所有数据库安装需要：
- Python 3.8+
- 足够的磁盘空间（见各数据库大小）
- wget 或 curl（用于下载）
- tar 和 gzip（用于解压）

某些数据库可能需要额外的工具：
- eggNOG: emapper
- CARD: RGI
- CAZy: dbCAN2

## 注意事项

1. **许可证**: 部分数据库有使用限制，请遵守各数据库的许可证要求
2. **网络**: 首次下载需要稳定的网络连接
3. **磁盘空间**: 建议预留数据库大小 2-3 倍的磁盘空间
4. **内存**: 大型数据库（如 KEGG）可能需要较多内存进行处理

## 数据库来源

- eggNOG: http://eggnogdb.embl.de/
- KEGG: https://www.kegg.jp/
- CAZy: http://www.cazy.org/
- CARD: https://card.mcmaster.ca/
- VFDB: http://www.mgc.ac.cn/VFs/
- GO: http://geneontology.org/
- COG: https://www.ncbi.nlm.nih.gov/research/cog/
- Swiss-Prot: https://www.uniprot.org/
