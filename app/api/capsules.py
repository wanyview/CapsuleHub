"""
胶囊 API - FastAPI
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import storage
from ..core.capsule import KnowledgeCapsule, CapsuleCreate, CapsuleSearch
from ..core.evaluator import datm_evaluator


router = APIRouter(prefix="/api/capsules", tags=["capsules"])


class CapsuleResponse(BaseModel):
    """胶囊响应"""
    capsule: KnowledgeCapsule
    score_breakdown: dict = None


class CapsuleListResponse(BaseModel):
    """胶囊列表响应"""
    capsules: List[KnowledgeCapsule]
    total: int


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[KnowledgeCapsule]
    count: int


@router.get("/", response_model=CapsuleListResponse)
async def list_capsules(limit: int = 20, offset: int = 0):
    """列出所有胶囊"""
    capsules = storage.list(limit=limit, offset=offset)
    return CapsuleListResponse(
        capsules=capsules,
        total=len(capsules)
    )


@router.get("/{capsule_id}", response_model=CapsuleResponse)
async def get_capsule(capsule_id: str):
    """获取单个胶囊"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    score_breakdown = datm_evaluator.get_score_breakdown(capsule)
    
    return CapsuleResponse(
        capsule=capsule,
        score_breakdown=score_breakdown
    )


@router.post("/", response_model=CapsuleResponse)
async def create_capsule(data: CapsuleCreate):
    """创建新胶囊"""
    capsule = storage.create(data)
    score_breakdown = datm_evaluator.get_score_breakdown(capsule)
    
    return CapsuleResponse(
        capsule=capsule,
        score_breakdown=score_breakdown
    )


@router.get("/search/", response_model=SearchResponse)
async def search_capsules(
    q: Optional[str] = None,
    domain: Optional[str] = None,
    topics: Optional[str] = None,
    min_score: Optional[float] = None,
    min_grade: Optional[str] = None,
    limit: int = 20
):
    """搜索胶囊"""
    topic_list = topics.split(",") if topics else None
    
    results = storage.search(
        query=q,
        domain=domain,
        topics=topic_list,
        min_score=min_score,
        min_grade=min_grade,
        limit=limit
    )
    
    return SearchResponse(
        query=q or "",
        results=results,
        count=len(results)
    )


@router.get("/domains/")
async def list_domains():
    """列出所有领域"""
    capsules = storage.list(limit=100)
    domains = list(set(c.domain for c in capsules))
    return {"domains": sorted(domains)}


@router.get("/topics/")
async def list_topics():
    """列出所有主题"""
    capsules = storage.list(limit=100)
    topics = set()
    for c in capsules:
        topics.update(c.topics)
    return {"topics": sorted(topics)}


@router.get("/trending/")
async def get_trending_capsules(limit: int = 10):
    """获取热门胶囊（按影响力评分）"""
    capsules = storage.list(limit=100)
    sorted_capsules = sorted(capsules, key=lambda x: x.impact_score, reverse=True)
    return {"capsules": sorted_capsules[:limit]}
