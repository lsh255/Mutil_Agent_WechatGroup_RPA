#!/bin/bash

# 快速启动脚本 - Linux/Mac版本

echo "========================================"
echo "多模态Agent微信群自动化项目"
echo "快速启动脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.12+"
    exit 1
fi

echo "[1/6] 检查Docker是否运行..."
if ! docker ps &> /dev/null; then
    echo "[错误] Docker未运行，请先启动Docker"
    exit 1
fi
echo "[完成] Docker运行正常"
echo ""

echo "[2/6] 安装Python依赖..."
pip install -e . -q
if [ $? -ne 0 ]; then
    echo "[错误] 依赖安装失败"
    exit 1
fi
echo "[完成] 依赖安装成功"
echo ""

echo "[3/6] 启动基础设施服务（Redis和Ollama）..."
docker-compose up -d redis ollama
if [ $? -ne 0 ]; then
    echo "[错误] 基础设施启动失败"
    exit 1
fi
echo "[完成] 基础设施启动成功"
echo ""

echo "[4/6] 创建必要的目录和模板..."
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates

python3 scripts/create_excel_template.py
echo "[完成] 目录和模板创建成功"
echo ""

echo "[5/6] 初始化知识库..."
python3 scripts/init_knowledge_base.py
if [ $? -ne 0 ]; then
    echo "[警告] 知识库初始化失败，但可以继续"
fi
echo "[完成] 知识库初始化完成"
echo ""

echo "[6/6] 启动协调中心服务..."
echo "提示：协调中心将在 http://localhost:8000 启动"
echo "按 Ctrl+C 可以停止服务"
echo ""
uvicorn services.orchestrator.main:app --host 0.0.0.0 --port 8000 --reload
