"""
胶囊溯源 API v0.3.0
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.provenance import (
    provenance_storage, ProvenanceType, EvolutionType, ValidationStatus
)
from ..core.storage import storage


router = APIRouter(prefix="/api/v1/provenance", tags=["provenance"])


# ========== 请求模型 ==========

class RegisterRequest(BaseModel):
    """注册胶囊请求"""
    capsule_id: str = Field(..., description="胶囊ID")
    source_type: str = Field(default="manual", description="来源类型")
    source_id: Optional[str] = Field(None, description="来源ID")
    source_data: Optional[Dict] = Field(None, description="来源数据")
    initial_version: str = Field(default="v1.0.0", description="初始版本")
    author: str = Field(default="system", description="作者")
    content_hash: str = Field(default="", description="内容哈希")


class UpdateVersionRequest(BaseModel):
    """更新版本请求"""
    version: str = Field(..., description="新版本号")
    changes: str = Field(default="", description="变更说明")
    reason: str = Field(default="", description="变更原因")
    author: str = Field(default="system", description="作者")
    datm_score: Optional[Dict] = Field(None, description="DATM评分")
    content_hash: str = Field(default="", description="内容哈希")


class EvolutionRequest(BaseModel):
    """演进关系请求"""
    related_capsule_id: str = Field(..., description="关联胶囊ID")
    relation_type: str = Field(..., description="关系类型")
    strength: float = Field(default=1.0, ge=0, le=1, description="关系强度")
    metadata: Optional[Dict] = Field(None, description="额外元数据")


class CitationRequest(BaseModel):
    """引用请求"""
    source_capsule_id: str = Field(..., description="引用来源胶囊ID")
    context: str = Field(default="", description="引用上下文")
    strength: float = Field(default=1.0, ge=0, le=1, description="引用强度")


class ValidationRequest(BaseModel):
    """验证请求"""
    validator: str = Field(..., description="验证者")
    status: str = Field(default="pending", description="验证状态")
    evidence: str = Field(default="", description="证据")
    comments: str = Field(default="", description="评论")
    score: Optional[float] = Field(None, ge=0, le=100, description="验证评分")


# ========== 胶囊注册 ==========

@router.post("/register")
async def register_capsule(request: RegisterRequest):
    """注册胶囊"""
    # 验证胶囊是否存在
    capsule = storage.get(request.capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {request.capsule_id} not found")
    
    try:
        provenance = provenance_storage.register_capsule(
            capsule_id=request.capsule_id,
            source_type=request.source_type,
            source_id=request.source_id,
            source_data=request.source_data,
            initial_version=request.initial_version,
            author=request.author,
            content_hash=request.content_hash
        )
        
        return {
            "status": "success",
            "message": "Capsule registered successfully",
            "provenance": provenance.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{capsule_id}")
async def get_provenance(capsule_id: str):
    """获取胶囊溯源信息"""
    provenance = provenance_storage.get_provenance(capsule_id)
    if not provenance:
        # 检查胶囊是否存在
        capsule = storage.get(capsule_id)
        if not capsule:
            raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
        
        # 返回空溯源
        return {
            "capsule_id": capsule_id,
            "status": "not_registered",
            "message": "Capsule exists but provenance not yet registered"
        }
    
    return {
        "status": "success",
        "provenance": provenance.to_dict()
    }


# ========== 版本管理 ==========

@router.post("/{capsule_id}/version")
async def update_version(capsule_id: str, request: UpdateVersionRequest):
    """更新胶囊版本"""
    # 验证胶囊是否存在
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    # 验证溯源是否存在
    provenance = provenance_storage.get_provenance(capsule_id)
    if not provenance:
        raise HTTPException(status_code=400, detail="Provenance not registered")
    
    try:
        version = provenance_storage.update_version(
            capsule_id=capsule_id,
            version=request.version,
            changes=request.changes,
            reason=request.reason,
            author=request.author,
            datm_score=request.datm_score,
            content_hash=request.content_hash
        )
        
        return {
            "status": "success",
            "message": f"Version {request.version} added",
            "version": version.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{capsule_id}/versions")
async def get_version_history(capsule_id: str):
    """获取版本历史"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    history = provenance_storage.get_version_history(capsule_id)
    if not history:
        return {
            "capsule_id": capsule_id,
            "current_version": capsule.version,
            "versions": [],
            "message": "No version history"
        }
    
    return {
        "capsule_id": capsule_id,
        "current_version": history.current_version,
        "version_count": history.version_count,
        "versions": [v.model_dump() for v in history.versions]
    }


# ========== 演进关系 ==========

