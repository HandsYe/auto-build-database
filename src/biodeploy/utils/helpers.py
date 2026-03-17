"""
辅助工具函数

提供常用的辅助函数。
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Iterator
from biodeploy.infrastructure.logger import get_logger


def format_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化时间间隔
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def calculate_file_hash(
    file_path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256, sha512)
        chunk_size: 读取块大小
        
    Returns:
        哈希值字符串
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_remove(path: Union[str, Path]) -> bool:
    """安全删除文件或目录
    
    Args:
        path: 文件或目录路径
        
    Returns:
        是否成功删除
    """
    logger = get_logger("helpers")
    path = Path(path)
    
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        logger.warning(f"删除 {path} 失败: {e}")
        return False


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    chunk_size: int = 8192
) -> int:
    """复制文件（支持大文件）
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        chunk_size: 复制块大小
        
    Returns:
        复制的字节数
    """
    src = Path(src)
    dst = Path(dst)
    
    # 确保目标目录存在
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    with open(src, "rb") as f_src, open(dst, "wb") as f_dst:
        while True:
            chunk = f_src.read(chunk_size)
            if not chunk:
                break
            f_dst.write(chunk)
            copied += len(chunk)
    
    return copied


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True
) -> Iterator[Path]:
    """查找文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        recursive: 是否递归查找
        
    Yields:
        文件路径
    """
    directory = Path(directory)
    
    if recursive:
        yield from directory.rglob(pattern)
    else:
        yield from directory.glob(pattern)


def get_file_info(file_path: Union[str, Path]) -> Dict[str, any]:
    """获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    file_path = Path(file_path)
    stat = file_path.stat()
    
    return {
        "path": str(file_path),
        "name": file_path.name,
        "size": stat.st_size,
        "size_formatted": format_size(stat.st_size),
        "modified_time": stat.st_mtime,
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "extension": file_path.suffix,
    }


def compare_versions(version1: str, version2: str) -> int:
    """比较版本号
    
    Args:
        version1: 版本号1
        version2: 版本号2
        
    Returns:
        -1: version1 < version2
        0: version1 == version2
        1: version1 > version2
    """
    def normalize(v):
        return [int(x) for x in v.split(".")]
    
    v1 = normalize(version1)
    v2 = normalize(version2)
    
    # 补齐版本号长度
    max_len = max(len(v1), len(v2))
    v1.extend([0] * (max_len - len(v1)))
    v2.extend([0] * (max_len - len(v2)))
    
    for a, b in zip(v1, v2):
        if a < b:
            return -1
        elif a > b:
            return 1
    
    return 0


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串
    
    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def merge_dicts(*dicts: Dict) -> Dict:
    """合并多个字典
    
    Args:
        dicts: 要合并的字典
        
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并字典
    
    Args:
        dict1: 字典1
        dict2: 字典2
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def batch_process(
    items: List,
    process_func,
    batch_size: int = 10,
    progress_callback: Optional[callable] = None
) -> List:
    """批量处理
    
    Args:
        items: 要处理的项列表
        process_func: 处理函数
        batch_size: 批次大小
        progress_callback: 进度回调
        
    Returns:
        处理结果列表
    """
    results = []
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_results = [process_func(item) for item in batch]
        results.extend(batch_results)
        
        if progress_callback:
            progress = min(i + batch_size, total) / total
            progress_callback(progress, i + len(batch), total)
    
    return results
