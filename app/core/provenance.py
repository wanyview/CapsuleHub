"""
胶囊溯源系统 - 版本管理和溯源追踪
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from enum import Enum


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


class CapsuleVersion(BaseModel):
    """胶囊版本"""
    version: str = Field(..., description="版本号 (如: v1.0.0)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changes: str = Field(default="", description="变更说明")
    reason: str = Field(default="", description="变更原因")
    author: str = Field(default="system", description="作者")
    datm_score: Dict[str, float] = Field(default_factory=dict, description="DATM评分")


class CapsuleProvenance(BaseModel):
    """胶囊溯源信息"""
    capsule_id: str = Field(..., description="胶囊ID")
    
    # 溯源信息
    source: Dict[str, Any] = Field(
        default_factory=dict,
        description="来源信息"
    )
    
    # 版本历史
    versions: List[CapsuleVersion] = Field(
        default_factory=list,
        description="版本历史"
    )
    
    # 演进关系
    evolution: Dict[str, Any] = Field(
        default_factory=dict,
        description="演进关系"
    )
    
    # 验证记录
    validations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="验证记录"
    )
    
    # 引用计数
    citations: int = Field(default=0, description="被引用次数")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProvenanceStorage:
    """溯源存储"""
    
    def __init__(self, storage_dir: str = "./data"):
        from pathlib import Path
        import sqlite3
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_dir / "provenance.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 溯源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                id TEXT PRIMARY KEY,
                capsule_id TEXT NOT NULL UNIQUE,
                source_type TEXT,
                source_id TEXT,
                source_data TEXT,
                versions_data TEXT,
                evolution_data TEXT,
                validations_data TEXT,
                citations INTEGER DEFAULT 0,
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
                created_at TEXT,
                FOREIGN KEY (capsule_id) REFERENCES provenance(capsule_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_provenance(
        self,
        capsule_id: str,
        source_type: str = "manual",
        source_id: Optional[str] = None,
        source_data: Optional[Dict] = None
    ) -> CapsuleProvenance:
        """创建溯源记录"""
        import sqlite3
        
        provenance = CapsuleProvenance(
            capsule_id=capsule_id,
            source={
                "type": source_type,
                "id": source_id,
                "data": source_data or {}
            },
            versions=[CapsuleVersion(version="v1.0.0", changes="Initial version")],
            evolution={"parent_id": None, "child_ids": [], "branches": []}
        )
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO provenance 
            (id, capsule_id, source_type, source_id, source_data, versions_data, evolution_data, validations_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid4()),
            capsule_id,
            source_type,
            source_id,
            str(source_data or {}),
            provenance.versions[0].model_dump_json(),
            str(provenance.evolution),
            "[]",
            provenance.created_at.isoformat(),
            provenance.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return provenance
    
    def add_version(
        self,
        capsule_id: str,
        version: str,
        changes: str = "",
        reason: str = "",
        author: str = "system",
        datm_score: Optional[Dict] = None
    ) -> CapsuleVersion:
        """添加新版本"""
        import sqlite3
        
        new_version = CapsuleVersion(
            version=version,
            changes=changes,
            reason=reason,
            author=author,
            datm_score=datm_score or {}
        )
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO versions 
            (capsule_id, version, changes, reason, author, datm_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            capsule_id,
            version,
            changes,
            reason,
            author,
            str(datm_score or {}),
            new_version.timestamp.isoformat()
        ))
        
        # 更新 provenance 表中的版本数据
        cursor.execute("SELECT versions_data FROM provenance WHERE capsule_id = ?", (capsule_id,))
        row = cursor.fetchone()
        
        if row:
            from .capsule import KnowledgeCapsule
            # 获取当前版本列表
            cursor.execute("SELECT version, changes, reason, author, datm_score, timestamp FROM versions WHERE capsule_id = ? ORDER BY timestamp", (capsule_id,))
            versions = []
            for v_row in cursor.fetchall():
                versions.append({
                    "version": v_row[0],
                    "changes": v_row[1],
                    "reason": v_row[2],
                    "author": v_row[3],
                    "datm_score": eval(v_row[4]) if v_row[4] else {},
                    "timestamp": v_row[5]
                })
            
            # 更新 updated_at
            cursor.execute("UPDATE provenance SET updated_at = ? WHERE capsule_id = ?", 
                          (datetime.utcnow().isoformat(), capsule_id))
        
        conn.commit()
        conn.close()
        
        return new_version
    
    def link_capsules(
        self,
        capsule_id: str,
        related_capsule_id: str,
        relation_type: str,  # "parent", "child", "branch", "inspired_by", etc.
        strength: float = 1.0
    ):
        """建立胶囊关联"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evolution 
            (capsule_id, related_capsule_id, relation_type, strength, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            capsule_id,
            related_capsule_id,
            relation_type,
            strength,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_provenance(self, capsule_id: str) -> Optional[Dict]:
        """获取溯源信息"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 获取溯源记录
        cursor.execute("SELECT * FROM provenance WHERE capsule_id = ?", (capsule_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # 获取版本历史
        cursor.execute("""
            SELECT version, changes, reason, author, datm_score, timestamp 
            FROM versions WHERE capsule_id = ? ORDER BY timestamp
        """, (capsule_id,))
        
        versions = []
        for v_row in cursor.fetchall():
            versions.append({
                "version": v_row[0],
                "changes": v_row[1],
                "reason": v_row[2],
                "author": v_row[3],
                "datm_score": eval(v_row[4]) if v_row[4] else {},
                "timestamp": v_row[5]
            })
        
        # 获取关联
        cursor.execute("""
            SELECT related_capsule_id, relation_type, strength FROM evolution 
            WHERE capsule_id = ?
        """, (capsule_id,))
        
        links = []
        for l_row in cursor.fetchall():
            links.append({
                "related_id": l_row[0],
                "type": l_row[1],
                "strength": l_row[2]
            })
        
        conn.close()
        
        return {
            "capsule_id": capsule_id,
            "source": eval(row[4]) if row[4] else {},
            "versions": versions,
            "evolution": {
                "links": links,
                "parent_id": None,
                "child_ids": [l[0] for l in links if l[1] == "parent"]
            },
            "validations": eval(row[8]) if row[8] else [],
            "citations": row[9],
            "created_at": row[10],
            "updated_at": row[11]
        }
    
    def increment_citations(self, capsule_id: str):
        """增加引用计数"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("UPDATE provenance SET citations = citations + 1 WHERE capsule_id = ?", (capsule_id,))
        
        conn.commit()
        conn.close()
    
    def get_evolution_graph(self, capsule_id: str, depth: int = 3) -> Dict:
        """获取演进图谱"""
        import sqlite3
        
        graph = {
            "nodes": [],
            "edges": []
        }
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 广度优先遍历获取关联胶囊
        visited = set()
        queue = [(capsule_id, 0)]
        
        while queue and len(graph["nodes"]) < 50:  # 限制节点数
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            # 获取当前胶囊信息
            cursor.execute("SELECT id, source_type FROM provenance WHERE capsule_id = ?", (current_id,))
            row = cursor.fetchone()
            
            if row:
                graph["nodes"].append({
                    "id": current_id,
                    "type": row[1] or "unknown",
                    "depth": current_depth
                })
            
            # 获取关联
            cursor.execute("""
                SELECT related_capsule_id, relation_type FROM evolution 
                WHERE capsule_id = ?
            """, (current_id,))
            
            for link_row in cursor.fetchall():
                related_id = link_row[0]
                relation = link_row[1]
                
                graph["edges"].append({
                    "source": current_id,
                    "target": related_id,
                    "type": relation
                })
                
                if related_id not in visited:
                    queue.append((related_id, current_depth + 1))
        
        conn.close()
        
        return graph


# 单例实例
provenance_storage = ProvenanceStorage()
