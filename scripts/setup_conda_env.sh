#!/bin/bash

# ========================================
# 创建并激活Conda虚拟环境
# ========================================

echo "========================================"
echo "多模态Agent微信群自动化项目"
echo "Conda环境设置脚本"
echo "========================================"
echo ""

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "[错误] 未检测到Conda，请先安装Anaconda或Miniconda"
    exit 1
fi

echo "[1/4] 检查现有环境..."
if conda env list | grep -q "wechat-workflow-agent"; then
    echo "[信息] 环境已存在，将更新依赖"
    conda env update -f environment.yml
else
    echo "[信息] 创建新环境..."
    conda env create -f environment.yml
fi

if [ $? -ne 0 ]; then
    echo "[错误] 环境创建失败"
    exit 1
fi

echo "[完成] Conda环境创建成功"
echo ""

echo "[2/4] 激活环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate wechat-workflow-agent

if [ $? -ne 0 ]; then
    echo "[错误] 环境激活失败"
    exit 1
fi

echo "[完成] 环境已激活"
echo ""

echo "[3/4] 创建必要的目录..."
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates
mkdir -p logs

echo "[完成] 目录创建成功"
echo ""

echo "[4/4] 安装项目依赖..."
pip install -e . -q

if [ $? -ne 0 ]; then
    echo "[警告] 依赖安装可能有问题，但可以继续"
else
    echo "[完成] 依赖安装成功"
fi

echo ""
echo "========================================"
echo "环境设置完成！"
echo "========================================"
echo ""
echo "使用以下命令激活环境："
echo "  conda activate wechat-workflow-agent"
echo ""
echo "使用以下命令启动服务："
echo "  bash scripts/quick_start.sh"
echo ""
