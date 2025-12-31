"""
部署前检查脚本
检查项目是否准备好部署到 Railway
"""
import os
import sys

def check_file(file_path, required=True):
    """检查文件是否存在"""
    exists = os.path.exists(file_path)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {file_path}")
    return exists

def check_env_var(var_name):
    """检查环境变量"""
    value = os.getenv(var_name)
    if value:
        # 只显示前10个字符，隐藏敏感信息
        display = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {var_name} = {display}")
        return True
    else:
        print(f"⚠️ {var_name} 未设置（将在 Railway 中设置）")
        return False

def main():
    print("=" * 50)
    print("Railway 部署检查")
    print("=" * 50)
    print()
    
    print("📁 检查必要文件...")
    files_ok = True
    files_ok &= check_file("bot.py", required=True)
    files_ok &= check_file("config.py", required=True)
    files_ok &= check_file("admin_commands.py", required=True)
    files_ok &= check_file("requirements.txt", required=True)
    files_ok &= check_file("railway.json", required=False)
    files_ok &= check_file("Procfile", required=False)
    print()
    
    print("🔑 检查环境变量...")
    check_env_var("BOT_TOKEN")
    check_env_var("ADMIN_IDS")
    print()
    
    print("📦 检查依赖...")
    try:
        import telegram
        print(f"✅ python-telegram-bot 已安装 (版本: {telegram.__version__})")
    except ImportError:
        print("❌ python-telegram-bot 未安装")
        print("   运行: pip install -r requirements.txt")
        files_ok = False
    print()
    
    print("=" * 50)
    if files_ok:
        print("✅ 检查完成！项目已准备好部署")
        print()
        print("下一步：")
        print("1. 将代码上传到 GitHub")
        print("2. 在 Railway 中创建项目")
        print("3. 设置环境变量 BOT_TOKEN")
        print()
        print("详细步骤请查看：RAILWAY_DEPLOY.md")
    else:
        print("❌ 检查未通过，请修复上述问题")
        sys.exit(1)
    print("=" * 50)

if __name__ == "__main__":
    main()

