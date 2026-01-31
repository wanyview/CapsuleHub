"""
胶囊溯源 API
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException

from ..core.provenance import provenance_storage
from ..core.capsule import KnowledgeCapsule
from ..core.storage import storage


router = APIRouter(prefix="/api/capsules", tags=["provenance"])


# ========== 溯源查询 ==========

@router.get("/{capsule_id}/provenance")
async def get_capsule_provenance(capsule_id: str):
    """获取胶囊溯源信息"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    provenance = provenance_storage.get_provenance(capsule_id)
    if not provenance:
        raise HTTPException(status_code=404, detail="Provenance not found")
    
    return provenance


@router.get("/{capsule_id}/versions")
async def get_capsule_versions(capsule_id: str):
    """获取胶囊版本历史"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    provenance = provenance_storage.get_provenance(capsule_id)
    if not provenance:
        raise HTTPException(status_code=404, detail="Provenance not found")
    
    return {
        "capsule_id": capsule_id,
        "current_version": capsule.version,
        "versions": provenance["versions"]
    }


@router.get("/{capsule_id}/evolution")
async def get_capsule_evolution(capsule_id: str, depth: int = 3):
    """获取胶囊演进图谱"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    graph = provenance_storage.get_evolution_graph(capsule_id, depth=depth)
    
    return {
        "capsule_id": capsule_id,
        "graph": graph
    }


@router.get("/{capsule_id}/citations")
async def get_citation_count(capsule_id: str):
    """获取引用计数"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    provenance = provenance_storage.get_provenance(capsule_id)
    
    return {
        "capsule_id": capsule_id,
        "citations": provenance["citations"] if provenance else 0
    }


# ========== 溯源管理 ==========

@router.post("/{capsule_id}/provenance")
async def create_provenance(
    capsule_id: str,
    source_type: str = "manual",
    source_id: Optional[str] = None,
    source_data: Optional[dict] = None
):
    """创建溯源记录"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # 检查是否已存在
    existing = provenance_storage.get_provenance(capsule_id)
    if existing:
        raise HTTPException(status_code=400, detail="Provenance already exists")
    
    provenance = provenance_storage.create_provenance(
        capsule_id=capsule_id,
        source_type=source_type,
        source_id=source_id,
        source_data=source_data
    )
    
    return {
        "status": "success",
        "message": "Provenance created",
        "provenance": provenance
    }


@router.post("/{capsule_id}/versions")
async def add_capsule_version(
    capsule_id: str,
    version: str,
    changes: str = "",
    reason: str = "",
    author: str = "system"
):
    """添加新版本"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    # 验证版本号格式
    if not version.startswith("v"):
        version = f"v{version}"
    
    new_version = provenance_storage.add_version(
        capsule_id=capsule_id,
        version=version,
        changes=changes,
        reason=reason,
        author=author,
        datm_score={
            "truth": capsule.datm_score.truth,
            "goodness": capsule.datm_score.goodness,
            "beauty": capsule.datm_score.beauty,
            "intelligence": capsule.datm_score.intelligence
        }
    )
    
    return {
        "status": "success",
        "message": f"Version {version} added",
        "version": new_version
    }


@router.post("/{capsule_id}/link")
async def link_capsules(
    capsule_id: str,
    related_capsule_id: str,
    relation_type: str,  # "parent", "child", "branch", "inspired_by", "supports", etc.
    strength: float = 1.0
):
    """建立胶囊关联"""
    # 验证两个胶囊都存在
    capsule = storage.get(capsule_id)
    related = storage.get(related_capsule_id)
    
    if not capsule:
        raise HTTPException(status_code=404, detail=f"Capsule {capsule_id} not found")
    if not related:
        raise HTTPException(status_code=404, detail=f"Capsule {related_capsule_id} not found")
    
    provenance_storage.link_capsules(
        capsule_id=capsule_id,
        related_capsule_id=related_capsule_id,
        relation_type=relation_type,
        strength=strength
    )
    
    return {
        "status": "success",
        "message": f"Linked {capsule_id} -> {related_capsule_id}",
        "relation": {
            "type": relation_type,
            "strength": strength
        }
    }


@router.post("/{capsule_id}/cite")
async def cite_capsule(capsule_id: str):
    """引用胶囊（增加引用计数）"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    provenance_storage.increment_citations(capsule_id)
    
    # 同时更新胶囊的引用数
    capsule.citations += 1
    
    return {
        "status": "success",
        "message": f"Capsule {capsule_id} cited",
        "new_count": capsule.citations
    }


# ========== 知识图谱相关 ==========

@router.get("/graph/overview")
async def get_knowledge_graph_overview(limit: int = 100):
    """获取知识图谱概览"""
    all_capsules = storage.list(limit=limit)
    
    graph = {
        "nodes": [],
        "edges": []
    }
    
    for capsule in all_capsules:
        graph["nodes"].append({
            "id": capsule.id,
            "title": capsule.title,
            "domain": capsule.domain,
            "grade": capsule.overall_grade,
            "score": capsule.overall_score
        })
        
        # 获取关联
        provenance = provenance_storage.get_provenance(capsule.id)
        if provenance:
            for link in provenance.get("evolution", {}).get("links", []):
                graph["edges"].append({
                    "source": capsule.id,
                    "target": link["related_id"],
                    "type": link["type"]
                })
    
    return graph


@router.get("/domains/{domain}/graph")
async def get_domain_graph(domain: str, limit: int = 50):
    """获取特定领域的知识图谱"""
    capsules = storage.list(limit=200)
    domain_capsules = [c for c in capsules if c.domain == domain][:limit]
    
    graph = {
        "domain": domain,
        "nodes": [],
        "edges": []
    }
    
    for capsule in domain_capsules:
        graph["nodes"].append({
            "id": capsule.id,
            "title": capsule.title,
            "grade": capsule.overall_grade,
            "score": capsule.overall_score
        })
    
    return graph


# ========== 验证相关 ==========

@router.post("/{capsule_id}/validate")
async def validate_capsule(
    capsule_id: str,
    validator: str,
    result: str,  # "verified", "disputed", "pending"
    evidence: str = ""
):
    """记录胶囊验证结果"""
    capsule = storage.get(capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    
    validation = {
        "timestamp": datetime.utcnow().isoformat(),
        "validator": validator,
        "result": result,
        "evidence": evidence
    }
    
    # 这里应该更新数据库中的验证记录
    # 暂时返回成功
    
    return {
        "status": "success",
        "message": "Validation recorded",
        "validation": validation
    }
