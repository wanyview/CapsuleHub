"""
胶囊存储层 - SQLite 实现
"""
import json
import os
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from .capsule import KnowledgeCapsule, CapsuleCreate, DATMScore
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
        
        # 精选胶囊表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS featured_capsules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capsule_id TEXT NOT NULL,
                featured_date TEXT NOT NULL,
                reason TEXT,
                created_at TEXT,
                UNIQUE(capsule_id, featured_date),
                FOREIGN KEY (capsule_id) REFERENCES capsules(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create(self, capsule_data: CapsuleCreate) -> KnowledgeCapsule:
        """创建胶囊"""
        import sqlite3
        
        # 获取 datm_score 和 confidence（如果存在）
        datm = getattr(capsule_data, 'datm_score', None)
        conf = getattr(capsule_data, 'confidence', 0.7)
        
        if datm and isinstance(datm, dict):
            datm_score = DATMScore(**datm)
        else:
            datm_score = DATMScore(truth=75, goodness=75, beauty=75, intelligence=75)
        
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
            capsule_type=getattr(capsule_data, 'capsule_type', 'general'),
            datm_score=datm_score,
            confidence=conf
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
    
    def get_todays_featured(self) -> Optional[KnowledgeCapsule]:
        """获取今日精选胶囊"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 先检查是否有今日精选
        cursor.execute("""
            SELECT c.data FROM capsules c
            JOIN featured_capsules f ON c.id = f.capsule_id
            WHERE f.featured_date = ?
            ORDER BY f.created_at DESC LIMIT 1
        """, (today,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return KnowledgeCapsule.model_validate_json(row[0])
        
        return None
    
    def get_yesterdays_featured(self) -> Optional[KnowledgeCapsule]:
        """获取昨日精选胶囊"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.data FROM capsules c
            JOIN featured_capsules f ON c.id = f.capsule_id
            WHERE f.featured_date = ?
            ORDER BY f.created_at DESC LIMIT 1
        """, (yesterday,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return KnowledgeCapsule.model_validate_json(row[0])
        
        return None
    
    def auto_select_featured(self, date: Optional[str] = None) -> Optional[KnowledgeCapsule]:
        """自动选择今日/指定日期的精选胶囊（基于评分 + 随机）"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        target_date = date or datetime.utcnow().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 获取所有胶囊，按评分排序
        cursor.execute("""
            SELECT data, overall_score FROM capsules
            ORDER BY overall_score DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # 策略：选择 Top 3 中随机一个，避免总是同样的
        top_candidates = rows[:3]
        selected = random.choice(top_candidates)
        
        capsule = KnowledgeCapsule.model_validate_json(selected[0])
        
        # 设置为精选
        self.set_featured(capsule.id, target_date, reason="自动选择 - 高评分")
        
        return capsule
    
    def set_featured(self, capsule_id: str, date: str, reason: str = ""):
        """手动设置精选胶囊"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 使用 REPLACE 实现 upsert
        cursor.execute("""
            INSERT OR REPLACE INTO featured_capsules (capsule_id, featured_date, reason, created_at)
            VALUES (?, ?, ?, ?)
        """, (capsule_id, date, reason, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_featured_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取精选历史"""
        import sqlite3
        
        history = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            capsule = self.get_featured_by_date(date)
            if capsule:
                history.append({
                    "date": date,
                    "capsule": capsule,
                    "grade": capsule.overall_grade,
                    "score": capsule.overall_score
                })
        
        return history
    
    def get_featured_by_date(self, date: str) -> Optional[KnowledgeCapsule]:
        """获取指定日期的精选胶囊"""
        import sqlite3
        from .capsule import KnowledgeCapsule
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.data FROM capsules c
            JOIN featured_capsules f ON c.id = f.capsule_id
            WHERE f.featured_date = ?
            LIMIT 1
        """, (date,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return KnowledgeCapsule.model_validate_json(row[0])
        return None
    
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
    
    def get_trending(self, days: int = 7, limit: int = 10) -> List[KnowledgeCapsule]:
        """获取近期热门胶囊（基于创建时间和评分）"""
        from .capsule import KnowledgeCapsule
        
        # 获取最近创建的胶囊
        capsules = self.list(limit=50)
        
        # 按评分排序
        sorted_capsules = sorted(capsules, key=lambda x: x.overall_score, reverse=True)
        
        return sorted_capsules[:limit]
    
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
    
    def update(self, capsule_id: str, capsule: KnowledgeCapsule) -> bool:
        """更新胶囊"""
        import sqlite3
        
        # 更新 updated_at
        capsule.updated_at = datetime.utcnow()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE capsules SET data = ?, updated_at = ? WHERE id = ?",
            (capsule.model_dump_json(), capsule.updated_at.isoformat(), capsule_id)
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete(self, capsule_id: str) -> bool:
        """删除胶囊"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM capsules WHERE id = ?", (capsule_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0


# 单例存储
storage = CapsuleStorage()
