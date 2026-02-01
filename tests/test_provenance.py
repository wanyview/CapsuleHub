"""
胶囊溯源系统测试 v0.3.0
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProvenanceModels:
    """测试溯源数据模型"""
    
    def test_capsule_version(self):
        """测试胶囊版本模型"""
        from app.core.provenance import CapsuleVersion
        
        version = CapsuleVersion(
            version="v1.0.0",
            changes="Initial version",
            reason="Creation",
            author="test_user",
            datm_score={"truth": 85, "goodness": 80, "beauty": 75, "intelligence": 90}
        )
        
        assert version.version == "v1.0.0"
        assert version.changes == "Initial version"
        assert version.author == "test_user"
        assert version.datm_score["truth"] == 85
    
    def test_version_history(self):
        """测试版本历史"""
        from app.core.provenance import VersionHistory
        
        history = VersionHistory(capsule_id="test-capsule-1")
        assert history.capsule_id == "test-capsule-1"
        assert history.version_count == 0
        assert len(history.versions) == 0
        
        # 添加版本
        from app.core.provenance import CapsuleVersion
        v1 = CapsuleVersion(version="v1.0.0", changes="Initial")
        history.add_version(v1)
        
        assert history.version_count == 1
        assert history.current_version == "v1.0.0"
        assert history.get_version("v1.0.0") == v1
        assert history.get_latest() == v1
    
    def test_evolution_relation(self):
        """测试演进关系"""
        from app.core.provenance import EvolutionRelation, EvolutionType
        
        relation = EvolutionRelation(
            related_capsule_id="capsule-2",
            relation_type=EvolutionType.PARENT,
            strength=0.8
        )
        
        assert relation.related_capsule_id == "capsule-2"
        assert relation.relation_type == EvolutionType.PARENT
        assert relation.strength == 0.8
    
    def test_evolution(self):
        """测试演进管理"""
        from app.core.provenance import Evolution, EvolutionRelation, EvolutionType
        
        evolution = Evolution(capsule_id="capsule-1")
        assert evolution.capsule_id == "capsule-1"
        assert evolution.parent_id is None
        
        # 添加子胶囊关系
        relation = EvolutionRelation(
            related_capsule_id="capsule-2",
            relation_type=EvolutionType.CHILD,
            strength=1.0
        )
        evolution.add_relation(relation)
        
        assert "capsule-2" in evolution.child_ids
        assert len(evolution.relations) == 1
    
    def test_validation(self):
        """测试验证记录"""
        from app.core.provenance import Validation, ValidationStatus
        
        validation = Validation(
            validator="expert_user",
            status=ValidationStatus.VERIFIED,
            evidence="Supporting evidence",
            score=95
        )
        
        assert validation.validator == "expert_user"
        assert validation.status == ValidationStatus.VERIFIED
        assert validation.score == 95
    
    def test_validation_record(self):
        """测试验证记录管理"""
        from app.core.provenance import ValidationRecord, Validation, ValidationStatus
        
        record = ValidationRecord(capsule_id="capsule-1")
        assert record.capsule_id == "capsule-1"
        assert record.get_verified_count() == 0
        
        # 添加验证
        v1 = Validation(validator="user1", status=ValidationStatus.VERIFIED)
        v2 = Validation(validator="user2", status=ValidationStatus.PENDING)
        record.add_validation(v1)
        record.add_validation(v2)
        
        assert record.get_verified_count() == 1
        assert record.get_disputed_count() == 0
        assert record.is_verified() == True
    
    def test_citations(self):
        """测试引用计数"""
        from app.core.provenance import Citations, Citation
        
        citations = Citations(capsule_id="capsule-1")
        assert citations.count == 0
        
        # 添加引用
        c1 = Citation(source_capsule_id="capsule-2", context="Using this insight")
        citations.add_citation(c1)
        
        assert citations.count == 1
        assert "capsule-2" in citations.get_citing_capsules()
    
    def test_capsule_provenance(self):
        """测试完整溯源模型"""
        from app.core.provenance import (
            CapsuleProvenance, VersionHistory, Evolution, 
            ValidationRecord, Citations, CapsuleVersion
        )
        
        provenance = CapsuleProvenance(
            capsule_id="test-capsule",
            source={"type": "discussion", "id": "disc-123"}
        )
        
        assert provenance.capsule_id == "test-capsule"
        assert provenance.source["type"] == "discussion"
        
        # 测试转换为字典
        data = provenance.to_dict()
        assert data["capsule_id"] == "test-capsule"
        assert "version_history" in data
        assert "evolution" in data
        assert "citations" in data


class TestProvenanceStorage:
    """测试溯源存储"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """创建临时存储"""
        from app.core.provenance import ProvenanceStorage
        storage = ProvenanceStorage(storage_dir=str(tmp_path))
        yield storage
    
    def test_register_capsule(self, temp_storage):
        """测试胶囊注册"""
        provenance = temp_storage.register_capsule(
            capsule_id="test-capsule-001",
            source_type="manual",
            source_id="user-123",
            author="test_user"
        )
        
        assert provenance is not None
        assert provenance.capsule_id == "test-capsule-001"
        assert provenance.source["type"] == "manual"
    
    def test_register_duplicate(self, temp_storage):
        """测试重复注册"""
        temp_storage.register_capsule(capsule_id="dup-capsule")
        
        with pytest.raises(ValueError):
            temp_storage.register_capsule(capsule_id="dup-capsule")
    
    def test_update_version(self, temp_storage):
        """测试版本更新"""
        # 先注册
        temp_storage.register_capsule(capsule_id="version-test")
        
        # 更新版本
        new_version = temp_storage.update_version(
            capsule_id="version-test",
            version="v2.0.0",
            changes="Major update",
            reason="New findings",
            author="researcher",
            datm_score={"truth": 90, "goodness": 85, "beauty": 80, "intelligence": 95}
        )
        
        assert new_version.version == "v2.0.0"
        assert new_version.changes == "Major update"
    
    def test_get_version_history(self, temp_storage):
        """测试获取版本历史"""
        temp_storage.register_capsule(capsule_id="history-test")
        temp_storage.update_version(capsule_id="history-test", version="v1.1.0", changes="Patch")
        temp_storage.update_version(capsule_id="history-test", version="v2.0.0", changes="Major")
        
        history = temp_storage.get_version_history("history-test")
        
        assert history is not None
        assert history.version_count == 3  # 初始 + 2次更新
        assert history.current_version == "v2.0.0"
        assert len(history.versions) == 3
    
    def test_add_evolution(self, temp_storage):
        """测试添加演进关系"""
        temp_storage.register_capsule(capsule_id="parent-capsule")
        temp_storage.register_capsule(capsule_id="child-capsule")
        
        relation = temp_storage.add_evolution(
            capsule_id="parent-capsule",
            related_capsule_id="child-capsule",
            relation_type="child",
            strength=0.9
        )
        
        assert relation.related_capsule_id == "child-capsule"
        assert relation.relation_type.value == "child"
    
    def test_get_evolution(self, temp_storage):
        """测试获取演进关系"""
        temp_storage.register_capsule(capsule_id="evo-test-1")
        temp_storage.register_capsule(capsule_id="evo-test-2")
        temp_storage.register_capsule(capsule_id="evo-test-3")
        
        temp_storage.add_evolution("evo-test-1", "evo-test-2", "child")
        temp_storage.add_evolution("evo-test-1", "evo-test-3", "branch")
        
        evolution = temp_storage.get_evolution("evo-test-1")
        
        assert evolution is not None
        assert "evo-test-2" in evolution.child_ids
        assert "evo-test-3" in evolution.branches
    
    def test_validate(self, temp_storage):
        """测试验证胶囊"""
        temp_storage.register_capsule(capsule_id="validate-test")
        
        validation = temp_storage.validate(
            capsule_id="validate-test",
            validator="reviewer-1",
            status="verified",
            evidence="Evidence provided",
            score=92
        )
        
        assert validation.validator == "reviewer-1"
        assert validation.status.value == "verified"
    
    def test_get_validations(self, temp_storage):
        """测试获取验证记录"""
        temp_storage.register_capsule(capsule_id="validations-test")
        temp_storage.validate("validations-test", "v1", "verified")
        temp_storage.validate("validations-test", "v2", "pending")
        
        record = temp_storage.get_validations("validations-test")
        
        assert record is not None
        assert record.get_verified_count() == 1
        assert record.get_disputed_count() == 0
    
    def test_add_citation(self, temp_storage):
        """测试添加引用"""
        temp_storage.register_capsule(capsule_id="source-capsule")
        temp_storage.register_capsule(capsule_id="target-capsule")
        
        citation = temp_storage.add_citation(
            source_capsule_id="source-capsule",
            target_capsule_id="target-capsule",
            context="Using the insight",
            strength=0.8
        )
        
        assert citation.source_capsule_id == "source-capsule"
        assert citation.strength == 0.8
    
    def test_get_citations(self, temp_storage):
        """测试获取引用"""
        temp_storage.register_capsule(capsule_id="cite-target")
        temp_storage.register_capsule(capsule_id="cite-source-1")
        temp_storage.register_capsule(capsule_id="cite-source-2")
        
        temp_storage.add_citation("cite-source-1", "cite-target")
        temp_storage.add_citation("cite-source-2", "cite-target")
        
        citations = temp_storage.get_citations("cite-target")
        
        assert citations is not None
        assert citations.count == 2
        assert len(citations.citations) == 2
    
    def test_get_provenance(self, temp_storage):
        """测试获取完整溯源"""
        temp_storage.register_capsule(capsule_id="full-test")
        temp_storage.update_version("full-test", version="v1.1.0", changes="Update")
        temp_storage.validate("full-test", "validator", "verified")
        
        provenance = temp_storage.get_provenance("full-test")
        
        assert provenance is not None
        assert provenance.capsule_id == "full-test"
        assert provenance.version_history.version_count == 2
        assert provenance.validation.get_verified_count() == 1
    
    def test_get_evolution_graph(self, temp_storage):
        """测试获取演进图谱"""
        # 创建链式结构
        for i in range(5):
            temp_storage.register_capsule(capsule_id=f"graph-test-{i}")
        
        for i in range(4):
            temp_storage.add_evolution(
                f"graph-test-{i}",
                f"graph-test-{i+1}",
                "child"
            )
        
        graph = temp_storage.get_evolution_graph("graph-test-0", depth=3)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0
    
    def test_not_found(self, temp_storage):
        """测试不存在的胶囊"""
        provenance = temp_storage.get_provenance("non-existent")
        assert provenance is None
        
        history = temp_storage.get_version_history("non-existent")
        assert history is None


class TestProvenanceAPI:
    """测试溯源 API"""
    
    @pytest.fixture
    def mock_storage(self):
        """模拟存储"""
        storage = MagicMock()
        storage.get.return_value = MagicMock(
            id="test-capsule",
            title="Test Capsule",
            domain="physics",
            overall_score=85,
            overall_grade="A",
            citations=5,
            version="1.0.0"
        )
        return storage
    
    def test_register_request_model(self):
        """测试注册请求模型"""
        from app.api.provenance_v2 import RegisterRequest
        
        request = RegisterRequest(
            capsule_id="test-123",
            source_type="discussion",
            initial_version="v1.0.0"
        )
        
        assert request.capsule_id == "test-123"
        assert request.source_type == "discussion"
    
    def test_evolution_request_model(self):
        """测试演进请求模型"""
        from app.api.provenance_v2 import EvolutionRequest
        
        request = EvolutionRequest(
            related_capsule_id="target-123",
            relation_type="child",
            strength=0.8
        )
        
        assert request.related_capsule_id == "target-123"
        assert request.relation_type == "child"
    
    def test_citation_request_model(self):
        """测试引用请求模型"""
        from app.api.provenance_v2 import CitationRequest
        
        request = CitationRequest(
            source_capsule_id="source-123",
            context="Using this insight",
            strength=0.9
        )
        
        assert request.source_capsule_id == "source-123"
        assert request.strength == 0.9


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def setup_capsules(self, tmp_path):
        """设置测试胶囊"""
        from app.core.provenance import ProvenanceStorage
        from app.core.storage import CapsuleStorage
        from app.core.capsule import CapsuleCreate
        
        prov_storage = ProvenanceStorage(storage_dir=str(tmp_path))
        capsule_storage = CapsuleStorage(storage_dir=str(tmp_path))
        
        # 创建测试胶囊
        create_data = CapsuleCreate(
            title="Integration Test Capsule",
            domain="physics",
            topics=["test"],
            insight="Test insight",
            evidence=["Evidence 1", "Evidence 2"]
        )
        capsule = capsule_storage.create(create_data)
        
        return capsule.id, prov_storage, capsule_storage
    
    def test_full_workflow(self, setup_capsules, tmp_path):
        """测试完整工作流"""
        capsule_id, prov_storage, capsule_storage = setup_capsules
        
        # 1. 注册溯源
        provenance = prov_storage.register_capsule(
            capsule_id=capsule_id,
            source_type="test",
            author="test_user"
        )
        assert provenance is not None
        
        # 2. 更新版本
        prov_storage.update_version(
            capsule_id=capsule_id,
            version="v2.0.0",
            changes="Integration test update",
            author="test_user"
        )
        
        # 3. 验证
        prov_storage.validate(
            capsule_id=capsule_id,
            validator="test_reviewer",
            status="verified",
            score=90
        )
        
        # 4. 获取完整溯源
        full_prov = prov_storage.get_provenance(capsule_id)
        assert full_prov is not None
        assert full_prov.version_history.current_version == "v2.0.0"
        assert full_prov.validation.is_verified()
        
        # 5. 获取演进图谱
        graph = prov_storage.get_evolution_graph(capsule_id)
        assert "nodes" in graph
        assert len(graph["nodes"]) == 1  # 只有自己


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
