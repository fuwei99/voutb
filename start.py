#!/usr/bin/env python3
"""
启动脚本 - OpenAI to Gemini Adapter
使用方法: python start.py
"""
import os
import sys
import uvicorn
from pathlib import Path

# 尝试加载 app/config.json (优先级高于 .env，但低于系统环境变量)
try:
    import json
    config_json_path = Path(__file__).parent / "app" / "config.json"
    if config_json_path.exists():
        print(f"📄 加载配置文件: {config_json_path}")
        with open(config_json_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if key and not os.environ.get(key): # 只有未设置时才设置
                    if isinstance(value, bool):
                        os.environ[key] = "true" if value else "false"
                    else:
                        os.environ[key] = str(value)
        print("✓ 配置文件加载完成\n")
except Exception as e:
    print(f"⚠️  加载配置文件失败: {e}\n")

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"📄 加载环境变量文件: {env_file}")
        load_dotenv(env_file, override=False)
        print("✓ 环境变量加载完成\n")
    else:
        print(f"⚠️  未找到 .env 文件: {env_file}")
        print("将使用系统环境变量或默认值\n")
except ImportError:
    print("⚠️  未安装 python-dotenv，使用手动加载方式")
    print("建议运行: pip install python-dotenv\n")
    # 手动加载 .env 文件
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"📄 手动加载环境变量文件: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # 只在环境变量未设置时才设置
                    if key and not os.environ.get(key):
                        os.environ[key] = value
        print("✓ 环境变量加载完成\n")
    else:
        print(f"⚠️  未找到 .env 文件: {env_file}")
        print("将使用系统环境变量或默认值\n")

# 添加app目录到Python路径
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def check_environment():
    """检查必需的环境变量"""
    print("=" * 60)
    print("检查环境配置...")
    print("=" * 60)
    
    # 检查API_KEY
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("⚠️  警告: API_KEY 未设置，将使用默认值 '123456'")
    else:
        print(f"✓ API_KEY: {'*' * len(api_key)}")
    
    # 检查认证方式
    auth_methods = []
    
    vertex_key = os.environ.get("VERTEX_EXPRESS_API_KEY")
    if vertex_key:
        keys = [k.strip() for k in vertex_key.split(',') if k.strip()]
        auth_methods.append(f"Vertex Express API Key ({len(keys)}个)")
        print(f"✓ VERTEX_EXPRESS_API_KEY: {len(keys)}个密钥")
    
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if google_creds_json:
        auth_methods.append("Google服务账号JSON")
        print("✓ GOOGLE_CREDENTIALS_JSON: 已设置")
    
    creds_dir = os.environ.get("CREDENTIALS_DIR", "/app/credentials")
    creds_path = Path(creds_dir)
    if creds_path.exists():
        json_files = list(creds_path.glob("*.json"))
        if json_files:
            auth_methods.append(f"服务账号文件 ({len(json_files)}个)")
            print(f"✓ CREDENTIALS_DIR: {creds_dir} ({len(json_files)}个JSON文件)")
    
    if not auth_methods:
        print("\n❌ 错误: 未配置任何认证方式！")
        print("请至少配置以下之一:")
        print("  1. VERTEX_EXPRESS_API_KEY")
        print("  2. GOOGLE_CREDENTIALS_JSON")
        print("  3. 在credentials/目录放置服务账号JSON文件")
        print("\n请参考 .env.example 文件配置环境变量")
        return False
    
    print(f"\n✓ 认证方式: {', '.join(auth_methods)}")
    
    # 显示可选配置
    print("\n可选配置:")
    roundrobin = os.environ.get("ROUNDROBIN", "false")
    print(f"  - 轮询模式: {roundrobin}")
    
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project:
        print(f"  - GCP项目ID: {gcp_project}")
    
    gcp_location = os.environ.get("GCP_LOCATION")
    if gcp_location:
        print(f"  - GCP区域: {gcp_location}")
    
    print("=" * 60)
    return True

def main():
    """主函数"""
    print("\n🚀 OpenAI to Gemini Adapter 启动中...\n")
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 获取配置
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8050"))
    
    print(f"\n启动服务器: http://{host}:{port}")
    print("按 Ctrl+C 停止服务\n")
    
    # 启动uvicorn
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()