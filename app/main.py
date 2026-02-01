"""
Knowledge Capsule Hub - FastAPI 主应用 v0.3.0
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
    description="AI 时代的知识资产交易所 - v0.3.0 溯源系统",
    version="0.3.0"
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

# 挂载旧版溯源 API (兼容)
try:
    from .api.provenance import router as provenance_router
    app.include_router(provenance_router, prefix="/api/capsules")
except ImportError:
    pass

# 挂载新版溯源 API v0.3.0
try:
    from .api.provenance_v2 import router as provenance_v2_router
    app.include_router(provenance_v2_router)
except ImportError as e:
    print(f"Warning: Could not load provenance v2 API: {e}")

# 挂载静态文件
ui_path = Path(__file__).parent / "ui"
if ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_path)), name="static")


# 简单的健康检查
@app.get("/health")
async def health():
    return {"status": "ok", "service": "knowledge-capsule-hub", "version": "0.3.0"}


# UI 页面
@app.get("/")
async def index():
    """主页"""
    index_file = Path(__file__).parent / "ui" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "Knowledge Capsule Hub",
        "version": "0.3.0",
        "description": "AI 时代的知识资产交易所 - 知识胶囊溯源系统",
        "ui": "UI not found, run 'python scripts/init_demo.py' first",
        "docs": "/docs"
    }


# API 信息
@app.get("/info")
async def info():
    return {
        "service": "Knowledge Capsule Hub",
        "version": "0.3.0",
        "description": "AI 时代的知识资产交易所 - 知识胶囊溯源系统 v0.3.0",
        "docs": "/docs",
        "features": [
            "知识胶囊管理",
            "DATM 质量评估",
            "今日/昨日精选",
            "胶囊溯源系统 v0.3.0",
            "版本演进追踪",
            "引用计数系统",
            "验证记录管理",
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
            # 旧版溯源系统
            "provenance": "/api/capsules/{id}/provenance",
            "versions": "/api/capsules/{id}/versions",
            "evolution": "/api/capsules/{id}/evolution",
            "knowledge_graph": "/api/capsules/graph/overview",
            # v0.3.0 新版溯源 API
            "provenance_register": "/api/v1/provenance/register",
            "provenance_get": "/api/v1/provenance/{capsule_id}",
            "provenance_version": "/api/v1/provenance/{capsule_id}/version",
            "provenance_versions": "/api/v1/provenance/{capsule_id}/versions",
            "provenance_evolve": "/api/v1/provenance/{capsule_id}/evolve",
            "provenance_evolution": "/api/v1/provenance/{capsule_id}/evolution",
            "provenance_cite": "/api/v1/provenance/cite",
            "provenance_citations": "/api/v1/provenance/{capsule_id}/citations",
            "provenance_validate": "/api/v1/provenance/{capsule_id}/validate",
            "provenance_validations": "/api/v1/provenance/{capsule_id}/validations",
            "provenance_graph": "/api/v1/provenance/graph",
            "provenance_graph_overview": "/api/v1/provenance/graph/overview"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
