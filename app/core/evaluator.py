"""
DATM 质量评估器
Truth / Goodness / Beauty / Intelligence
"""
from typing import Dict, Any
from .capsule import KnowledgeCapsule, DATMScore


class DATMEvaluator:
    """DATM 质量评估器"""
    
    # 评估维度权重
    WEIGHTS = {
        "truth": 0.35,
        "goodness": 0.20,
        "beauty": 0.15,
        "intelligence": 0.30
    }
    
    def evaluate(self, capsule: KnowledgeCapsule) -> DATMScore:
        """
        评估胶囊的 DATM 分数
        
        目前是规则基础评估，未来可以：
        - 集成 AI 评估
        - 引入社区投票
        - 关联外部验证
        """
        return DATMScore(
            truth=self._evaluate_truth(capsule),
            goodness=self._evaluate_goodness(capsule),
            beauty=self._evaluate_beauty(capsule),
            intelligence=self._evaluate_intelligence(capsule)
        )
    
    def _evaluate_truth(self, capsule: KnowledgeCapsule) -> float:
        """评估真理性"""
        score = 70.0  # 基础分
        
        # 证据越多，真理性越高
        evidence_count = len(capsule.evidence)
        if evidence_count >= 5:
            score += 15
        elif evidence_count >= 3:
            score += 10
        elif evidence_count >= 1:
            score += 5
        
        # 有明确局限性加分（承认局限是真科学的态度）
        if len(capsule.limitations) > 0:
            score += 5
        
        # 来源可靠加分
        if capsule.source_type in ["discussion", "agent"]:
            score += 5
        
        # 置信度影响
        confidence_boost = capsule.confidence * 10
        score = min(100, score + confidence_boost * 0.2)
        
        return round(score, 1)
    
    def _evaluate_goodness(self, capsule: KnowledgeCapsule) -> float:
        """评估良善性"""
        score = 70.0  # 基础分
        
        # 有行动建议加分（知识要能指导行动）
        if len(capsule.action_items) >= 3:
            score += 15
        elif len(capsule.action_items) >= 1:
            score += 10
        
        # 适用场景明确加分
        if capsule.applicability:
            score += 10
        
        # 作者/贡献者数量（协作加分）
        if len(capsule.authors) >= 3:
            score += 5
        
        return min(100, round(score, 1))
    
    def _evaluate_beauty(self, capsule: KnowledgeCapsule) -> float:
        """评估美感"""
        score = 70.0  # 基础分
        
        # 标题简洁性
        title_length = len(capsule.title)
        if 10 <= title_length <= 80:
            score += 10
        elif title_length > 100:
            score -= 5
        
        # 洞见清晰度（长度适中）
        insight_length = len(capsule.insight)
        if 20 <= insight_length <= 200:
            score += 10
        elif insight_length > 300:
            score -= 5
        
        # 结构完整
        if capsule.domain and capsule.topics:
            score += 10
        
        return min(100, round(score, 1))
    
    def _evaluate_intelligence(self, capsule: KnowledgeCapsule) -> float:
        """评估智能性（洞察深度）"""
        score = 70.0  # 基础分
        
        # 主题标签数量（跨领域加分）
        if len(capsule.topics) >= 3:
            score += 10
        elif len(capsule.topics) >= 1:
            score += 5
        
        # 有影响力潜力评估
        if capsule.impact_potential >= 0.7:
            score += 10
        elif capsule.impact_potential >= 0.5:
            score += 5
        
        # 可复现性高加分
        if capsule.reproducibility >= 0.8:
            score += 5
        
        # 版本迭代（不是 v1.0.0 意味着经过改进）
        if capsule.version != "1.0.0":
            score += 5
        
        return min(100, round(score, 1))
    
    def get_score_breakdown(self, capsule: KnowledgeCapsule) -> Dict[str, Any]:
        """获取详细评分分解"""
        score = self.evaluate(capsule)
        return {
            "truth": {
                "score": score.truth,
                "weight": self.WEIGHTS["truth"],
                "weighted": score.truth * self.WEIGHTS["truth"]
            },
            "goodness": {
                "score": score.goodness,
                "weight": self.WEIGHTS["goodness"],
                "weighted": score.goodness * self.WEIGHTS["goodness"]
            },
            "beauty": {
                "score": score.beauty,
                "weight": self.WEIGHTS["beauty"],
                "weighted": score.beauty * self.WEIGHTS["beauty"]
            },
            "intelligence": {
                "score": score.intelligence,
                "weight": self.WEIGHTS["intelligence"],
                "weighted": score.intelligence * self.WEIGHTS["intelligence"]
            },
            "confidence": capsule.confidence,
            "overall": capsule.overall_score,
            "grade": capsule.overall_grade
        }


# 单例实例
datm_evaluator = DATMEvaluator()
