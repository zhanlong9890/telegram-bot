#!/usr/bin/env python3
"""
部署前检查脚本
检查所有必需文件是否存在，确保可以成功部署
"""
import os
import sys

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} 不存在: {filepath}")
        return False

def check_file_content(filepath, required_content, description):
    """检查文件内容"""
    if not os.path.exists(filepath):
        print(f"❌ {description} 不存在: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if required_content in content:
                print(f"✅ {description}: {filepath}")
                return True
            else:
                print(f"⚠️  {description} 可能不完整: {filepath}")
                return False
    except Exception as e:
        print(f"❌ 读取 {filepath} 时出错: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 60)
    print("🚀 部署前检查")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # 检查必需文件
    print("📋 检查必需文件...")
    print("-" * 60)
    
    files_to_check = [
        ("bot.py", "主程序文件"),
        ("requirements.txt", "依赖列表"),
        ("config.py", "配置文件"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    print()
    
    # 检查 bot.py 内容
    print("📝 检查文件内容...")
    print("-" * 60)
    
    if not check_file_content("bot.py", "if __name__ == '__main__'", "bot.py 主程序入口"):
        all_ok = False
    
    if not check_file_content("requirements.txt", "python-telegram-bot", "requirements.txt 依赖"):
        all_ok = False
    
    print()
    
    # 检查可选文件
    print("📦 检查可选文件...")
    print("-" * 60)
    
    optional_files = [
        ("Procfile", "Railway/Heroku 配置"),
        ("railway.json", "Railway 配置"),
        ("runtime.txt", "Python 版本配置"),
        (".env", "环境变量文件（本地测试用）"),
        ("env.example", "环境变量示例"),
    ]
    
    for filepath, description in optional_files:
        if os.path.exists(filepath):
            print(f"✅ {description}: {filepath}")
        else:
            print(f"ℹ️  {description} 不存在（可选）: {filepath}")
    
    print()
    
    # 检查环境变量
    print("🔐 检查环境变量...")
    print("-" * 60)
    
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token:
        if len(bot_token) > 20:
            print("✅ BOT_TOKEN 已设置")
        else:
            print("⚠️  BOT_TOKEN 可能不正确（太短）")
    else:
        print("ℹ️  BOT_TOKEN 未设置（部署时需要在平台配置）")
    
    print()
    
    # 总结
    print("=" * 60)
    if all_ok:
        print("✅ 检查完成！所有必需文件都存在，可以部署。")
        print()
        print("📚 下一步：")
        print("1. 确保代码已推送到 GitHub")
        print("2. 访问 https://railway.app 创建项目")
        print("3. 配置环境变量 BOT_TOKEN")
        print("4. 等待部署完成")
        print()
        print("详细步骤请查看：部署步骤.md")
        return 0
    else:
        print("❌ 检查失败！请修复上述问题后重试。")
        return 1

if __name__ == '__main__':
    sys.exit(main())

