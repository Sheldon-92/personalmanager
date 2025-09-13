#!/usr/bin/env python3
"""
Google OAuth 最小权限测试脚本
用于测试和诊断 403 access_denied 错误
"""

import sys
import os
sys.path.append('/Users/sheldonzhao/programs/personal-manager/src')

from pm.core.config import PMConfig
from pm.integrations.google_auth import GoogleAuthManager

def main():
    print("🔍 Google OAuth 最小权限测试")
    print("=" * 50)
    
    config = PMConfig()
    google_auth = GoogleAuthManager(config)
    
    print("📋 配置检查:")
    print(f"✅ 凭证已配置: {google_auth.is_credentials_configured()}")
    print(f"✅ Client ID: {google_auth.client_id[:30]}...")
    print()
    
    print("🔐 生成最小权限认证URL:")
    print("只请求 Calendar 只读权限...")
    
    try:
        # 使用最小权限生成认证URL
        auth_url, state = google_auth.start_google_auth(minimal=True)
        
        print("✅ 认证URL生成成功!")
        print(f"权限范围: {' '.join(google_auth.MINIMAL_SCOPES)}")
        print()
        print("🌐 请在浏览器中打开以下链接:")
        print(auth_url)
        print()
        print("📋 测试步骤:")
        print("1. 复制上面的URL到浏览器")
        print("2. 登录您的Google账号")
        print("3. 授权访问Calendar只读权限")
        print("4. 查看是否还有403错误")
        print()
        print("💡 如果仍然出现403错误，请检查:")
        print("• Google Cloud Console中是否启用了Calendar API")
        print("• OAuth同意屏幕中是否添加了calendar.readonly权限")
        print("• 您的邮箱是否在测试用户列表中")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print()
        print("🔧 请检查:")
        print("• 凭证文件是否正确配置")
        print("• Client ID和Client Secret是否有效")

if __name__ == "__main__":
    main()