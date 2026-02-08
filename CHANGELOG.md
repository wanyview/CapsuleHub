# Changelog - CapsuleHub v0.3.0

## [v0.3.0] - 2026-02-08

### 🔗 胶囊溯源系统 (Provenance System)

**核心功能：**
- 版本历史管理 (`versions`)
- 演进关系追踪 (`evolution`)
- 引用计数系统 (`citations`)
- 知识图谱接口 (`graph`)
- 验证记录管理 (`validations`)

**API 新增：**
- `POST /api/v1/provenance/register` - 注册溯源
- `GET /api/v1/provenance/{capsule_id}` - 获取溯源
- `POST /api/v1/provenance/{capsule_id}/version` - 添加版本
- `GET /api/v1/provenance/{capsule_id}/versions` - 获取版本历史
- `POST /api/v1/provenance/{capsule_id}/evolve` - 建立演进关系
- `GET /api/v1/provenance/{capsule_id}/evolution` - 获取演进图谱
- `POST /api/v1/provenance/cite` - 引用胶囊
- `GET /api/v1/provenance/{capsule_id}/citations` - 获取引用计数
- `POST /api/v1/provenance/{capsule_id}/validate` - 记录验证
- `GET /api/v1/provenance/{capsule_id}/validations` - 获取验证记录
- `GET /api/v1/provenance/graph` - 获取知识图谱
- `GET /api/v1/provenance/graph/overview` - 图谱概览

**数据模型：**
- `CapsuleVersion` - 胶囊版本
- `VersionHistory` - 版本历史
- `EvolutionRelation` - 演进关系
- `ValidationRecord` - 验证记录

### 📦 其他改进
- SQLite 持久化存储
- 精选胶囊自动选择
- DATM 质量评估

## [v0.2.0] - 2026-01-30
- 今日/昨日精选功能
- 精选历史记录
- 热门胶囊推荐

## [v0.1.0] - 2026-01-29
- 知识胶囊基础 CRUD
- DATM 评分系统
- 搜索和筛选
- 域名/主题分类
