# 🌐 Webhook 部署指南

## 📚 什么是 Webhook？

Telegram Bot 有两种工作方式：

### 1. Polling（轮询）- 当前使用的方式
- 机器人**主动**向 Telegram 服务器请求更新
- 需要保持连接，持续运行
- 适合：本地运行、云服务器部署

### 2. Webhook（网络钩子）- 更高效的方式
- Telegram 服务器**主动推送**更新到你的服务器
- 不需要持续轮询，更节省资源
- 需要：**HTTPS 服务器**（Telegram 要求）
- 适合：有 HTTPS 服务器的部署

---

## 🎯 Webhook vs Polling 对比

| 特性 | Polling（轮询） | Webhook（钩子） |
|------|----------------|-----------------|
| **连接方式** | 机器人主动请求 | Telegram 主动推送 |
| **资源消耗** | 持续连接 | 按需推送 |
| **服务器要求** | 任何服务器 | 需要 HTTPS |
| **响应速度** | 有延迟 | 即时 |
| **部署难度** | 简单 | 需要 HTTPS |

---

## 🚀 Webhook 部署方案

### 方案 1：使用 Railway + Webhook（推荐）

Railway 提供 HTTPS 域名，可以直接使用 Webhook！

#### 步骤：

1. **部署到 Railway**（按之前的步骤）
2. **获取 Railway 域名**
   - 在 Railway 项目页面
   - 点击 "Settings" → "Generate Domain"
   - 会得到一个类似 `xxx.railway.app` 的域名

3. **修改代码使用 Webhook**

创建 `bot_webhook.py`：

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN
import os

# 从环境变量获取 Webhook URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("机器人运行中！")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    if WEBHOOK_URL:
        # 使用 Webhook 模式
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # 回退到 Polling 模式
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

4. **设置环境变量**
   - `WEBHOOK_URL`: `https://你的域名.railway.app/webhook`
   - `PORT`: `8000`（Railway 自动提供）

---

### 方案 2：使用 Render + Webhook

Render 也提供 HTTPS 域名。

#### 步骤：

1. **部署到 Render**（按之前的步骤）
2. **获取 Render 域名**
   - Render 会自动分配域名
   - 格式：`xxx.onrender.com`

3. **配置 Webhook**
   - 设置环境变量 `WEBHOOK_URL`
   - 使用上面的代码

---

### 方案 3：使用 Fly.io + Webhook

Fly.io 提供 HTTPS 和全球 CDN。

#### 步骤：

1. **部署到 Fly.io**
2. **获取域名**
   - Fly.io 自动分配域名
   - 或使用自定义域名

3. **配置 Webhook**
   - 同上

---

## 🔧 修改现有代码支持 Webhook

### 创建 `bot_webhook.py`

