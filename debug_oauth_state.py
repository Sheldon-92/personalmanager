#!/usr/bin/env python3
"""
OAuth State参数调试工具
用于诊断和修复状态参数验证问题
"""

import sys
import os
sys.path.append('/Users/sheldonzhao/programs/personal-manager/src')

from pm.core.config import PMConfig
from pm.integrations.google_auth import GoogleAuthManager
from datetime import datetime

def main():
    print("🔍 OAuth State参数调试")
    print("=" * 50)
    
    config = PMConfig()
    google_auth = GoogleAuthManager(config)
    oauth_manager = google_auth.oauth_manager
    
    print("📋 当前状态检查:")
    print(f"Pending states数量: {len(oauth_manager._pending_states)}")
    
    if oauth_manager._pending_states:
        print("\n存储的状态参数:")
        for state, info in oauth_manager._pending_states.items():
            created_time = info['created_at']
            age_seconds = (datetime.now() - created_time).total_seconds()
            print(f"• State: {state[:8]}...")
            print(f"  创建时间: {created_time.strftime('%H:%M:%S')}")
            print(f"  存在时长: {age_seconds:.1f}秒")
            print(f"  服务: {info['service_name']}")
            print()
    
    # 清理过期状态
    print("🧹 清理过期状态...")
    oauth_manager.cleanup_expired_states()
    
    print(f"清理后的状态数量: {len(oauth_manager._pending_states)}")
    print()
    
    print("🔧 生成新的认证URL进行测试:")
    try:
        auth_url, new_state = google_auth.start_google_auth(['calendar'], minimal=True)
        print(f"✅ 新状态参数: {new_state[:8]}...")
        print(f"✅ URL长度: {len(auth_url)}")
        
        # 验证新状态是否存储
        if new_state in oauth_manager._pending_states:
            print("✅ 新状态参数已正确存储")
            state_info = oauth_manager._pending_states[new_state]
            print(f"   创建时间: {state_info['created_at'].strftime('%H:%M:%S')}")
        else:
            print("❌ 新状态参数存储失败")
        
        print(f"\n📋 测试URL:")
        print(f"{auth_url[:100]}...")
        
    except Exception as e:
        print(f"❌ 生成认证URL失败: {str(e)}")
    
    print(f"\n💡 建议:")
    print("1. 确保每次认证都生成新的state参数")
    print("2. 在浏览器授权后立即处理回调")
    print("3. 避免重复使用旧的认证URL")

if __name__ == "__main__":
    main()