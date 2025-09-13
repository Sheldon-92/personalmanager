"""AI可调用的Obsidian集成工具函数 - Sprint 18核心功能"""

from typing import Tuple, Optional, Dict, Any, List
import structlog
from datetime import datetime
from pathlib import Path

from pm.core.config import PMConfig
from pm.integrations.obsidian_integration import ObsidianIntegration
from pm.models.obsidian import KnowledgeGraph
from pm.models.task import Task, TaskStatus

logger = structlog.get_logger()


def connect_obsidian_vault(
    vault_path: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """连接到Obsidian Vault的AI可调用工具函数
    
    Args:
        vault_path: Obsidian Vault的路径
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 连接信息)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        success, message = integration.connect_vault(vault_path)
        
        if success:
            # 执行初始扫描
            scan_success, scan_message, scan_data = integration.scan_vault()
            
            result_data = {
                'vault_path': vault_path,
                'connection_status': 'connected',
                'scan_results': scan_data if scan_success else None,
                'vault_info': integration.vault_info.to_dict() if integration.vault_info else None
            }
            
            logger.info("Obsidian vault connected successfully", vault_path=vault_path)
            return True, f"成功连接到Obsidian Vault: {message}", result_data
        else:
            return False, message, None
            
    except Exception as e:
        logger.error("Failed to connect to Obsidian vault", error=str(e))
        return False, f"连接Obsidian Vault失败: {str(e)}", None


def scan_obsidian_vault(
    vault_path: str,
    force_rescan: bool = False,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """扫描Obsidian Vault并建立索引
    
    Args:
        vault_path: Vault路径
        force_rescan: 是否强制重新扫描
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 扫描结果)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        success, message, data = integration.scan_vault(force_rescan)
        
        if success:
            logger.info("Vault scan completed", 
                       notes=data['total_notes'], 
                       attachments=data['total_attachments'])
        
        return success, message, data
        
    except Exception as e:
        logger.error("Failed to scan vault", error=str(e))
        return False, f"扫描Vault失败: {str(e)}", None


def search_obsidian_notes(
    vault_path: str,
    query: str,
    search_content: bool = True,
    search_titles: bool = True,
    search_tags: bool = True,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """搜索Obsidian笔记
    
    Args:
        vault_path: Vault路径
        query: 搜索查询
        search_content: 是否搜索内容
        search_titles: 是否搜索标题
        search_tags: 是否搜索标签
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 搜索结果)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        # 扫描vault以获取最新数据
        integration.scan_vault()
        
        # 执行搜索
        results = integration.search_notes(query, search_content, search_titles, search_tags)
        
        # 构建搜索结果
        search_data = {
            'query': query,
            'total_results': len(results),
            'search_options': {
                'content': search_content,
                'titles': search_titles,
                'tags': search_tags
            },
            'results': [note.to_dict() for note in results[:20]]  # 限制返回前20个结果
        }
        
        logger.info("Note search completed", 
                   query=query, results_count=len(results))
        
        return True, f"找到 {len(results)} 个匹配的笔记", search_data
        
    except Exception as e:
        logger.error("Failed to search notes", error=str(e))
        return False, f"搜索笔记失败: {str(e)}", None


def create_obsidian_note(
    vault_path: str,
    title: str,
    content: str,
    folder: Optional[str] = None,
    tags: Optional[List[str]] = None,
    frontmatter: Optional[Dict[str, Any]] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """在Obsidian中创建新笔记
    
    Args:
        vault_path: Vault路径
        title: 笔记标题
        content: 笔记内容
        folder: 目标文件夹（可选）
        tags: 标签列表（可选）
        frontmatter: frontmatter数据（可选）
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 创建结果)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        success, message, file_path = integration.create_note(
            title, content, folder, tags, frontmatter
        )
        
        if success:
            result_data = {
                'title': title,
                'file_path': file_path,
                'folder': folder,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'word_count': len(content.split())
            }
            
            logger.info("Note created successfully", title=title, file_path=file_path)
            return True, message, result_data
        else:
            return False, message, None
            
    except Exception as e:
        logger.error("Failed to create note", error=str(e))
        return False, f"创建笔记失败: {str(e)}", None


