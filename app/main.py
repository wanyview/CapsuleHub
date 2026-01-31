"""
Knowledge Capsule Hub - FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .api.capsules import router as capsules_router


# 创建 FastAPI 应用
app = FastAPI(
    title="Knowledge Capsule Hub",
    description="AI 时代的知识资产交易所",
    version="0.2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API 路由
app.include_router(capsules_router)

# 挂载溯源 API
try:
    from .api.provenance import router as provenance_router
    app.include_router(provenance_router, prefix="/api/capsules")
except ImportError:
    pass  # 溯源模块可能还未加载

# 挂载静态文件
ui_path = Path(__file__).parent / "ui"
if ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_path)), name="static")


# 简单的健康检查
@app.get("/health")
async def health():
    return {"status": "ok", "service": "knowledge-capsule-hub"}


# UI 页面
@app.get("/")
async def index():
    """主页"""
    index_file = Path(__file__).parent / "ui" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "Knowledge Capsule Hub",
        "version": "0.1.0",
        "description": "AI 时代的知识资产交易所",
        "ui": "UI not found, run 'python scripts/init_demo.py' first",
        "docs": "/docs"
    }


# API 信息
@app.get("/info")
async def info():
    return {
        "service": "Knowledge Capsule Hub",
        "version": "0.2.0",
        "description": "AI 时代的知识资产交易所 - 知识胶囊溯源系统",
        "docs": "/docs",
        "features": [
            "知识胶囊管理",
            "DATM 质量评估",
            "今日/昨日精选",
            "胶囊溯源系统",  # 新功能
            "版本演进追踪",
            "知识图谱可视化"
        ],
        "endpoints": {
            # 胶囊基础
            "capsules": "/api/capsules/",
            "search": "/api/capsules/search/",
            "domains": "/api/capsules/domains/",
            "topics": "/api/capsules/topics/",
            "trending": "/api/capsules/trending/",
            # 精选功能
            "featured_today": "/api/capsules/featured/today",
            "featured_yesterday": "/api/capsules/featured/yesterday",
            "featured_history": "/api/capsules/featured/history",
            # 溯源系统 (新)
            "provenance": "/api/capsules/{id}/provenance",
            "versions": "/api/capsules/{id}/versions",
            "evolution": "/api/capsules/{id}/evolution",
            "knowledge_graph": "/api/capsules/graph/overview"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
