# Handoff: pm next --push / --pull

**From**: Alex (Solution Lead)
**To**: Blake (Execution Master)
**Date**: 2024-12-24
**Status**: Ready for Implementation

---

## 1. 任务概述

为 `pm next` 命令添加 `--push` 和 `--pull` 参数，实现 NEXT.md 与 Google Tasks 的双向同步。

## 2. 需求规格

### 2.1 `pm next --push`

```
流程:
1. 扫描 ~/programs/*/NEXT.md 所有项目
2. 汇总到 personal-manager/MASTER.md (加 [项目名] 前缀)
3. 推送到 Google Tasks "NEXT Tasks" 列表
4. 跳过已存在的任务 (避免重复)

日期映射:
- 今天 → 当天日期
- 本周 → 本周五
- 待定/阻塞 → 无日期
```

### 2.2 `pm next --pull`

```
流程:
1. 从 Google Tasks "NEXT Tasks" 列表拉取完成的任务
2. 更新 MASTER.md
3. 自动分发回各项目 NEXT.md:
   - 删除原位置的 - [ ] 行
   - 追加到"已完成"区: - [x] 任务 ✓MM-DD
```

---

## 3. 文件结构

### 3.1 新增文件

| 文件 | 用途 |
|------|------|
| `src/pm/parsers/__init__.py` | 模块初始化 |
| `src/pm/parsers/next_md_parser.py` | NEXT.md 解析器 |
| `src/pm/core/next_sync.py` | 同步核心逻辑 |

### 3.2 修改文件

| 文件 | 改动 |
|------|------|
| `src/pm/integrations/google_tasks.py` | +`create_task_list()`, +`create_task()`, +`get_task_lists()` |
| `src/pm/cli/main.py` | 修改 `next` 命令添加 `--push`, `--pull` 参数 |

---

## 4. 数据模型

### 4.1 NextTask (数据类)

```python
@dataclass
class NextTask:
    title: str                              # 任务标题
    project: str                            # 所属项目名
    priority: TaskPriority                  # 优先级 (TODAY/THIS_WEEK/SOMEDAY/BLOCKED)
    is_completed: bool = False
    completed_date: Optional[date] = None
    line_number: int = 0                    # 原文件行号

    @property
    def due_date(self) -> Optional[date]:
        """根据优先级计算截止日期"""

    @property
    def formatted_title(self) -> str:
        """[项目名] 任务标题"""

    @property
    def unique_key(self) -> str:
        """项目名::任务标题 (用于去重)"""
```

### 4.2 TaskPriority (枚举)

```python
class TaskPriority(Enum):
    TODAY = "今天"
    THIS_WEEK = "本周"
    SOMEDAY = "待定"
    BLOCKED = "阻塞"
    COMPLETED = "已完成"
```

### 4.3 SyncStats (统计)

```python
@dataclass
class SyncStats:
    projects_scanned: int = 0
    tasks_found: int = 0
    tasks_pushed: int = 0
    tasks_skipped: int = 0
    tasks_pulled: int = 0
    tasks_updated: int = 0
    errors: List[str] = field(default_factory=list)
```

---

## 5. 关键函数签名

### 5.1 NextMdParser

```python
class NextMdParser:
    def parse_file(self, file_path: Path, project_name: str) -> NextMdFile:
        """解析单个 NEXT.md 文件"""

    def scan_projects(self, base_path: Path) -> List[NextMdFile]:
        """扫描目录下所有项目的 NEXT.md"""
```

### 5.2 NextSyncManager

```python
class NextSyncManager:
    GOOGLE_LIST_NAME = "NEXT Tasks"

    def __init__(self, config: PMConfig, projects_path: str = "~/programs"):
        ...

    def push(self) -> SyncStats:
        """推送任务到 Google Tasks"""

    def pull(self) -> SyncStats:
        """拉取完成状态并分发回各项目"""
```

### 5.3 GoogleTasksIntegration (新增方法)

