"""
胶囊存储层 - SQLite 实现
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from .capsule import KnowledgeCapsule, CapsuleCreate
from .evaluator import datm_evaluator


class CapsuleStorage:
    """胶囊存储（SQLite + JSON 文件）"""
    
    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_dir / "capsules.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capsules (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT,
                metric_type TEXT,
                value REAL,
                created_at TEXT,
                FOREIGN KEY (capsule_id) REFERENCES capsules(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create(self, capsule_data: CapsuleCreate) -> KnowledgeCapsule:
        """创建胶囊"""
        import sqlite3
        
        # 构建胶囊对象
        capsule = KnowledgeCapsule(
            title=capsule_data.title,
            domain=capsule_data.domain,
            topics=capsule_data.topics,
            insight=capsule_data.insight,
            evidence=capsule_data.evidence,
            action_items=capsule_data.action_items,
            applicability=capsule_data.applicability,
            limitations=capsule_data.limitations,
            source_type=capsule_data.source_type,
            source_id=capsule_data.source_id,
            authors=capsule_data.authors,
            license=capsule_data.license,
            datm_score=datm_evaluator.evaluate(
                KnowledgeCapsule(
                    title=capsule_data.title,
                    domain=capsule_data.domain,
                    topics=capsule_data.topics,
                    insight=capsule_data.insight,
                    evidence=capsule_data.evidence,
                    action_items=capsule_data.action_items,
                    applicability=capsule_data.applicability,
                    limitations=capsule_data.limitations,
                    source_type=capsule_data.source_type,
                    source_id=capsule_data.source_id,
                    authors=capsule_data.authors,
                    license=capsule_data.license,
                    confidence=0.7  # 默认置信度
                )
            ),
            confidence=0.7  # 默认置信度
        )
        
        # 存储到数据库
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO capsules (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (capsule.id, capsule.model_dump_json(), capsule.created_at.isoformat(), capsule.updated_at.isoformat())
        )
        
        conn.commit()
        conn.close()
        
        return capsule
    
    def get(self, capsule_id: str) -> Optional[KnowledgeCapsule]:
        """获取胶囊"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM capsules WHERE id = ?", (capsule_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return KnowledgeCapsule.model_validate_json(row[0])
        return None
    
    def list(self, limit: int = 20, offset: int = 0) -> List[KnowledgeCapsule]:
        """列出胶囊"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data FROM capsules ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        
        capsules = []
        for row in cursor.fetchall():
            try:
                capsules.append(KnowledgeCapsule.model_validate_json(row[0]))
            except Exception:
                continue
        
        conn.close()
        return capsules
    
    def search(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        topics: Optional[List[str]] = None,
        min_score: Optional[float] = None,
        min_grade: Optional[str] = None,
        limit: int = 20
    ) -> List[KnowledgeCapsule]:
        """搜索胶囊"""
        from .capsule import KnowledgeCapsule
        
        capsules = self.list(limit=100)  # 先获取一批
        
        results = []
        for capsule in capsules:
            # 过滤：域名
            if domain and capsule.domain != domain:
                continue
            
            # 过滤：主题
            if topics:
                if not any(t in capsule.topics for t in topics):
                    continue
            
            # 过滤：最低分数
            if min_score and capsule.overall_score < min_score:
                continue
            
            # 过滤：最低评级
            grade_order = {"D": 0, "C": 1, "B": 2, "A": 3}
            if min_grade:
                if grade_order.get(capsule.overall_grade, 0) < grade_order.get(min_grade, 0):
                    continue
            
            # 过滤：搜索关键词（简单匹配）
            if query:
                q = query.lower()
                text = f"{capsule.title} {capsule.insight} {capsule.domain}".lower()
                if q not in text:
                    continue
            
            results.append(capsule)
        
        return results[:limit]
    
    def update_metrics(self, capsule_id: str, metric_type: str, value: float):
        """更新指标"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO metrics (capsule_id, metric_type, value, created_at) VALUES (?, ?, ?, ?)",
            (capsule_id, metric_type, value, datetime.utcnow().isoformat())
        )
        
        conn.commit()
        conn.close()


# 单例存储
storage = CapsuleStorage()
