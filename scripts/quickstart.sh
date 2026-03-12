#!/bin/bash
# BioDeploy 快速开始脚本

set -e

echo "================================"
echo "BioDeploy 快速开始"
echo "================================"
echo ""

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 检查Python版本是否>=3.8
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "错误: 需要Python 3.8或更高版本"
    exit 1
fi

echo "✓ Python版本符合要求"
echo ""

# 创建虚拟环境（可选）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"
echo ""

# 安装依赖
echo "安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依赖已安装"
echo ""

# 安装biodeploy
echo "安装BioDeploy..."
pip install -e .
echo "✓ BioDeploy已安装"
echo ""

# 运行测试
echo "运行测试..."
python -m pytest tests/unit/test_models.py -v
echo "✓ 测试完成"
echo ""

# 显示帮助信息
echo "================================"
echo "安装完成！"
echo "================================"
echo ""
echo "快速开始:"
echo "  biodeploy --help           # 查看帮助"
echo "  biodeploy list             # 列出可用数据库"
echo "  biodeploy install ncbi     # 安装NCBI数据库"
echo ""
echo "配置文件位置: ~/.biodeploy/config.yaml"
echo "日志文件位置: ~/.biodeploy/logs/"
echo ""
