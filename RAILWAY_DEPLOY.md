# Railway 部署指南 - 5分钟快速部署

## 🚀 快速开始

### 第一步：准备 GitHub 仓库（如果没有）

#### 选项 A：使用 GitHub Desktop（最简单）

1. **下载 GitHub Desktop**
   - 访问：https://desktop.github.com
   - 下载并安装

2. **创建仓库**
   - 打开 GitHub Desktop
   - 点击 "File" → "New Repository"
   - 名称：`telegram-bot`（或任意名称）
   - 本地路径：选择 `D:\app\TG生态`
   - 勾选 "Initialize this repository with a README"
   - 点击 "Create Repository"

3. **提交并推送代码**
   - 在 GitHub Desktop 中，你会看到所有文件
   - 在左下角输入提交信息：`Initial commit`
   - 点击 "Commit to main"
   - 点击 "Publish repository"
   - 选择 "Keep this code private"（推荐）或公开
   - 点击 "Publish Repository"

#### 选项 B：使用 Git 命令行

```bash
# 在项目目录打开 PowerShell 或 CMD
cd D:\app\TG生态

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 在 GitHub 上创建新仓库（网页操作），然后：
git remote add origin https://github.com/你的用户名/telegram-bot.git
git branch -M main
git push -u origin main
```

---

### 第二步：部署到 Railway

1. **访问 Railway**
   - 打开浏览器，访问：https://railway.app
   - 点击右上角 "Login" 或 "Get Started"

2. **登录账号**
   - 选择 "Login with GitHub"
   - 授权 Railway 访问你的 GitHub 账号

3. **创建新项目**
   - 登录后，点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 在列表中找到你的仓库（`telegram-bot` 或你创建的名称）
   - 点击仓库名称

4. **配置环境变量**
   - Railway 会自动开始部署，但我们需要先配置环境变量
   - 点击项目卡片，进入项目详情
   - 点击 "Variables" 标签
   - 点击 "New Variable"
   - 添加以下环境变量：
     ```
     变量名: BOT_TOKEN
     值: 8468223563:AAGwZNfTT97sGhXaqba9ZBb-w1OznieV67k
     ```
   - 点击 "Add"
   - （可选）如果需要管理员ID，再添加：
     ```
     变量名: ADMIN_IDS
     值: 你的Telegram用户ID（用逗号分隔多个ID）
     ```

5. **等待部署完成**
   - Railway 会自动：
     - 检测到 `requirements.txt` 并安装依赖
     - 运行 `python bot.py` 启动机器人
   - 在 "Deployments" 标签可以看到部署进度
   - 等待状态变为 "Active"（绿色）

6. **验证部署**
   - 在 Telegram 中给你的机器人发送 `/start`
   - 如果机器人回复了，说明部署成功！🎉

---

## 📋 部署检查清单

- [ ] GitHub 仓库已创建并推送代码
- [ ] Railway 账号已注册并登录
- [ ] 项目已连接到 GitHub 仓库
- [ ] 环境变量 `BOT_TOKEN` 已设置
- [ ] 部署状态显示为 "Active"
- [ ] 在 Telegram 中测试机器人响应

---

## 🔧 常见问题

### Q1: 部署失败怎么办？

**检查：**
1. 查看 Railway 的 "Deployments" 标签中的日志
2. 确认 `BOT_TOKEN` 环境变量已正确设置
3. 检查 `requirements.txt` 中的依赖是否正确

### Q2: 机器人不响应？

**检查：**
1. 在 Railway 中查看日志（点击项目 → "Deployments" → 点击最新部署 → "View Logs"）
2. 确认机器人没有被其他程序运行（本地电脑上的机器人需要先停止）
3. 检查 Telegram 中机器人是否在线

### Q3: 如何查看日志？

1. 在 Railway 项目页面
2. 点击 "Deployments" 标签
3. 点击最新的部署
4. 点击 "View Logs" 查看实时日志

### Q4: 如何更新代码？

1. 在本地修改代码
2. 使用 Git 提交并推送到 GitHub：
   ```bash
   git add .
   git commit -m "更新说明"
   git push
   ```
3. Railway 会自动检测到更新并重新部署

### Q5: 如何停止机器人？

1. 在 Railway 项目页面
2. 点击项目设置（齿轮图标）
3. 点击 "Delete Project"（删除项目）
   - 或者点击服务，选择 "Stop"

---

## 💰 费用说明

**Railway 免费版：**
- $5 免费额度/月
- 对于 Telegram 机器人来说完全够用
- 超出后按使用量付费（通常不会超出）

**升级建议：**
- 如果只是运行一个机器人，免费版完全足够
- 如果流量很大，可以考虑升级到付费计划

---

## 🎯 部署成功后

恭喜！你的机器人现在已经：
- ✅ 24小时在线运行
- ✅ 自动重启（如果崩溃）
- ✅ 无需维护
- ✅ 可以随时查看日志

**下一步：**
1. 将机器人添加到你的群组
2. 给机器人管理员权限
3. 开始使用群管功能！

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 Railway 的日志输出
2. 检查环境变量是否正确
3. 确认代码已正确推送到 GitHub

祝你部署顺利！🚀

