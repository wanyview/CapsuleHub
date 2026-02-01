"""
胶囊溯源系统 v0.3.0 - 版本管理和溯源追踪
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from enum import Enum
from pathlib import Path
import sqlite3
import json


class ProvenanceType(str, Enum):
    """溯源类型"""
    DISCUSSION = "discussion"  # 来自讨论
    MANUAL = "manual"          # 手动创建
    IMPORT = "import"          # 导入


class EvolutionType(str, Enum):
    """演进类型"""
    PARENT = "parent"          # 父版本
    CHILD = "child"            # 子版本
    BRANCH = "branch"          # 分支
    MERGE = "merge"            # 合并
    INSPIRED_BY = "inspired_by"  # 启发
    SUPPORTS = "supports"      # 支持
    CONTRADICTS = "contradicts" # 矛盾


class ValidationStatus(str, Enum):
    """验证状态"""
    PENDING = "pending"       # 待验证
    VERIFIED = "verified"     # 已验证
    DISPUTED = "disputed"     # 有争议
    EXPIRED = "expired"       # 已过期


class CapsuleVersion(BaseModel):
    """胶囊版本"""
    version: str = Field(..., description="版本号 (如: v1.0.0)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changes: str = Field(default="", description="变更说明")
    reason: str = Field(default="", description="变更原因")
    author: str = Field(default="system", description="作者")
    datm_score: Dict[str, float] = Field(default_factory=dict, description="DATM评分")
    hash: str = Field(default="", description="内容哈希")


class VersionHistory(BaseModel):
    """版本历史管理"""
    capsule_id: str = Field(..., description="胶囊ID")
    versions: List[CapsuleVersion] = Field(default_factory=list, description="版本列表")
    current_version: str = Field(default="v1.0.0", description="当前版本")
    version_count: int = Field(default=0, description="版本数量")
    
    def add_version(self, version: CapsuleVersion) -> CapsuleVersion:
        """添加新版本"""
        self.versions.append(version)
        self.current_version = version.version
        self.version_count = len(self.versions)
        return version
    
    def get_version(self, version: str) -> Optional[CapsuleVersion]:
        """获取指定版本"""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def get_latest(self) -> Optional[CapsuleVersion]:
        """获取最新版本"""
        if self.versions:
            return self.versions[-1]
        return None


class EvolutionRelation(BaseModel):
    """演进关系"""
    related_capsule_id: str = Field(..., description="关联胶囊ID")
    relation_type: EvolutionType = Field(..., description="关系类型")
    strength: float = Field(default=1.0, ge=0, le=1, description="关系强度")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class Evolution(BaseModel):
    """演进关系追踪"""
    capsule_id: str = Field(..., description="胶囊ID")
    parent_id: Optional[str] = Field(None, description="父胶囊ID")
    child_ids: List[str] = Field(default_factory=list, description="子胶囊ID列表")
    branches: List[str] = Field(default_factory=list, description="分支列表")
    relations: List[EvolutionRelation] = Field(default_factory=list, description="关联关系")
    
    def add_relation(self, relation: EvolutionRelation):
        """添加演进关系"""
        self.relations.append(relation)
        
        # 更新子胶囊列表
        if relation.relation_type == EvolutionType.CHILD:
            if relation.related_capsule_id not in self.child_ids:
                self.child_ids.append(relation.related_capsule_id)
        elif relation.relation_type == EvolutionType.PARENT:
            self.parent_id = relation.related_capsule_id
        elif relation.relation_type == EvolutionType.BRANCH:
            if relation.related_capsule_id not in self.branches:
                self.branches.append(relation.related_capsule_id)
    
    def get_ancestors(self) -> List[str]:
        """获取祖先链"""
        ancestors = []
        current = self.parent_id
        while current:
            ancestors.append(current)
            # 需要从数据库获取父级的父级
            current = None  # 简化处理
        return ancestors
    
    def get_descendants(self) -> List[str]:
        """获取后代链"""
        return self.child_ids + self.branches


class Validation(BaseModel):
    """验证记录"""
    validator: str = Field(..., description="验证者")
    status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence: str = Field(default="", description="证据")
    comments: str = Field(default="", description="评论")
    score: Optional[float] = Field(None, ge=0, le=100, description="验证评分")


class ValidationRecord(BaseModel):
    """验证记录管理"""
    capsule_id: str = Field(..., description="胶囊ID")
    validations: List[Validation] = Field(default_factory=list, description="验证列表")
    
    def add_validation(self, validation: Validation):
        """添加验证记录"""
        self.validations.append(validation)
    
    def get_verified_count(self) -> int:
        """获取已验证数量"""
        return sum(1 for v in self.validations if v.status == ValidationStatus.VERIFIED)
    
    def get_disputed_count(self) -> int:
        """获取有争议数量"""
        return sum(1 for v in self.validations if v.status == ValidationStatus.DISPUTED)
    
    def is_verified(self) -> bool:
        """是否已验证"""
        return self.get_verified_count() > 0


class Citation(BaseModel):
    """引用记录"""
    source_capsule_id: str = Field(..., description="引用来源胶囊ID")
    target_capsule_id: str = Field(default="", description="被引用胶囊ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: str = Field(default="", description="引用上下文")
    strength: float = Field(default=1.0, ge=0, le=1, description="引用强度")


class Citations(BaseModel):
    """引用计数管理"""
    capsule_id: str = Field(..., description="胶囊ID")
    count: int = Field(default=0, description="引用次数")
    citations: List[Citation] = Field(default_factory=list, description="引用记录")
    
    def add_citation(self, citation: Citation):
        """添加引用"""
        self.citations.append(citation)
        self.count = len(self.citations)
    
    def get_citing_capsules(self) -> List[str]:
        """获取引用该胶囊的所有胶囊ID"""
        return [c.source_capsule_id for c in self.citations]


class CapsuleProvenance(BaseModel):
    """完整胶囊溯源信息"""
    capsule_id: str = Field(..., description="胶囊ID")
    
    # 溯源信息
    source: Dict[str, Any] = Field(
        default_factory=dict,
        description="来源信息"
    )
    
    # 版本历史
    version_history: VersionHistory = Field(
        default_factory=lambda: VersionHistory(capsule_id=""),
        description="版本历史"
    )
    
    # 演进关系
    evolution: Evolution = Field(
        default_factory=lambda: Evolution(capsule_id=""),
        description="演进关系"
    )
    
    # 验证记录
    validation: ValidationRecord = Field(
        default_factory=lambda: ValidationRecord(capsule_id=""),
        description="验证记录"
    )
    
    # 引用计数
    citations: Citations = Field(
        default_factory=lambda: Citations(capsule_id=""),
        description="引用计数"
    )
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "capsule_id": self.capsule_id,
            "source": self.source,
            "version_history": {
                "capsule_id": self.version_history.capsule_id,
                "versions": [v.model_dump() for v in self.version_history.versions],
                "current_version": self.version_history.current_version,
                "version_count": self.version_history.version_count
            },
            "evolution": {
                "capsule_id": self.evolution.capsule_id,
                "parent_id": self.evolution.parent_id,
                "child_ids": self.evolution.child_ids,
                "branches": self.evolution.branches,
                "relations": [r.model_dump() for r in self.evolution.relations]
            },
            "validation": {
                "capsule_id": self.validation.capsule_id,
                "validations": [v.model_dump() for v in self.validation.validations],
                "verified_count": self.validation.get_verified_count(),
                "disputed_count": self.validation.get_disputed_count()
            },
            "citations": {
                "capsule_id": self.citations.capsule_id,
                "count": self.citations.count,
                "citing_capsules": self.citations.get_citing_capsules()
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ProvenanceStorage:
    """溯源存储引擎"""
    
    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_dir / "provenance.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 溯源主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                id TEXT PRIMARY KEY,
                capsule_id TEXT NOT NULL UNIQUE,
                source_type TEXT,
                source_id TEXT,
                source_data TEXT,
                current_version TEXT DEFAULT 'v1.0.0',
                version_count INTEGER DEFAULT 0,
                citation_count INTEGER DEFAULT 0,
                verified_count INTEGER DEFAULT 0,
                disputed_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # 版本历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT NOT NULL,
                version TEXT NOT NULL,
                changes TEXT,
                reason TEXT,
                author TEXT,
                datm_score TEXT,
                content_hash TEXT,
                timestamp TEXT,
                FOREIGN KEY (capsule_id) REFERENCES provenance(capsule_id)
            )
        """)
        
        # 演进关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT NOT NULL,
                related_capsule_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                metadata TEXT,
                timestamp TEXT,
                FOREIGN KEY (capsule_id) REFERENCES provenance(capsule_id)
            )
        """)
        
        # 验证记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT NOT NULL,
                validator TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                evidence TEXT,
                comments TEXT,
                score REAL,
                timestamp TEXT,
                FOREIGN KEY (capsule_id) REFERENCES provenance(capsule_id)
            )
        """)
        
        # 引用记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_capsule_id TEXT NOT NULL,
                target_capsule_id TEXT NOT NULL,
                context TEXT,
                strength REAL DEFAULT 1.0,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ========== 胶囊注册 ==========
    
    def register_capsule(
        self,
        capsule_id: str,
        source_type: str = "manual",
        source_id: Optional[str] = None,
        source_data: Optional[Dict] = None,
        initial_version: str = "v1.0.0",
        author: str = "system",
        content_hash: str = ""
    ) -> CapsuleProvenance:
        """注册胶囊"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("SELECT capsule_id FROM provenance WHERE capsule_id = ?", (capsule_id,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Capsule {capsule_id} already registered")
        
        now = datetime.utcnow()
        
        # 创建溯源记录
        provenance = CapsuleProvenance(
            capsule_id=capsule_id,
            source={
                "type": source_type,
                "id": source_id,
                "data": source_data or {}
            },
            version_history=VersionHistory(
                capsule_id=capsule_id,
                current_version=initial_version,
                version_count=1
            ),
            evolution=Evolution(capsule_id=capsule_id),
            validation=ValidationRecord(capsule_id=capsule_id),
            citations=Citations(capsule_id=capsule_id),
            created_at=now,
            updated_at=now
        )
        
        # 插入主记录
        cursor.execute("""
            INSERT INTO provenance 
            (id, capsule_id, source_type, source_id, source_data, current_version, 
             version_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()),
            capsule_id,
            source_type,
            source_id,
            json.dumps(source_data or {}),
            initial_version,
            1,
            now.isoformat(),
            now.isoformat()
        ))
        
        # 插入初始版本
        cursor.execute("""
            INSERT INTO versions 
            (capsule_id, version, changes, reason, author, datm_score, content_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            initial_version,
            "Initial version",
            "Initial creation",
            author,
            "{}",
            content_hash,
            now.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return provenance
    
    # ========== 版本管理 ==========
    
    def update_version(
        self,
        capsule_id: str,
        version: str,
        changes: str = "",
        reason: str = "",
        author: str = "system",
        datm_score: Optional[Dict] = None,
        content_hash: str = ""
    ) -> CapsuleVersion:
        """更新版本"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 检查胶囊是否存在
        cursor.execute("SELECT current_version FROM provenance WHERE capsule_id = ?", (capsule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Capsule {capsule_id} not found")
        
        new_version = CapsuleVersion(
            version=version,
            changes=changes,
            reason=reason,
            author=author,
            datm_score=datm_score or {},
            hash=content_hash
        )
        
        # 插入新版本
        cursor.execute("""
            INSERT INTO versions 
            (capsule_id, version, changes, reason, author, datm_score, content_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            version,
            changes,
            reason,
            author,
            json.dumps(datm_score or {}),
            content_hash,
            new_version.timestamp.isoformat()
        ))
        
        # 更新主记录
        cursor.execute("""
            UPDATE provenance 
            SET current_version = ?, version_count = version_count + 1, updated_at = ?
            WHERE capsule_id = ?
        """, (version, datetime.utcnow().isoformat(), capsule_id))
        
        conn.commit()
        conn.close()
        
        return new_version
    
    def get_version_history(self, capsule_id: str) -> Optional[VersionHistory]:
        """获取版本历史"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT current_version, version_count FROM provenance 
            WHERE capsule_id = ?
        """, (capsule_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        history = VersionHistory(
            capsule_id=capsule_id,
            current_version=row[0],
            version_count=row[1]
        )
        
        cursor.execute("""
            SELECT version, changes, reason, author, datm_score, content_hash, timestamp
            FROM versions WHERE capsule_id = ? ORDER BY timestamp
        """, (capsule_id,))
        
        for v_row in cursor.fetchall():
            history.versions.append(CapsuleVersion(
                version=v_row[0],
                changes=v_row[1] or "",
                reason=v_row[2] or "",
                author=v_row[3] or "system",
                datm_score=json.loads(v_row[4]) if v_row[4] else {},
                hash=v_row[5] or ""
            ))
        
        conn.close()
        return history
    
    # ========== 演进关系 ==========
    
    def add_evolution(
        self,
        capsule_id: str,
        related_capsule_id: str,
        relation_type: str,
        strength: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> EvolutionRelation:
        """添加演进关系"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 验证关系类型
        try:
            rel_type = EvolutionType(relation_type)
        except ValueError:
            raise ValueError(f"Invalid relation type: {relation_type}")
        
        relation = EvolutionRelation(
            related_capsule_id=related_capsule_id,
            relation_type=rel_type,
            strength=strength,
            metadata=metadata or {}
        )
        
        cursor.execute("""
            INSERT INTO evolution 
            (capsule_id, related_capsule_id, relation_type, strength, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            related_capsule_id,
            relation_type,
            strength,
            json.dumps(metadata or {}),
            relation.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return relation
    
    def get_evolution(self, capsule_id: str) -> Optional[Evolution]:
        """获取演进关系"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT capsule_id FROM provenance WHERE capsule_id = ?", (capsule_id,))
        if not cursor.fetchone():
            conn.close()
            return None
        
        evolution = Evolution(capsule_id=capsule_id)
        
        cursor.execute("""
            SELECT related_capsule_id, relation_type, strength, metadata, timestamp
            FROM evolution WHERE capsule_id = ?
        """, (capsule_id,))
        
        for row in cursor.fetchall():
            try:
                rel_type = EvolutionType(row[1])
            except ValueError:
                rel_type = EvolutionType.BRANCH
            
            evolution.relations.append(EvolutionRelation(
                related_capsule_id=row[0],
                relation_type=rel_type,
                strength=row[2],
                metadata=json.loads(row[3]) if row[3] else {}
            ))
            
            # 更新关系列表
            if row[1] == "parent":
                evolution.parent_id = row[0]
            elif row[1] == "child":
                if row[0] not in evolution.child_ids:
                    evolution.child_ids.append(row[0])
            elif row[1] == "branch":
                if row[0] not in evolution.branches:
                    evolution.branches.append(row[0])
        
        conn.close()
        return evolution
    
    # ========== 验证记录 ==========
    
    def validate(
        self,
        capsule_id: str,
        validator: str,
        status: str = "pending",
        evidence: str = "",
        comments: str = "",
        score: Optional[float] = None
    ) -> Validation:
        """验证胶囊"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            val_status = ValidationStatus(status)
        except ValueError:
            val_status = ValidationStatus.PENDING
        
        validation = Validation(
            validator=validator,
            status=val_status,
            evidence=evidence,
            comments=comments,
            score=score
        )
        
        cursor.execute("""
            INSERT INTO validations 
            (capsule_id, validator, status, evidence, comments, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            validator,
            status,
            evidence,
            comments,
            score,
            validation.timestamp.isoformat()
        ))
        
        # 更新统计
        if status == "verified":
            cursor.execute("""
                UPDATE provenance SET verified_count = verified_count + 1, updated_at = ?
                WHERE capsule_id = ?
            """, (datetime.utcnow().isoformat(), capsule_id))
        elif status == "disputed":
            cursor.execute("""
                UPDATE provenance SET disputed_count = disputed_count + 1, updated_at = ?
                WHERE capsule_id = ?
            """, (datetime.utcnow().isoformat(), capsule_id))
        
        conn.commit()
        conn.close()
        
        return validation
    
    def get_validations(self, capsule_id: str) -> Optional[ValidationRecord]:
        """获取验证记录"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT capsule_id FROM provenance WHERE capsule_id = ?", (capsule_id,))
        if not cursor.fetchone():
            conn.close()
            return None
        
        record = ValidationRecord(capsule_id=capsule_id)
        
        cursor.execute("""
            SELECT validator, status, evidence, comments, score, timestamp
            FROM validations WHERE capsule_id = ? ORDER BY timestamp
        """, (capsule_id,))
        
        for row in cursor.fetchall():
            try:
                status = ValidationStatus(row[1])
            except ValueError:
                status = ValidationStatus.PENDING
            
            record.validations.append(Validation(
                validator=row[0],
                status=status,
                evidence=row[2] or "",
                comments=row[3] or "",
                score=row[4]
            ))
        
        conn.close()
        return record
    
    # ========== 引用计数 ==========
    
    def add_citation(
        self,
        source_capsule_id: str,
        target_capsule_id: str,
        context: str = "",
        strength: float = 1.0
    ) -> Citation:
        """添加引用"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        citation = Citation(
            source_capsule_id=source_capsule_id,
            target_capsule_id=target_capsule_id,
            context=context,
            strength=strength
        )
        
        cursor.execute("""
            INSERT INTO citations 
            (source_capsule_id, target_capsule_id, context, strength, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source_capsule_id,
            target_capsule_id,
            context,
            strength,
            citation.timestamp.isoformat()
        ))
        
        # 更新目标胶囊的引用计数
        cursor.execute("""
            UPDATE provenance SET citation_count = citation_count + 1, updated_at = ?
            WHERE capsule_id = ?
        """, (datetime.utcnow().isoformat(), target_capsule_id))
        
        conn.commit()
        conn.close()
        
        return citation
    
    def get_citations(self, capsule_id: str) -> Optional[Citations]:
        """获取引用信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT citation_count FROM provenance WHERE capsule_id = ?", (capsule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        citations = Citations(
            capsule_id=capsule_id,
            count=row[0]
        )
        
        cursor.execute("""
            SELECT source_capsule_id, target_capsule_id, context, strength, timestamp
            FROM citations WHERE target_capsule_id = ?
        """, (capsule_id,))
        
        for row in cursor.fetchall():
            citations.citations.append(Citation(
                source_capsule_id=row[0],
                target_capsule_id=row[1],
                context=row[2] or "",
                strength=row[3]
            ))
        
        conn.close()
        return citations
    
    # ========== 完整溯源查询 ==========
    
    def get_provenance(self, capsule_id: str) -> Optional[CapsuleProvenance]:
        """获取完整溯源信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM provenance WHERE capsule_id = ?", (capsule_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # 解析 source_data (安全处理)
        source_data = {}
        if row[5]:
            try:
                source_data = json.loads(row[5]) if isinstance(row[5], str) else row[5]
            except (json.JSONDecodeError, TypeError):
                source_data = {}
        
        provenance = CapsuleProvenance(
            capsule_id=capsule_id,
            source={
                "type": row[3],
                "id": row[4],
                "data": source_data
            },
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12])
        )
        
        # 获取版本历史
        provenance.version_history = self.get_version_history(capsule_id)
        
        # 获取演进关系
        provenance.evolution = self.get_evolution(capsule_id)
        
        # 获取验证记录
        provenance.validation = self.get_validations(capsule_id)
        
        # 获取引用信息
        provenance.citations = self.get_citations(capsule_id)
        
        conn.close()
        return provenance
    
    # ========== 知识图谱 ==========
    
    def get_evolution_graph(self, capsule_id: str, depth: int = 3) -> Dict:
        """获取演进图谱"""
        graph = {
            "nodes": [],
            "edges": []
        }
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        visited = set()
        queue = [(capsule_id, 0)]
        
        while queue and len(graph["nodes"]) < 100:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # 获取节点信息
            cursor.execute("""
                SELECT p.capsule_id, p.source_type, p.current_version, c.title
                FROM provenance p
                LEFT JOIN capsules c ON p.capsule_id = c.id
                WHERE p.capsule_id = ?
            """, (current_id,))
            
            row = cursor.fetchone()
            if row:
                graph["nodes"].append({
                    "id": current_id,
                    "type": row[1] or "unknown",
                    "version": row[2],
                    "depth": current_depth
                })
            
            # 获取关联边
            cursor.execute("""
                SELECT related_capsule_id, relation_type, strength
                FROM evolution WHERE capsule_id = ?
            """, (current_id,))
            
            for link_row in cursor.fetchall():
                related_id = link_row[0]
                
                graph["edges"].append({
                    "source": current_id,
                    "target": related_id,
                    "type": link_row[1],
                    "strength": link_row[2]
                })
                
                if related_id not in visited:
                    queue.append((related_id, current_depth + 1))
        
        conn.close()
        return graph
    
    def get_all_provenance_summary(self, limit: int = 100) -> List[Dict]:
        """获取所有溯源摘要"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT capsule_id, source_type, current_version, version_count, 
                   citation_count, verified_count, created_at
            FROM provenance ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "capsule_id": row[0],
                "source_type": row[1],
                "current_version": row[2],
                "version_count": row[3],
                "citation_count": row[4],
                "verified_count": row[5],
                "created_at": row[6]
            })
        
        conn.close()
        return results


# 单例实例
provenance_storage = ProvenanceStorage()
