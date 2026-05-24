#!/bin/bash
# 简历优化系统启动脚本

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

echo "🚀 启动简历优化系统..."

# 检查并导入 LLM 配置
if [ ! -f "$PROJECT_DIR/backend/config.yaml" ]; then
  echo "📥 导入 LLM 配置..."
  $VENV_PYTHON "$PROJECT_DIR/backend/scripts/import_llm_config.py"
fi

# 启动后端
echo "🔧 启动后端服务 (端口 8000)..."
cd "$PROJECT_DIR/backend"
"$PROJECT_DIR/.venv/bin/uvicorn" main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务 (端口 5173)..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "📍 访问地址："
echo "   前端: http://localhost:5173"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待进程
wait
