#!/bin/bash

# CapsuleHub GitHub 发布脚本
# 运行方式: ./scripts/publish.sh

echo "🚀 开始发布 CapsuleHub 到 GitHub..."

# 1. 如果还没有 GitHub 账号，先注册: https://github.com
# 2. 创建仓库: https://github.com/new
#    - Repository name: CapsuleHub
#    - Description: AI时代的知识资产交易所
#    - Public: ✓
#    - Add a README: ✗

# 3. 运行以下命令（替换 <your-username> 为你的用户名）:

# 方式1: 如果从未推送到 GitHub
git remote add origin https://github.com/wanyview/CapsuleHub.git
git push -u origin main

# 方式2: 如果已经有 remote
# git push -u origin main

# 4. 创建 Release:
#    访问: https://github.com/wanyview/CapsuleHub/releases/new
#    Tag version: v0.1.0
#    Release title: CapsuleHub v0.1.0
#    Description: 第一个版本发布
#    This is a pre-release: ✓

echo "✅ 完成！访问 https://github.com/wanyview/CapsuleHub 查看"
