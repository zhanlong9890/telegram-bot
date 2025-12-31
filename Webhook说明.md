# 🌐 Webhook 模式说明

## 📚 什么是 Webhook？

Telegram Bot 有两种工作方式：

### 1. Polling（轮询）- 当前默认方式
```
机器人 ←→ Telegram 服务器
（机器人主动请求更新）
```
- ✅ 简单易用
- ✅ 不需要 HTTPS
- ⚠️ 需要持续连接
- ⚠️ 有轻微延迟

### 2. Webhook（网络钩子）- 更高效方式
```
Telegram 服务器 → 你的服务器
（Telegram 主动推送更新）
```
- ✅ 响应更快（即时推送）
- ✅ 更节省资源
- ✅ 更高效
- ⚠️ 需要 HTTPS 服务器

---

## 🎯 为什么使用 Webhook？

### 优势
1. **响应更快**：Telegram 主动推送，无需等待轮询
2. **更高效**：不需要持续连接，按需推送
3. **更稳定**：减少连接中断问题

### 要求
1. **HTTPS 必需**：Telegram 要求 Webhook URL 必须是 HTTPS
2. **公网可访问**：服务器必须可以从互联网访问

---

## 🚀 如何使用 Webhook 模式？

### 方法 1：使用 Railway（推荐）

Railway 自动提供 HTTPS 域名，完美支持 Webhook！

#### 步骤：

1. **部署到 Railway**（按之前的步骤）

2. **获取域名**
   - Railway 项目页面 → "Settings" → "Generate Domain"
   - 会得到类似 `xxx.railway.app` 的域名

3. **设置环境变量**
   ```
   BOT_TOKEN=你的机器人Token
   WEBHOOK_URL=https://你的域名.railway.app
   PORT=8000
   ```

4. **修改启动命令**
   - Railway 项目设置 → "Settings"
   - 将启动命令改为：`python bot_webhook.py`

5. **完成！**
   - Railway 会自动使用 Webhook 模式
   - 更高效，响应更快

---

### 方法 2：使用 Render

Render 也提供 HTTPS 域名。

#### 步骤：

1. **部署到 Render**
2. **获取域名**（Render 自动分配）
3. **设置环境变量**：
   ```
   WEBHOOK_URL=https://你的应用名.onrender.com
   ```
4. **修改启动命令**：`python bot_webhook.py`

---

### 方法 3：使用 Fly.io

Fly.io 提供 HTTPS 和全球 CDN。

#### 步骤：

1. **部署到 Fly.io**
2. **获取域名**（Fly.io 自动分配）
3. **设置环境变量**：
   ```
   fly secrets set WEBHOOK_URL=https://你的应用名.fly.dev
   ```
4. **修改启动命令**：`python bot_webhook.py`

---

## 🔄 自动切换

`bot_webhook.py` 支持自动切换：

- **如果设置了 `WEBHOOK_URL`**：使用 Webhook 模式
- **如果没有设置 `WEBHOOK_URL`**：自动使用 Polling 模式

这样你可以：
- 本地测试：不设置 `WEBHOOK_URL`，使用 Polling
- 云端部署：设置 `WEBHOOK_URL`，使用 Webhook

---

## 📝 环境变量说明

### 必需变量
```
BOT_TOKEN=你的机器人Token
```

### Webhook 模式变量（可选）
```
WEBHOOK_URL=https://你的域名.com
PORT=8000
```

### 说明
- **WEBHOOK_URL**：你的服务器 HTTPS 地址（不包含 `/webhook` 路径）
- **PORT**：监听端口（Railway 等平台自动提供）

---

## ⚠️ 注意事项

### 1. HTTPS 必需
- Telegram 要求 Webhook URL 必须是 HTTPS
- Railway、Render、Fly.io 都自动提供 HTTPS

### 2. 端口配置
- Railway 自动提供 `PORT` 环境变量
- 代码会自动使用

### 3. 域名配置
- 确保域名正确配置
- Webhook URL 格式：`https://域名/webhook`

---

## 🔍 如何检查 Webhook 是否工作？

### 方法 1：查看日志
```
使用 Webhook 模式: https://xxx.railway.app/webhook
监听端口: 8000
```

### 方法 2：测试机器人
- 在 Telegram 中发送 `/start`
- 如果收到回复，说明 Webhook 工作正常

---

## 💡 推荐方案

### 对于大多数用户

**推荐使用 Polling 模式**（当前方式）：
- ✅ 简单易用
- ✅ 不需要额外配置
- ✅ 适合所有部署平台

### 对于高级用户

**推荐使用 Webhook 模式**：
- ✅ 更高效
- ✅ 响应更快
- ✅ 节省资源

---

## 📚 相关文件

- `bot.py` - Polling 模式（默认）
- `bot_webhook.py` - 支持 Webhook 和 Polling 自动切换
- `Webhook部署指南.md` - 详细部署指南

---

## 🎉 总结

- **Polling**：简单，适合所有场景（当前使用）
- **Webhook**：高效，需要 HTTPS（Railway 等平台支持）

**建议**：
1. 先使用 Polling 模式部署，确保稳定
2. 稳定后切换到 Webhook 模式，获得更好性能

