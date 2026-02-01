"""
Knowledge Capsule Hub - 核心数据结构
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import uuid4


class DATMScore(BaseModel):
    """DATM 质量评分"""
    truth: float = Field(..., ge=0, le=100, description="真理性 - 事实准确性")
    goodness: float = Field(..., ge=0, le=100, description="良善性 - 价值导向")
    beauty: float = Field(..., ge=0, le=100, description="美感 - 表达优雅")
    intelligence: float = Field(..., ge=0, le=100, description="智能性 - 洞察深度")
    
    @property
    def average(self) -> float:
        return (self.truth + self.goodness + self.beauty + self.intelligence) / 4


class KnowledgeCapsule(BaseModel):
    """知识胶囊 - 核心数据结构"""
    
    # ========== 核心标识 ==========
    id: str = Field(default_factory=lambda: str(uuid4()), description="唯一标识")
    title: str = Field(..., min_length=1, max_length=200, description="胶囊标题")
    
    # ========== 分类元数据 ==========
    domain: str = Field(..., description="学科领域 (physics/AI/biology...)")
    topics: List[str] = Field(default_factory=list, description="主题标签")
    
    # ========== 胶囊类型 (2026-01-31 新增) ==========
    capsule_type: str = Field(
        default="general",
        description="胶囊类型: general/discussion/historical_replication/fusion/breakthrough"
    )
    
    # ========== 核心内容 ==========
    insight: str = Field(..., description="核心洞见（一句话总结）")
    evidence: List[str] = Field(..., min_items=1, description="支撑证据（3-5条）")
    action_items: List[str] = Field(default_factory=list, description="可执行建议")
    
    # ========== 质量评估 ==========
    datm_score: DATMScore = Field(..., description="DATM 评分")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    
    @property
    def overall_score(self) -> float:
        """综合评分 = DATM均值 × 置信度"""
        return self.datm_score.average * self.confidence
    
    @property
    def overall_grade(self) -> str:
        """评级：A(≥80) B(60-79) C(40-59) D(<40)"""
        score = self.overall_score
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"
    
    # ========== 价值属性 ==========
    applicability: str = Field(default="", description="适用场景")
    limitations: List[str] = Field(default_factory=list, description="已知局限性")
    reproducibility: float = Field(default=0.5, ge=0, le=1, description="可复现度")
    impact_potential: float = Field(default=0.5, ge=0, le=1, description="影响力潜力")
    
    # ========== 溯源元数据 ==========
    source_type: str = Field(default="discussion", description="来源类型 (discussion/agent/manual)")
    source_id: Optional[str] = Field(None, description="来源ID")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    license: str = Field(default="MIT", description="许可证")
    
    # ========== 时间戳 ==========
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0", description="胶囊版本")
    
    # ========== 价值追踪 ==========
    citations: int = Field(default=0, description="被引用次数")
    use_cases: List[str] = Field(default_factory=list, description="应用案例")
    validations: int = Field(default=0, description="验证次数")
    impact_score: float = Field(default=0.0, ge=0, le=100, description="实际影响力评分")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CapsuleCreate(BaseModel):
    """创建胶囊的请求结构"""
    title: str
    domain: str
    topics: List[str] = []
    capsule_type: str = "general"  # 2026-01-31 新增
    insight: str
    evidence: List[str]
    action_items: List[str] = []
    applicability: str = ""
    limitations: List[str] = []
    source_type: str = "manual"
    source_id: Optional[str] = None
    authors: List[str] = []
    license: str = "MIT"


class CapsuleSearch(BaseModel):
    """搜索请求结构"""
    query: Optional[str] = None
    domain: Optional[str] = None
    topics: List[str] = []
    min_score: Optional[float] = None
    min_grade: Optional[str] = None  # A/B/C/D
    limit: int = 20
    offset: int = 0


# ============ 历史复现胶囊扩展 (2026-01-31 新增) ============

class OriginalExperiment(BaseModel):
    """原始实验"""
    researcher: str = Field(..., description="原始研究者")
    year: int = Field(..., description="实验年份")
    description: str = Field(..., description="实验描述")
    original_goal: str = Field(..., description="原始目的")
    methods: List[str] = Field(default_factory=list, description="实验方法")
    findings: List[str] = Field(default_factory=list, description="原始发现")


class ReplicationExperiment(BaseModel):
    """复现实验"""
    researcher: str = Field(..., description="复现研究者")
    year: int = Field(..., description="复现年份")
    replication_details: str = Field(..., description="复现过程")
    deviations: List[str] = Field(default_factory=list, description="与原实验的差异")
    modern_tools: List[str] = Field(default_factory=list, description="现代工具")


class NewDiscovery(BaseModel):
    """新发现"""
    phenomena: List[str] = Field(default_factory=list, description="新现象")
    mechanism: str = Field(default="", description="新机制解释")
    implications: List[str] = Field(default_factory=list, description="意义")
    applications: List[str] = Field(default_factory=list, description="潜在应用")


class Connection(BaseModel):
    """连接分析"""
    temporal_span: int = Field(..., description="时间跨度（年）")
    domain_bridge: str = Field(..., description="领域桥梁")
    paradigm_shift: str = Field(default="", description="范式转变")
    knowledge_gap: str = Field(default="", description="为何原始研究者未发现")


class HistoricalReplicationCapsule(BaseModel):
    """历史复现知识胶囊扩展数据"""
    original_experiment: OriginalExperiment
    replication_experiment: ReplicationExperiment
    new_discovery: NewDiscovery
    connection: Connection