```python
"""
支持 Webhook 模式的机器人
自动检测环境变量，支持 Webhook 和 Polling 两种模式
"""
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, LOG_LEVEL, LOG_FILE

# 导入所有命令处理器（从 bot.py）
from admin_commands import (
    ban_user, unban_user, mute_user, unmute_user,
    warn_user, delete_message, get_user_info, unwarn_user, get_warnings
)
from points_system import (
    my_points, points_leaderboard, add_points_command,
    remove_points_command, set_points_command,
    handle_message_points
)
from auto_moderation import (
    auto_delete_ads, welcome_new_member
)
from chat_settings import (
    set_welcome, get_welcome, set_rules, get_rules,
    toggle_auto_delete_ads, toggle_welcome, chat_settings
)
from anti_spam import (
    anti_flood, detect_duplicate_messages
)
from statistics import group_stats
from utils import get_id, group_info, admins_list
from channel_management import (
    pin_message, unpin_message
)
from error_handler import error_handler

# 配置日志
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_handlers = [logging.StreamHandler()]

if LOG_FILE:
    log_handlers.append(logging.FileHandler(LOG_FILE, encoding='utf-8'))

logging.basicConfig(
    format=log_format,
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_PATH = '/webhook'  # Webhook 路径

# 导入 start 和 help_command（从 bot.py 复制）
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    chat = update.effective_chat
    
    if chat and chat.type == 'channel':
        welcome_text = """
🤖 欢迎使用频道管理机器人！

📺 频道管理员可用命令：

🔧 基础管理：
/del - 删除消息（回复消息）
/pin - 置顶消息（回复消息）
/unpin - 取消所有置顶消息

📊 信息查看：
/id - 获取频道ID
/groupinfo - 查看频道信息
/admins - 查看管理员列表
/stats - 查看频道统计

/help - 显示详细帮助

⚠️ 注意：频道不支持踢人、禁言、积分等功能
        """
    else:
        welcome_text = """
🤖 欢迎使用群管机器人！

📋 管理命令（仅管理员）：
/ban - 踢出用户
/unban - 解封用户
/mute [时间] - 禁言用户
/unmute - 解除禁言
/warn [原因] - 警告用户
/unwarn - 清除警告
/warns - 查看警告次数
/del - 删除消息
/info - 查看用户信息

💰 积分命令：
/points - 查看自己的积分
/top - 查看积分排行榜

📊 实用工具：
/id - 获取用户ID和群组ID
/groupinfo - 查看群组信息
/admins - 查看管理员列表
/stats - 查看统计（管理员）
/pin - 置顶消息（管理员）
/unpin - 取消置顶（管理员）

⚙️ 群组设置（仅管理员）：
/setwelcome <消息> - 设置欢迎消息
/getwelcome - 查看欢迎消息
/setrules <规则> - 设置群规
/rules - 查看群规
/settings - 查看群组设置

/help - 显示详细帮助
        """
    
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    # 简化版，完整版从 bot.py 复制
    await update.message.reply_text("发送 /start 查看所有命令")

def main():
    """主函数"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册所有命令处理器（从 bot.py 复制）
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # 管理命令
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("unwarn", unwarn_user))
    application.add_handler(CommandHandler("warns", get_warnings))
    application.add_handler(CommandHandler("del", delete_message))
    application.add_handler(CommandHandler("info", get_user_info))
    
    # 积分命令
    application.add_handler(CommandHandler("points", my_points))
    application.add_handler(CommandHandler("top", points_leaderboard))
    application.add_handler(CommandHandler("addpoints", add_points_command))
    application.add_handler(CommandHandler("removepoints", remove_points_command))
    application.add_handler(CommandHandler("setpoints", set_points_command))
    
    # 群组设置命令
    application.add_handler(CommandHandler("setwelcome", set_welcome))
    application.add_handler(CommandHandler("getwelcome", get_welcome))
    application.add_handler(CommandHandler("setrules", set_rules))
    application.add_handler(CommandHandler("rules", get_rules))
    application.add_handler(CommandHandler("settings", chat_settings))
    application.add_handler(CommandHandler("toggleads", toggle_auto_delete_ads))
    application.add_handler(CommandHandler("togglewelcome", toggle_welcome))
    
    # 实用工具命令
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("chatid", get_id))
    application.add_handler(CommandHandler("groupinfo", group_info))
    application.add_handler(CommandHandler("admins", admins_list))
    application.add_handler(CommandHandler("stats", group_stats))
    application.add_handler(CommandHandler("pin", pin_message))
    application.add_handler(CommandHandler("unpin", unpin_message))
    
    # 消息处理器
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        anti_flood,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        detect_duplicate_messages,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        auto_delete_ads,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message_points
    ))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    ))
    
    application.add_error_handler(error_handler)
    
    # 根据环境变量选择运行模式
    if WEBHOOK_URL:
        logger.info(f"使用 Webhook 模式: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        logger.info("使用 Polling 模式")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

---

## 📝 部署步骤（Webhook 模式）

### Railway 部署（Webhook）

1. **部署代码**（按之前的步骤）
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
   - 在 Railway 项目设置中
   - 将启动命令改为：`python bot_webhook.py`

5. **完成！**
   - Railway 会自动使用 Webhook 模式
   - 更高效，响应更快

---

## ⚠️ 注意事项

### Webhook 要求

1. **HTTPS 必需**
   - Telegram 要求 Webhook URL 必须是 HTTPS
   - Railway、Render、Fly.io 都提供 HTTPS

2. **端口配置**
   - Railway 自动提供 `PORT` 环境变量
   - 代码会自动使用

3. **域名配置**
   - 确保域名正确配置
   - Webhook URL 格式：`https://域名/webhook`

---

## 🔄 切换模式

### 从 Polling 切换到 Webhook

1. 设置 `WEBHOOK_URL` 环境变量
2. 使用 `bot_webhook.py` 启动
3. 机器人会自动切换到 Webhook 模式

### 从 Webhook 切换回 Polling

1. 删除或清空 `WEBHOOK_URL` 环境变量
2. 使用 `bot.py` 启动（或 `bot_webhook.py` 会自动回退）

---

## 💡 推荐方案

### 对于大多数用户

**推荐使用 Polling 模式**（当前方式）：
- ✅ 简单易用
- ✅ 不需要 HTTPS 配置
- ✅ 适合所有部署平台

### 对于高级用户

**推荐使用 Webhook 模式**：
- ✅ 更高效
- ✅ 响应更快
- ✅ 节省资源

---

## 📚 总结

- **Polling**：简单，适合所有场景（当前使用）
- **Webhook**：高效，需要 HTTPS（Railway 等平台支持）

**建议**：先使用 Polling 模式部署，稳定后再考虑切换到 Webhook。

