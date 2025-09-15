#!/usr/bin/env python3
"""
多账号架构迁移脚本

将现有的单账号Google认证迁移到新的多账号支持架构
"""

import sys
import os
from pathlib import Path
import shutil
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.core.config import PMConfig
from pm.integrations.account_manager import AccountManager


def migrate_existing_token():
    """迁移现有的google_token.json到多账号架构"""

    print("🔄 开始迁移到多账号架构...")

    config = PMConfig()
    account_manager = AccountManager(config)

    old_token_file = config.data_dir / "tokens" / "google_token.json"
    new_token_file = config.data_dir / "tokens" / "google_default_token.json"

    if not old_token_file.exists():
        print("ℹ️  未找到需要迁移的token文件，可能已经是多账号架构或未认证")
        return True

    if new_token_file.exists():
        print("ℹ️  多账号架构已存在，跳过迁移")
        return True

    try:
        # 读取现有token文件，检查是否有用户信息
        with open(old_token_file, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        print(f"📋 找到现有token，过期时间: {token_data.get('expires_at', 'Unknown')}")

        # 复制token文件到新的命名格式
        shutil.copy2(old_token_file, new_token_file)
        print(f"✅ Token文件已迁移: {old_token_file.name} -> {new_token_file.name}")

        # 确保默认账号配置存在
        accounts_config = account_manager._accounts_config
        if 'default' not in accounts_config.get('accounts', {}):
            account_manager.add_account(
                alias='default',
                display_name='现有账号',
                email='',  # 用户可以后续更新
            )
            print("✅ 创建了默认账号配置")

        print("🎉 迁移完成！现有功能将继续正常工作")
        print("\n📝 建议后续操作：")
        print("1. 运行 'pm auth list-accounts' 查看账号状态")
        print("2. 如需添加其他账号，使用 'pm auth add-account'")

        return True

    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""

    print("\n🧪 测试向后兼容性...")

    try:
        config = PMConfig()

        # 测试AccountManager初始化
        account_manager = AccountManager(config)
        print("✅ AccountManager 初始化成功")

        # 测试默认账号
        default_account = account_manager.get_default_account()
        print(f"✅ 默认账号: {default_account}")

        # 测试账号列表
        accounts = account_manager.list_accounts()
        print(f"✅ 账号列表: {list(accounts.keys())}")

        return True

    except Exception as e:
        print(f"❌ 兼容性测试失败: {str(e)}")
        return False


def verify_file_structure():
    """验证文件结构"""

    print("\n📁 验证文件结构...")

    config = PMConfig()

    # 检查必要的目录
    dirs_to_check = [
        config.data_dir / "tokens",
        Path.home() / ".personalmanager"
    ]

    for directory in dirs_to_check:
        if directory.exists():
            print(f"✅ 目录存在: {directory}")
        else:
            print(f"❌ 目录不存在: {directory}")
            return False

    # 检查配置文件
    accounts_config_file = config.data_dir / "accounts_config.json"
    if accounts_config_file.exists():
        try:
            with open(accounts_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✅ 账号配置文件: {len(config_data.get('accounts', {}))} 个账号")
        except Exception as e:
            print(f"❌ 账号配置文件损坏: {str(e)}")
            return False
    else:
        print("ℹ️  账号配置文件将在首次使用时创建")

    return True


def main():
    """主函数"""

    print("🚀 PersonalManager 多账号架构迁移工具\n")

    success = True

    # 验证文件结构
    if not verify_file_structure():
        success = False

    # 迁移现有token
    if not migrate_existing_token():
        success = False

    # 测试兼容性
    if not test_backward_compatibility():
        success = False

    print("\n" + "="*50)

    if success:
        print("🎉 迁移成功完成！")
        print("\n📋 可用的新命令:")
        print("• pm auth list-accounts          # 查看所有账号")
        print("• pm auth add-account <alias>    # 添加新账号")
        print("• pm auth login google --account=<alias>  # 指定账号登录")
        print("• pm auth switch-default <alias> # 切换默认账号")
        print("\n现有命令继续正常工作，无需修改使用方式。")
    else:
        print("❌ 迁移过程中出现错误")
        print("请检查上述错误信息并重试")
        sys.exit(1)


if __name__ == "__main__":
    main()