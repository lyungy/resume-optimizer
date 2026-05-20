"""
简历优化系统 - FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import config
from models.database import init_db


# 应用生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print(f"✅ 数据库初始化完成: {config.database.url}")
    yield
    # 关闭时清理资源
    print("👋 应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="针对中小企业（对大龄 IT 从业人员友好）的简历优化系统",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from api import (
    company_router,
    jd_router,
    resume_router,
    optimization_router,
    interview_router,
    llm_router,
    stats_router,
)

app.include_router(company_router, prefix="/api/v1")
app.include_router(jd_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(optimization_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(llm_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")


@app.get("/")
def root():
    """根路径"""
    return {
        "name": config.app_name,
        "version": config.app_version,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.backend_host,
        port=config.backend_port,
        reload=config.debug,
    )