@router.post("/{capsule_id}/evolve")
async def add_evolution(capsule_id: str, request: EvolutionRequest):
    """添加演进关系"""
    # 验证胶囊是否存在
    capsule = storage.get(capsule_id)
    related = storage.get(request.related_capsule_id)
    
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    if not related:
        raise HTTPException(status_code=404, detail=f"Related capsule {request.related_capsule_id} not found")
    
    try:
        relation = provenance_storage.add_evolution(
            capsule_id=capsule_id,
            related_capsule_id=request.related_capsule_id,
            relation_type=request.relation_type,
            strength=request.strength,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": f"Evolution relation added: {capsule_id} -> {request.related_capsule_id}",
            "relation": relation.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{capsule_id}/evolution")
async def get_evolution(capsule_id: str):
    """获取演进关系"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    evolution = provenance_storage.get_evolution(capsule_id)
    if not evolution:
        return {
            "capsule_id": capsule_id,
            "parent_id": None,
            "child_ids": [],
            "branches": [],
            "relations": [],
            "message": "No evolution relations"
        }
    
    return {
        "capsule_id": capsule_id,
        "parent_id": evolution.parent_id,
        "child_ids": evolution.child_ids,
        "branches": evolution.branches,
        "relations": [r.model_dump() for r in evolution.relations]
    }


# ========== 引用计数 ==========

@router.post("/cite")
async def add_citation(request: CitationRequest):
    """添加引用"""
    # 验证胶囊是否存在
    source = storage.get(request.source_capsule_id)
    target = storage.get(request.target_capsule_id or "")
    
    if not source:
        raise HTTPException(status_code=404, detail=f"Source capsule {request.source_capsule_id} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target capsule not found")
    
    citation = provenance_storage.add_citation(
        source_capsule_id=request.source_capsule_id,
        target_capsule_id=request.target_capsule_id or "",
        context=request.context,
        strength=request.strength
    )
    
    # 更新胶囊的引用计数
    target.citations += 1
    storage.update(request.target_capsule_id or "", target)
    
    return {
        "status": "success",
        "message": f"Citation added: {request.source_capsule_id} cites {request.target_capsule_id}",
        "citation": citation.model_dump(),
        "target_citations": target.citations
    }


@router.get("/{capsule_id}/citations")
async def get_citations(capsule_id: str):
    """获取引用信息"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    citations = provenance_storage.get_citations(capsule_id)
    if not citations:
        return {
            "capsule_id": capsule_id,
            "count": 0,
            "citing_capsules": []
        }
    
    return {
        "capsule_id": capsule_id,
        "count": citations.count,
        "citing_capsules": citations.get_citing_capsules()
    }


# ========== 验证记录 ==========

@router.post("/{capsule_id}/validate")
async def validate_capsule(capsule_id: str, request: ValidationRequest):
    """验证胶囊"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    validation = provenance_storage.validate(
        capsule_id=capsule_id,
        validator=request.validator,
        status=request.status,
        evidence=request.evidence,
        comments=request.comments,
        score=request.score
    )
    
    # 更新胶囊的验证状态
    if request.status == "verified":
        capsule.validations += 1
        storage.update(capsule_id, capsule)
    
    return {
        "status": "success",
        "message": "Validation recorded",
        "validation": validation.model_dump()
    }


@router.get("/{capsule_id}/validations")
async def get_validations(capsule_id: str):
    """获取验证记录"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    record = provenance_storage.get_validations(capsule_id)
    if not record:
        return {
            "capsule_id": capsule_id,
            "validations": [],
            "verified_count": 0,
            "disputed_count": 0
        }
    
    return {
        "capsule_id": capsule_id,
        "validations": [v.model_dump() for v in record.validations],
        "verified_count": record.get_verified_count(),
        "disputed_count": record.get_disputed_count()
    }


# ========== 知识图谱 ==========

@router.get("/graph")
async def get_evolution_graph(
    capsule_id: str = Query(..., description="根胶囊ID"),
    depth: int = Query(default=3, ge=1, le=5, description="遍历深度")
):
    """获取演进图谱"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    
    graph = provenance_storage.get_evolution_graph(capsule_id, depth=depth)
    
    return {
        "root_capsule_id": capsule_id,
        "depth": depth,
        "graph": graph
    }


@router.get("/graph/overview")
async def get_graph_overview(limit: int = Query(default=50, ge=1, le=200)):
    """获取知识图谱概览"""
    summaries = provenance_storage.get_all_provenance_summary(limit=limit)
    
    # 构建简单图
    graph = {
        "nodes": [],
        "edges": []
    }
    
    for item in summaries:
        graph["nodes"].append({
            "id": item["capsule_id"],
            "type": item["source_type"],
            "version": item["current_version"],
            "versions": item["version_count"],
            "citations": item["citation_count"],
            "verified": item["verified_count"] > 0
        })
    
    return {
        "total_capsules": len(summaries),
        "graph": graph
    }


# ========== 批量操作 ==========

@router.post("/batch/register")
async def batch_register(capsule_ids: List[str]):
    """批量注册胶囊"""
    results = []
    for cid in capsule_ids:
        capsule = storage.get(cid)
        if not capsule:
            results.append({"capsule_id": cid, "status": "error", "message": "Capsule not found"})
            continue
        
        try:
            provenance = provenance_storage.register_capsule(
                capsule_id=cid,
                source_type="manual",
                author="system"
            )
            results.append({"capsule_id": cid, "status": "success", "version": "v1.0.0"})
        except ValueError:
            results.append({"capsule_id": cid, "status": "skipped", "message": "Already registered"})
    
    return {
        "total": len(capsule_ids),
        "success": sum(1 for r in results if r["status"] == "success"),
        "results": results
    }