```python
def get_task_lists(self) -> List[dict]:
    """获取所有任务列表"""

def create_task_list(self, title: str) -> Optional[str]:
    """创建新列表，返回 list_id"""

def create_task(
    self,
    list_id: str,
    title: str,
    notes: Optional[str] = None,
    due_date: Optional[date] = None
) -> Tuple[bool, str]:
    """创建任务到指定列表"""
```

---

## 6. MASTER.md 格式

```markdown
# MASTER - 跨项目任务汇总

*自动生成于 2025-12-24 10:30*

## 今天
- [ ] [personal-manager] 实现 pm next --push @12-24
- [ ] [blog] 写完 GraphQL 教程 @12-24

## 本周
- [ ] [personal-manager] 创建 MASTER.md 汇总机制 @12-27

## 阻塞
- [ ] [infra] 等待 AWS 账号审批

## 待定
- [ ] [blog] 准备新年计划文章

## 已完成
### 2025-W52
- [x] [personal-manager] 定义 NEXT.md 格式规范 ✓12-23
```

---

## 7. NEXT.md 解析规则

### 7.1 分类标题映射

| 标题关键词 | 优先级 |
|-----------|--------|
| `今天`, `today` | TODAY |
| `本周`, `week`, `this week` | THIS_WEEK |
| `待定`, `someday`, `later` | SOMEDAY |
| `阻塞`, `blocked`, `waiting` | BLOCKED |
| `已完成`, `completed`, `done` | COMPLETED |

### 7.2 任务行正则

```python
TASK_PATTERN = re.compile(r'^-\s*\[([ xX])\]\s*(.+)$')
COMPLETED_DATE_PATTERN = re.compile(r'[✓v](\d{1,2})-(\d{1,2})$')
```

---

## 8. CLI 修改

```python
@app.command()
def next(
    path: str = typer.Option("~/programs", "--path", "-p", help="项目目录路径"),
    push: bool = typer.Option(False, "--push", help="推送任务到 Google Tasks"),
    pull: bool = typer.Option(False, "--pull", help="从 Google Tasks 拉取完成状态")
):
    """查看/同步所有项目的下一步行动"""

    if push and pull:
        console.print("[red]错误: --push 和 --pull 不能同时使用[/red]")
        return

    if push:
        _do_next_push(path)
    elif pull:
        _do_next_pull(path)
    else:
        _do_next_list(path)  # 现有逻辑
```

---

## 9. 实现顺序

1. **创建 `src/pm/parsers/__init__.py`**
2. **创建 `src/pm/parsers/next_md_parser.py`** - NextTask, TaskPriority, NextMdParser
3. **修改 `src/pm/integrations/google_tasks.py`** - 添加新方法
4. **创建 `src/pm/core/next_sync.py`** - NextSyncManager
5. **修改 `src/pm/cli/main.py`** - 添加 --push, --pull
6. **测试** - 端到端验证

---

## 10. 注意事项

1. **MASTER.md 位置**: `personal-manager/MASTER.md` (项目根目录)
2. **去重逻辑**: 用 `formatted_title.lower()` 比较
3. **日期格式**: Google Tasks API 需要 RFC 3339 格式
4. **错误处理**: 单个任务失败不应阻断整体流程
5. **已完成区**: 如果 NEXT.md 没有"已完成"分区，需要自动创建

---

## 11. 验收标准

- [ ] `pm next` 正常显示 (不影响现有功能)
- [ ] `pm next --push` 成功创建 "NEXT Tasks" 列表
- [ ] `pm next --push` 正确添加 [项目名] 前缀
- [ ] `pm next --push` 跳过重复任务
- [ ] `pm next --pull` 正确拉取完成状态
- [ ] `pm next --pull` 自动分发回各项目 NEXT.md
- [ ] MASTER.md 正确生成和更新

---

**Alex 签名**: 🎯 设计完成，准备交接
