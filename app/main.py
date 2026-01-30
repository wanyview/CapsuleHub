"""
Knowledge Capsule Hub - FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .api.capsules import router as capsules_router


# 创建 FastAPI 应用
app = FastAPI(
    title="Knowledge Capsule Hub",
    description="AI 时代的知识资产交易所",
    version="0.1.0"
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


# 简单的健康检查
@app.get("/health")
async def health():
    return {"status": "ok", "service": "knowledge-capsule-hub"}


# API 信息
@app.get("/")
async def root():
    return {
        "service": "Knowledge Capsule Hub",
        "version": "0.1.0",
        "description": "AI 时代的知识资产交易所",
        "docs": "/docs",
        "endpoints": {
            "capsules": "/api/capsules/",
            "search": "/api/capsules/search/",
            "domains": "/api/capsules/domains/",
            "topics": "/api/capsules/topics/",
            "trending": "/api/capsules/trending/"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
