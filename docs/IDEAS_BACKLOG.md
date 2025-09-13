# IDEAS BACKLOG

This document serves as a living backlog for potential features, improvements, and refactorings for the PersonalManager project. Ideas are captured here for future consideration and prioritization.

---

### UX 改进: 优化 `setup` 向导中的书籍/方法论选择流程

**来源**: 用户反馈 (2025-09-12)
**描述**: 当前 `pm setup` 向导中，书籍理论模块的启用方式是逐一询问用户“是否启用《某某书》？”这种交互方式笨拙且不直观。
**建议优化**:
1.  将逐一询问改为**单次多选**交互：列出所有可用方法论，让用户通过输入编号（如“1,3,5”）一次性选择。
2.  **概念措辞优化**：将“启用《某某书》”改为“启用 **[方法论名称] 模式** (源自《[书籍名称]》)”，使概念更清晰。
3.  **代码变量重构**：将 `config.py` 中的 `enabled_book_modules` 重命名为 `enabled_methodologies`，并同步更新所有引用。
**优先级**: 高 (UX 提升，概念对齐)
**状态**: 待规划

