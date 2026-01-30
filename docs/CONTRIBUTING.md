# 贡献指南

感谢您对 CapsuleHub 的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 1. 报告问题
- 在 GitHub Issues 中报告 Bug
- 提出新功能建议
- 分享使用体验

### 2. 提交代码
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个 Pull Request

### 3. 改进文档
- 修正错别字
- 补充使用示例
- 翻译文档

## 代码规范

### Python
- 使用 Black 格式化
- 使用 isort 排序导入
- 遵循 PEP 8
- 添加类型注解

```bash
pip install black isort mypy
black .
isort .
mypy .
```

### 提交信息
- 使用语义化提交信息
- 遵循 Conventional Commits 规范
- 示例：
  - `feat: Add new search API`
  - `fix: Resolve storage bug`
  - `docs: Update API documentation`

## 分支策略

- `main` - 生产分支
- `develop` - 开发分支
- `feature/*` - 特性分支
- `hotfix/*` - 紧急修复

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_capsules.py
```

## 代码审查

- 所有 PR 需要至少一个 Reviewer 批准
- 确保 CI 通过
- 保持代码变更专注且小

## 行为准则

请遵循 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。

---

有问题？请在 GitHub Discussions 中提问。
