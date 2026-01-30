# Knowledge Capsule Hub - API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs`

## 胶囊 API

### 列出胶囊

```http
GET /api/capsules/?limit=20&offset=0
```

**参数:**
- `limit` (int): 返回数量，默认 20
- `offset` (int): 偏移量，默认 0

**响应:**
```json
{
  "capsules": [
    {
      "id": "uuid",
      "title": "胶囊标题",
      "domain": "physics",
      "topics": ["quantum", "entanglement"],
      "insight": "核心洞见...",
      "evidence": ["证据1", "证据2"],
      "action_items": ["建议1"],
      "datm_score": {
        "truth": 85.0,
        "goodness": 80.0,
        "beauty": 75.0,
        "intelligence": 90.0
      },
      "confidence": 0.85,
      "overall_score": 72.25,
      "overall_grade": "A",
      "applicability": "量子计算研究",
      "limitations": [],
      "reproducibility": 0.8,
      "impact_potential": 0.9,
      "source_type": "discussion",
      "authors": ["牛顿", "爱因斯坦"],
      "license": "MIT",
      "version": "1.0.0",
      "created_at": "2026-01-30T12:00:00",
      "updated_at": "2026-01-30T12:00:00",
      "citations": 0,
      "use_cases": [],
      "validations": 0,
      "impact_score": 0.0
    }
  ],
  "total": 1
}
```

### 获取单个胶囊

```http
GET /api/capsules/{id}
```

**响应:**
```json
{
  "capsule": { ... },
  "score_breakdown": {
    "truth": {"score": 85.0, "weight": 0.35, "weighted": 29.75},
    "goodness": {"score": 80.0, "weight": 0.20, "weighted": 16.0},
    "beauty": {"score": 75.0, "weight": 0.15, "weighted": 11.25},
    "intelligence": {"score": 90.0, "weight": 0.30, "weighted": 27.0},
    "confidence": 0.85,
    "overall": 72.25,
    "grade": "A"
  }
}
```

### 创建胶囊

```http
POST /api/capsules/
Content-Type: application/json

{
  "title": "量子纠缠的新理解",
  "domain": "physics",
  "topics": ["quantum", "entanglement"],
  "insight": "量子纠缠是一种瞬时的、非局域的关联",
  "evidence": [
    "Bell 实验验证了量子纠缠的存在",
    "量子隐形传态实验成功传输量子态"
  ],
  "action_items": [
    "设计新的量子纠缠验证实验",
    "探索量子纠缠在量子计算中的应用"
  ],
  "applicability": "量子计算、量子通信",
  "limitations": [],
  "source_type": "discussion",
  "source_id": "discussion-123",
  "authors": ["研究者A", "研究者B"],
  "license": "MIT"
}
```

### 搜索胶囊

```http
GET /api/capsules/search/?q=量子&domain=physics&min_score=60
```

**参数:**
- `q` (str): 搜索关键词
- `domain` (str): 领域过滤
- `topics` (str): 主题过滤（逗号分隔）
- `min_score` (float): 最低综合评分
- `min_grade` (str): 最低评级 (A/B/C/D)
- `limit` (int): 返回数量

### 其他端点

```http
GET /api/capsules/domains/     # 列出所有领域
GET /api/capsules/topics/      # 列出所有主题
GET /api/capsules/trending/    # 热门胶囊
```

## 系统端点

```http
GET /              # 服务信息
GET /health        # 健康检查
GET /docs          # API 文档
```
