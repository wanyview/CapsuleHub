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


# ========== 今日/昨日精选 ==========

@router.get("/featured/today")
async def get_todays_featured():
    """获取今日精选胶囊"""
    capsule = storage.get_todays_featured()
    if not capsule:
        # 自动选择
        capsule = storage.auto_select_featured()
        if not capsule:
            raise HTTPException(status_code=404, detail="No capsules available")
    
    score_breakdown = datm_evaluator.get_score_breakdown(capsule)
    return CapsuleResponse(
        capsule=capsule,
        score_breakdown=score_breakdown
    )


@router.get("/featured/yesterday")
async def get_yesterdays_featured():
    """获取昨日精选胶囊"""
    capsule = storage.get_yesterdays_featured()
    if not capsule:
        raise HTTPException(status_code=404, detail="No featured capsule for yesterday")
    
    score_breakdown = datm_evaluator.get_score_breakdown(capsule)
    return CapsuleResponse(
        capsule=capsule,
        score_breakdown=score_breakdown
    )


@router.get("/featured/{date}")
async def get_featured_by_date(date: str):
    """获取指定日期的精选胶囊"""
    capsule = storage.get_featured_by_date(date)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"No featured capsule for {date}")
    
    score_breakdown = datm_evaluator.get_score_breakdown(capsule)
    return CapsuleResponse(
        capsule=capsule,
        score_breakdown=score_breakdown
    )


@router.get("/featured/history")
async def get_featured_history(days: int = 7):
    """获取精选历史"""
    history = storage.get_featured_history(days=days)
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/featured/")
async def set_featured(capsule_id: str, date: str, reason: str = ""):
    """手动设置精选胶囊"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    storage.set_featured(capsule_id, date, reason)
    return {
        "status": "success",
        "message": f"Capsule {capsule_id} set as featured for {date}",
        "capsule": capsule
    }


@router.post("/featured/auto-select")
async def auto_select_featured(date: Optional[str] = None):
    """自动选择精选胶囊"""
    capsule = storage.auto_select_featured(date)
    if not capsule:
        raise HTTPException(status_code=404, detail="No capsules available")
    
    return {
        "status": "success",
        "message": f"Auto-selected capsule for {date or 'today'}",
        "capsule": capsule
    }


# ========== 精选统计 ==========

@router.get("/featured/stats")
async def get_featured_stats():
    """获取精选统计信息"""
    history = storage.get_featured_history(days=30)
    
    if not history:
        return {
            "total_featured": 0,
            "domains": {},
            "avg_score": 0,
            "top_grade": "N/A"
        }
    
    # 统计
    total = len(history)
    domains = {}
    total_score = 0
    
    for item in history:
        c = item["capsule"]
        d = c.domain
        domains[d] = domains.get(d, 0) + 1
        total_score += c.overall_score
    
    avg_score = total_score / total if total > 0 else 0
    
    # 评分分布
    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    for item in history:
        grade = item["capsule"].overall_grade
        if grade in grade_dist:
            grade_dist[grade] += 1
    
    return {
        "total_featured": total,
        "domains": domains,
        "avg_score": round(avg_score, 1),
        "grade_distribution": grade_dist,
        "last_updated": history[0]["date"] if history else None
    }


@router.get("/featured/random")
async def get_random_featured(limit: int = 3):
    """随机获取精选胶囊（用于展示）"""
    history = storage.get_featured_history(days=30)
    
    if not history:
        raise HTTPException(status_code=404, detail="No featured capsules")
    
    import random
    selected = random.sample(history, min(limit, len(history)))
    
    capsules = []
    for item in selected:
        c = item["capsule"]
        capsules.append({
            **c.model_dump(),
            "featured_date": item["date"],
            "reason": item.get("reason", "")
        })
    
    return {"capsules": capsules, "count": len(capsules)}


# ========== 胶囊对比 ==========

@router.post("/compare")
async def compare_capsules(capsule_ids: List[str]):
    """对比多个胶囊"""
    capsules = []
    for cid in capsule_ids:
        c = storage.get(cid)
        if c:
            capsules.append({
                "capsule": c,
                "score_breakdown": datm_evaluator.get_score_breakdown(c)
            })
    
    return {
        "capsules": capsules,
        "count": len(capsules)
    }
