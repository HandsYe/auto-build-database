"""
单元测试 - AdapterRegistry 动态解析

确保 `biodeploy list`/`install` 能发现并解析多变体数据库名称。
"""

from biodeploy.adapters.adapter_registry import AdapterRegistry


def test_list_adapters_includes_variants():
    registry = AdapterRegistry()
    names = set(registry.list_adapters())

    # NCBI variants
    assert "ncbi_refseq_protein" in names
    assert "ncbi_refseq_genomic" in names
    assert "ncbi_genbank" in names

    # KEGG variants (移除了 full，因为它需要商业许可)
    assert "kegg_pathway" in names
    assert "kegg_genes" in names

    # eggNOG variants
    assert "eggnog_eggnog" in names
    assert "eggnog_bacteria" in names

    # UCSC common genomes (新格式包含 file_type)
    assert "ucsc_genome_hg38_fasta" in names
    assert "ucsc_genome_hg38_2bit" in names
    assert "ucsc_genome_hg19_fasta" in names


def test_get_resolves_dynamic_adapter_instances():
    registry = AdapterRegistry()

    ncbi = registry.get("ncbi_genbank")
    assert ncbi is not None
    assert ncbi.database_name == "ncbi_genbank"

    kegg = registry.get("kegg_pathway")
    assert kegg is not None
    assert kegg.database_name == "kegg_pathway"

    eggnog = registry.get("eggnog_bacteria")
    assert eggnog is not None
    assert eggnog.database_name == "eggnog_bacteria"

    ucsc = registry.get("ucsc_genome_hg38_fasta")
    assert ucsc is not None
    assert ucsc.database_name == "ucsc_genome_hg38_fasta"

