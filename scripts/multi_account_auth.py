#!/usr/bin/env python3
"""
多账号Google服务认证管理脚本
允许Calendar和Gmail使用不同的Google账号
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess

class MultiAccountManager:
    def __init__(self):
        self.base_dir = Path.home() / ".personalmanager"
        self.tokens_dir = self.base_dir / "data" / "tokens"
        self.multi_tokens_dir = self.base_dir / "data" / "multi_tokens"
        self.multi_tokens_dir.mkdir(parents=True, exist_ok=True)

    def save_current_token(self, service_name: str):
        """保存当前token为特定服务的token"""
        current_token = self.tokens_dir / "google_token.json"
        if current_token.exists():
            service_token = self.multi_tokens_dir / f"{service_name}_token.json"
            shutil.copy2(current_token, service_token)
            print(f"✅ 已保存{service_name}的认证token")
            return True
        else:
            print(f"❌ 未找到当前token文件")
            return False

    def switch_to_service(self, service_name: str):
        """切换到特定服务的token"""
        service_token = self.multi_tokens_dir / f"{service_name}_token.json"
        current_token = self.tokens_dir / "google_token.json"

        if service_token.exists():
            shutil.copy2(service_token, current_token)
            print(f"✅ 已切换到{service_name}账号")
            return True
        else:
            print(f"❌ {service_name}账号尚未配置")
            return False

    def list_configured_services(self):
        """列出已配置的服务"""
        print("\n📋 已配置的服务账号：")
        tokens = list(self.multi_tokens_dir.glob("*_token.json"))
        if not tokens:
            print("   尚未配置任何服务")
            return

        for token_file in tokens:
            service_name = token_file.stem.replace("_token", "")
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    # 尝试提取账号信息（如果有）
                    print(f"   - {service_name}: 已配置")
            except:
                print(f"   - {service_name}: 已配置")

    def setup_multi_account(self):
        """交互式设置多账号"""
        print("\n🔐 多账号Google服务设置向导")
        print("="*50)
        print("\n这个向导将帮助你为不同的Google服务配置不同的账号\n")

        # Step 1: 配置Calendar账号
        print("📅 Step 1: 配置Calendar账号")
        print("-"*30)
        input("请按Enter开始登录你的Calendar账号...")

        # 登录Calendar账号
        pm_local = Path.home() / "programs" / "personal-manager" / "bin" / "pm-local"
        subprocess.run([str(pm_local), "auth", "login"])

        # 保存为calendar token
        if self.save_current_token("calendar"):
            print("✅ Calendar账号配置成功！\n")
        else:
            print("❌ Calendar账号配置失败\n")
            return

        # Step 2: 配置Gmail账号
        print("📧 Step 2: 配置Gmail账号")
        print("-"*30)

        use_different = input("是否使用不同的账号用于Gmail？(y/n): ").lower()
        if use_different == 'y':
            print("\n现在需要登录你的Gmail账号")
            input("请按Enter开始登录你的Gmail账号...")

            # 先登出
            subprocess.run([str(pm_local), "auth", "logout"])

            # 登录Gmail账号
            subprocess.run([str(pm_local), "auth", "login"])

            # 保存为gmail token
            if self.save_current_token("gmail"):
                print("✅ Gmail账号配置成功！\n")
            else:
                print("❌ Gmail账号配置失败\n")
                return
        else:
            # 使用相同账号
            self.save_current_token("gmail")
            print("✅ Gmail使用与Calendar相同的账号\n")

        print("\n✨ 多账号配置完成！")
        self.list_configured_services()

        print("\n📝 使用说明：")
        print("1. 使用Calendar时：python3 ~/programs/personal-manager/scripts/multi_account_auth.py switch calendar")
        print("2. 使用Gmail时：python3 ~/programs/personal-manager/scripts/multi_account_auth.py switch gmail")
        print("3. 或使用包装命令（见下方）")

def main():
    import sys

    manager = MultiAccountManager()

    if len(sys.argv) < 2:
        print("使用方法：")
        print("  setup    - 设置多账号")
        print("  switch <service> - 切换到特定服务账号")
        print("  list     - 列出已配置的服务")
        return

    command = sys.argv[1]

    if command == "setup":
        manager.setup_multi_account()
    elif command == "switch" and len(sys.argv) > 2:
        service = sys.argv[2]
        manager.switch_to_service(service)
    elif command == "list":
        manager.list_configured_services()
    else:
        print("未知命令")

if __name__ == "__main__":
    main()