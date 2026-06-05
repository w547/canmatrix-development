#!/bin/bash
echo "========================================"
echo "  DbcTool 可视化转换工具"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "[1/2] 检查依赖..."
pip install Flask canmatrix --quiet 2>/dev/null

export PYTHONPATH="$(pwd)/../src:$PYTHONPATH"

echo "[2/2] 启动服务..."
python app.py