def sync_tasks_to_obsidian(
    vault_path: str,
    task_filter: Optional[Dict[str, Any]] = None,
    target_folder: str = "Tasks",
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """将PersonalManager任务同步到Obsidian
    
    Args:
        vault_path: Vault路径
        task_filter: 任务过滤条件
        target_folder: 目标文件夹
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 同步结果)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        # 导入GTD代理以获取任务
        from pm.agents.gtd_agent import GTDAgent
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        # 获取任务
        agent = GTDAgent(config)
        tasks = agent.get_next_actions()
        
        # 应用过滤条件
        if task_filter:
            filtered_tasks = []
            for task in tasks:
                match = True
                if 'status' in task_filter and task.status.value != task_filter['status']:
                    match = False
                if 'priority' in task_filter and task.priority and task.priority.value != task_filter['priority']:
                    match = False
                if 'context' in task_filter and task.context and task.context.value != task_filter['context']:
                    match = False
                
                if match:
                    filtered_tasks.append(task)
            
            tasks = filtered_tasks
        
        # 同步任务到Obsidian
        synced_count = 0
        failed_count = 0
        
        for task in tasks:
            # 构建任务笔记内容
            task_content = f"# {task.title}\n\n"
            
            if task.description:
                task_content += f"**描述:** {task.description}\n\n"
            
            task_content += f"**状态:** {task.status.value}\n"
            
            if task.priority:
                task_content += f"**优先级:** {task.priority.value}\n"
            
            if task.context:
                task_content += f"**情境:** {task.context.value}\n"
            
            if task.estimated_duration:
                task_content += f"**预估时长:** {task.estimated_duration}分钟\n"
            
            if task.due_date:
                task_content += f"**截止时间:** {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            
            task_content += f"\n**任务ID:** `{task.id}`\n"
            task_content += f"**创建时间:** {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            # 创建frontmatter
            frontmatter = {
                'pm_task_id': task.id,
                'status': task.status.value,
                'priority': task.priority.value if task.priority else None,
                'context': task.context.value if task.context else None,
                'created': task.created_at.strftime('%Y-%m-%d'),
                'type': 'pm_task'
            }
            
            # 创建笔记
            success, _, _ = integration.create_note(
                title=f"Task - {task.title}",
                content=task_content,
                folder=target_folder,
                tags=['pm-task', task.status.value],
                frontmatter=frontmatter
            )
            
            if success:
                synced_count += 1
            else:
                failed_count += 1
        
        sync_data = {
            'total_tasks': len(tasks),
            'synced_count': synced_count,
            'failed_count': failed_count,
            'target_folder': target_folder,
            'sync_timestamp': datetime.now().isoformat()
        }
        
        logger.info("Task sync completed", 
                   synced=synced_count, failed=failed_count)
        
        return True, f"已同步 {synced_count} 个任务到Obsidian", sync_data
        
    except Exception as e:
        logger.error("Failed to sync tasks to Obsidian", error=str(e))
        return False, f"同步任务失败: {str(e)}", None


def generate_knowledge_graph(
    vault_path: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """生成知识图谱数据
    
    Args:
        vault_path: Vault路径
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 图谱数据)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        # 扫描vault
        integration.scan_vault()
        
        # 构建知识图谱
        graph = KnowledgeGraph()
        
        # 添加节点
        for file_path, note in integration._notes_cache.items():
            graph.nodes[file_path] = {
                'id': file_path,
                'title': note.title,
                'tags': list(note.tags),
                'word_count': note.word_count,
                'link_count': len(note.outgoing_links) + len(note.incoming_links),
                'created_at': note.created_at.isoformat(),
                'modified_at': note.modified_at.isoformat()
            }
        
        # 添加边（链接关系）
        edge_id = 0
        for file_path, note in integration._notes_cache.items():
            for link in note.outgoing_links:
                # 查找目标节点
                target_file = None
                for candidate_path, candidate_note in integration._notes_cache.items():
                    if candidate_note.title == link or candidate_path == link:
                        target_file = candidate_path
                        break
                
                if target_file:
                    graph.edges.append({
                        'id': edge_id,
                        'source': file_path,
                        'target': target_file,
                        'type': 'wikilink'
                    })
                    edge_id += 1
        
        # 计算图谱统计
        graph.total_nodes = len(graph.nodes)
        graph.total_edges = len(graph.edges)
        
        if graph.total_nodes > 1:
            graph.density = (2 * graph.total_edges) / (graph.total_nodes * (graph.total_nodes - 1))
        
        # 识别枢纽笔记（链接数最多的笔记）
        link_counts = {}
        for node_id, node_data in graph.nodes.items():
            link_counts[node_id] = node_data['link_count']
        
        sorted_by_links = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)
        graph.hub_notes = [node_id for node_id, count in sorted_by_links[:5] if count > 0]
        
        # 识别孤立笔记
        graph.isolated_notes = [node_id for node_id, count in link_counts.items() if count == 0]
        
        logger.info("Knowledge graph generated", 
                   nodes=graph.total_nodes, edges=graph.total_edges)
        
        return True, "知识图谱生成成功", graph.to_dict()
        
    except Exception as e:
        logger.error("Failed to generate knowledge graph", error=str(e))
        return False, f"生成知识图谱失败: {str(e)}", None


def get_vault_statistics(
    vault_path: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取Vault统计信息
    
    Args:
        vault_path: Vault路径
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 统计数据)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        integration = ObsidianIntegration(config, vault_path)
        connect_success, _ = integration.connect_vault(vault_path)
        
        if not connect_success:
            return False, "无法连接到指定的Vault路径", None
        
        # 扫描vault
        success, _, scan_data = integration.scan_vault()
        
        if not success:
            return False, "无法扫描Vault", None
        
        # 收集详细统计
        total_words = 0
        total_reading_time = 0
        tag_counts = {}
        
        for note in integration._notes_cache.values():
            total_words += note.word_count
            total_reading_time += note.reading_time_minutes
            
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 排序标签
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats = {
            'basic_info': {
                'vault_name': integration.vault_info.vault_name if integration.vault_info else 'Unknown',
                'vault_path': vault_path,
                'last_analyzed': scan_data['last_scan']
            },
            'content_stats': {
                'total_notes': scan_data['total_notes'],
                'total_attachments': scan_data['total_attachments'],
                'total_words': total_words,
                'total_reading_time_minutes': total_reading_time,
                'average_note_length': total_words // max(1, scan_data['total_notes'])
            },
            'tag_analysis': {
                'total_unique_tags': len(tag_counts),
                'top_tags': top_tags
            },
            'network_info': {
                'notes_with_links': len([n for n in integration._notes_cache.values() if n.outgoing_links]),
                'isolated_notes': len([n for n in integration._notes_cache.values() if not n.outgoing_links and not n.incoming_links])
            }
        }
        
        logger.info("Vault statistics generated", 
                   notes=stats['content_stats']['total_notes'],
                   words=stats['content_stats']['total_words'])
        
        return True, "Vault统计信息获取成功", stats
        
    except Exception as e:
        logger.error("Failed to get vault statistics", error=str(e))
        return False, f"获取统计信息失败: {str(e)}", None