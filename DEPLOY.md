# 机器人部署指南 - 让机器人24小时运行

## 🤔 为什么别人的机器人一直在线？

**关键区别：**
- ❌ **你的机器人**：运行在本地电脑上，电脑关机或程序关闭，机器人就停止
- ✅ **别人的机器人**：部署在云服务器上，服务器24小时运行，机器人一直在线

## 🚀 解决方案

### 方案一：免费云平台部署（推荐新手）

#### 1. Railway 部署（推荐，最简单）

**优点：** 免费额度充足，部署简单，自动重启

**步骤：**

1. **注册账号**
   - 访问 https://railway.app
   - 使用 GitHub 账号登录

2. **创建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 连接你的 GitHub 仓库（如果没有，先上传代码到 GitHub）

3. **配置环境变量**
   - 在 Railway 项目设置中添加环境变量：
     - `BOT_TOKEN`: 你的机器人 Token
     - `ADMIN_IDS`: 管理员ID（可选）

4. **部署**
   - Railway 会自动检测 `requirements.txt` 并安装依赖
   - 设置启动命令：`python bot.py`
   - 点击部署，等待完成

5. **完成！**
   - 机器人会自动运行，即使你关闭浏览器也会继续工作

---

#### 2. Render 部署

**步骤：**

1. 访问 https://render.com 并注册
2. 创建新的 "Web Service"
3. 连接 GitHub 仓库
4. 设置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Environment Variables**: 添加 `BOT_TOKEN`
5. 点击 "Create Web Service"

**注意：** Render 免费版会在15分钟无活动后休眠，需要升级到付费版才能24小时运行。

---

### 方案二：Windows 本地服务（免费，但电脑需开机）

如果你想让机器人在本地电脑上24小时运行（电脑需要一直开机），可以使用 Windows 服务：

#### 使用 NSSM（推荐）

1. **下载 NSSM**
   - 访问 https://nssm.cc/download
   - 下载适合你系统的版本（32位或64位）

2. **安装服务**
   ```powershell
   # 以管理员身份运行 PowerShell
   # 解压 NSSM 到 C:\nssm
   
   # 安装服务
   C:\nssm\win64\nssm.exe install TelegramBot "C:\Python\python.exe" "D:\app\TG生态\bot.py"
   
   # 设置工作目录
   C:\nssm\win64\nssm.exe set TelegramBot AppDirectory "D:\app\TG生态"
   
   # 启动服务
   C:\nssm\win64\nssm.exe start TelegramBot
   ```

3. **管理服务**
   - 启动：`nssm start TelegramBot`
   - 停止：`nssm stop TelegramBot`
   - 删除：`nssm remove TelegramBot confirm`

---

### 方案三：VPS 服务器部署（最稳定）

如果你有 VPS（如阿里云、腾讯云、DigitalOcean等）：

#### Linux 服务器部署

1. **上传代码到服务器**
   ```bash
   # 使用 scp 或 git clone
   git clone your-repo-url
   cd TG生态
   ```

2. **安装依赖**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **使用 systemd 创建服务**
   
   创建服务文件：`/etc/systemd/system/telegram-bot.service`
   ```ini
   [Unit]
   Description=Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/TG生态
   ExecStart=/usr/bin/python3 bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **启动服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```

5. **查看状态**
   ```bash
   sudo systemctl status telegram-bot
   ```

---

## 📊 方案对比

| 方案 | 成本 | 难度 | 稳定性 | 推荐度 |
|------|------|------|--------|--------|
| Railway | 免费 | ⭐ 简单 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Render | 免费/付费 | ⭐⭐ 中等 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Windows 服务 | 免费 | ⭐⭐ 中等 | ⭐⭐⭐ | ⭐⭐⭐ |
| VPS | 付费 | ⭐⭐⭐ 较难 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 🎯 推荐方案

**新手推荐：Railway**
- 完全免费
- 部署简单
- 自动重启
- 无需维护

**有服务器经验：VPS + systemd**
- 完全控制
- 性能最好
- 最稳定

## ⚠️ 注意事项

1. **环境变量安全**
   - 不要在代码中硬编码 Token
   - 使用环境变量或 `.env` 文件

2. **日志监控**
   - 部署后定期查看日志
   - 确保机器人正常运行

3. **备份**
   - 定期备份代码和配置
   - 保存好 Bot Token

4. **免费额度**
   - Railway 免费版有使用限制，但通常足够小型机器人使用
   - 如果流量大，考虑升级或使用 VPS

## 🔧 故障排查

**机器人不响应？**
- 检查服务器是否运行
- 查看日志文件
- 确认 Bot Token 正确

**服务自动停止？**
- 检查服务器资源使用
- 查看错误日志
- 确认网络连接正常

