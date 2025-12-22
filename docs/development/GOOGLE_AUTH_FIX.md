# 🔐 Google 认证永久解决方案

## 问题分析

您的Google认证频繁失效的原因：

1. **Token过期**：所有token都已过期（最新的是9月20日过期）
2. **Refresh Token问题**：虽然有refresh_token，但刷新失败（client ID无法确定）
3. **多账户混乱**：有4个不同的token文件，系统不确定使用哪个

## 🛠 永久解决方案

### 步骤1：清理旧Token

```bash
# 备份现有token
mkdir -p ~/.personalmanager/data/tokens/backup
mv ~/.personalmanager/data/tokens/*.json ~/.personalmanager/data/tokens/backup/

# 查看备份
ls -la ~/.personalmanager/data/tokens/backup/
```

### 步骤2：重新进行完整认证

1. **打开认证URL**（复制到浏览器）：

```
https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=755565635473-rraqd3gpdngu9etjbgj6fvug529re26v.apps.googleusercontent.com&redirect_uri=http://localhost:8080/oauth/callback&scope=https://www.googleapis.com/auth/calendar+https://www.googleapis.com/auth/tasks+https://www.googleapis.com/auth/gmail.readonly&state=permanent_auth&code_challenge=B4MS-4aGok-W2tLN7WklPutsvOa8qeyKrXybFjpLUtw&code_challenge_method=S256&access_type=offline&prompt=consent
```

2. **重要提示**：
   - 选择正确的Google账号
   - **必须点击"高级" -> "转至PersonalManager(不安全)"** （如果出现）
   - 勾选所有权限（Calendar、Tasks、Gmail）
   - 点击"继续"

3. **获取授权码**：
   - 授权后会重定向到 `http://localhost:8080/oauth/callback?code=xxxxx&state=permanent_auth`
   - 复制`code=`后面的内容（到`&`之前）

### 步骤3：使用命令行完成认证

```bash
# 进入项目目录
cd /Users/sheldonzhao/programs/personal-manager

# 运行认证命令
./bin/pm-local auth login google
```

当提示输入授权码时，粘贴上一步复制的code。

### 步骤4：验证认证

```bash
# 检查认证状态
./bin/pm-local auth status

# 测试Google Tasks同步
./bin/pm-local tasks lists

# 测试Calendar同步
./bin/pm-local calendar today
```

## 🔄 自动保持认证有效

### 创建自动刷新脚本

创建文件 `/Users/sheldonzhao/programs/personal-manager/scripts/keep_auth_alive.sh`：

```bash
#!/bin/bash
# Google认证保活脚本

cd /Users/sheldonzhao/programs/personal-manager

# 每次运行时尝试刷新token
echo "刷新Google认证..."
./bin/pm-local auth status > /dev/null 2>&1

# 如果失败，记录日志
if [ $? -ne 0 ]; then
    echo "$(date): 认证刷新失败" >> ~/.personalmanager/auth_refresh.log
else
    echo "$(date): 认证刷新成功" >> ~/.personalmanager/auth_refresh.log
fi
```

### 添加到crontab（每天自动运行）

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天早上7点前运行，确保运动提醒正常）
0 6 * * * /Users/sheldonzhao/programs/personal-manager/scripts/keep_auth_alive.sh
```

## 🔧 故障排除

### 如果认证仍然失败：

1. **检查credentials.json**：
```bash
cat ~/.personalmanager/credentials.json
# 确保有client_id和client_secret
```

2. **检查token权限**：
```bash
chmod 600 ~/.personalmanager/data/tokens/*.json
```

3. **使用不同账号**：
```bash
# 使用personal账号（如果有多个Google账号）
./bin/pm-local auth login google --account personal
```

## 📝 注意事项

1. **Refresh Token很重要**：确保在授权时看到"离线访问"权限
2. **不要删除credentials.json**：这包含了OAuth客户端信息
3. **定期检查**：每周运行一次 `./bin/pm-local auth status` 确认状态

## 🎯 快速测试

认证成功后，测试以下功能：

```bash
# 同步任务到Google Tasks
./bin/pm-local tasks sync-to

# 从Google Calendar获取事件
./bin/pm-local calendar sync

# 扫描Gmail邮件
./bin/pm-local gmail scan
```

---

**完成以上步骤后，您的Google认证应该可以长期保持有效！**