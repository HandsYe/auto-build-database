#!/bin/bash
# GitHub 推送脚本
# 使用前请先在GitHub上创建仓库

set -e

echo "=========================================="
echo "BioDeploy GitHub 推送脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Git配置
echo -e "${YELLOW}检查Git配置...${NC}"
git config user.name > /dev/null 2>&1 || { echo -e "${RED}错误: 未配置用户名${NC}"; exit 1; }
git config user.email > /dev/null 2>&1 || { echo -e "${RED}错误: 未配置邮箱${NC}"; exit 1; }
echo -e "${GREEN}✓ Git配置正常${NC}"
echo ""

# 显示当前Git配置
echo "当前Git配置:"
echo "  用户名: $(git config user.name)"
echo "  邮箱: $(git config user.email)"
echo ""

# 检查远程仓库
echo -e "${YELLOW}检查远程仓库...${NC}"
if git remote get-url origin > /dev/null 2>&1; then
    echo "已存在远程仓库:"
    git remote -v
    echo ""
    read -p "是否使用现有远程仓库? (y/n): " use_existing
    if [ "$use_existing" != "y" ]; then
        git remote remove origin
    else
        echo -e "${GREEN}✓ 使用现有远程仓库${NC}"
    fi
fi

# 如果没有远程仓库，询问用户
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "请提供GitHub仓库信息:"
    echo ""
    read -p "GitHub用户名: " github_username
    read -p "仓库名称 (默认: biodeploy): " repo_name
    repo_name=${repo_name:-biodeploy}

    # 构建远程仓库URL
    remote_url="https://github.com/${github_username}/${repo_name}.git"

    echo ""
    echo "远程仓库URL: ${remote_url}"
    echo ""
    echo -e "${YELLOW}重要提示:${NC}"
    echo "1. 请先在GitHub上创建仓库: https://github.com/new"
    echo "2. 仓库名称: ${repo_name}"
    echo "3. 不要初始化README、.gitignore或LICENSE"
    echo ""
    read -p "确认已创建仓库并继续? (y/n): " confirmed

    if [ "$confirmed" != "y" ]; then
        echo -e "${RED}取消操作${NC}"
        exit 1
    fi

    # 添加远程仓库
    git remote add origin "${remote_url}"
    echo -e "${GREEN}✓ 远程仓库已添加${NC}"
fi

echo ""
echo -e "${YELLOW}准备推送代码...${NC}"
echo ""

# 显示将要推送的内容
echo "推送内容:"
echo "  Git提交数: $(git log --oneline | wc -l)"
echo "  Python模块: $(find src -name "*.py" | wc -l)"
echo "  文档文件: $(find . -name "*.md" | wc -l)"
echo ""

# 确认推送
read -p "确认推送到GitHub? (y/n): " push_confirmed
if [ "$push_confirmed" != "y" ]; then
    echo -e "${RED}取消推送${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}正在推送代码...${NC}"
echo ""

# 推送代码
if git push -u origin main; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 推送成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "仓库地址:"
    git remote get-url origin
    echo ""
    echo "下一步:"
    echo "  1. 访问仓库查看推送结果"
    echo "  2. 设置仓库描述和Topics"
    echo "  3. 创建第一个Release (v1.0.0)"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ 推送失败${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "可能的原因:"
    echo "  1. GitHub仓库未创建或URL错误"
    echo "  2. 认证失败（用户名/密码错误）"
    echo "  3. 网络连接问题"
    echo ""
    echo "解决方案:"
    echo "  1. 确认GitHub仓库已创建"
    echo "  2. 检查远程仓库URL: git remote -v"
    echo "  3. 使用Personal Access Token进行认证"
    echo "  4. 修改远程仓库URL: git remote set-url origin <new-url>"
    echo ""
    exit 1
fi
