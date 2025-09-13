"""Gmail重要邮件处理器 - Sprint 9-10核心功能

智能识别和处理重要邮件，并转换为GTD任务
"""

import json
import re
import requests
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from .google_auth import GoogleAuthManager

logger = structlog.get_logger()


class EmailMessage:
    """Gmail邮件消息封装"""
    
    def __init__(self,
                 message_id: str,
                 thread_id: str,
                 subject: str,
                 sender: str,
                 recipient: str,
                 body: str,
                 received_date: datetime,
                 labels: List[str] = None,
                 attachments: List[str] = None,
                 importance_score: float = 0.0):
        self.message_id = message_id
        self.thread_id = thread_id
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.body = body
        self.received_date = received_date
        self.labels = labels or []
        self.attachments = attachments or []
        self.importance_score = importance_score
    
    @property
    def is_important(self) -> bool:
        """检查邮件是否重要"""
        return self.importance_score >= 0.7
    
    @property
    def is_urgent(self) -> bool:
        """检查邮件是否紧急"""
        return self.importance_score >= 0.9
    
    @property
    def sender_name(self) -> str:
        """获取发件人姓名"""
        # 解析 "Name <email@domain.com>" 格式
        match = re.match(r'^(.+?)\s*<.+>$', self.sender)
        if match:
            return match.group(1).strip()
        return self.sender
    
    @property
    def sender_email(self) -> str:
        """获取发件人邮箱"""
        match = re.search(r'<(.+?)>', self.sender)
        if match:
            return match.group(1)
        return self.sender
    
    def to_gtd_task(self) -> Task:
        """转换为GTD任务"""
        
        # 根据邮件内容推断上下文
        context = self._infer_context()
        
        # 根据重要性和紧急性推断优先级
        priority = self._infer_priority()
        
        # 根据邮件复杂度推断所需精力
        energy = self._infer_energy_level()
        
        # 生成任务标题
        task_title = f"📧 回复: {self.subject[:50]}{'...' if len(self.subject) > 50 else ''}"
        
        task = Task(
            title=task_title,
            description=self._generate_task_description(),
            status=TaskStatus.INBOX,  # 邮件任务首先进入收件箱
            context=context,
            priority=priority,
            energy_required=energy,
            estimated_duration=self._estimate_duration(),
            source="gmail",
            source_id=self.message_id
        )
        
        return task
    
    def _infer_context(self) -> TaskContext:
        """根据邮件内容推断执行上下文"""
        
        subject_lower = self.subject.lower()
        body_lower = self.body.lower()
        combined = f"{subject_lower} {body_lower}"
        
        # 上下文关键词映射
        context_keywords = {
            TaskContext.MEETING: ['会议', '讨论', 'meeting', '面谈', '约', '时间', 'schedule'],
            TaskContext.PHONE: ['电话', '通话', 'call', '联系', '沟通', '拨打'],
            TaskContext.COMPUTER: ['附件', '文档', '链接', '系统', '网站', '代码', '程序'],
            TaskContext.FOCUS: ['审阅', 'review', '意见', '建议', '分析', '规划', '策略'],
            TaskContext.OFFICE: ['报告', '表格', 'excel', '合同', '文件', '归档'],
            TaskContext.READING: ['阅读', '学习', '资料', '文档', '手册', '指南']
        }
        
        for context, keywords in context_keywords.items():
            if any(keyword in combined for keyword in keywords):
                return context
        
        # 根据发件人推断上下文
        sender_lower = self.sender.lower()
        if any(domain in sender_lower for domain in ['@company.com', '@work.com']):
            return TaskContext.COMPUTER
        
        # 默认为邮件回复上下文
        return TaskContext.COMPUTER
    
    def _infer_priority(self) -> TaskPriority:
        """根据重要性和紧急性推断优先级"""
        
        if self.is_urgent:
            return TaskPriority.HIGH
        elif self.is_important:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _infer_energy_level(self) -> EnergyLevel:
        """根据邮件复杂度推断所需精力水平"""
        
        # 分析邮件长度和复杂度
        body_length = len(self.body)
        has_attachments = len(self.attachments) > 0
        
        # 检查复杂关键词
        complex_keywords = ['分析', '评估', '规划', '设计', '策略', '方案', '详细']
        has_complex_content = any(keyword in self.body for keyword in complex_keywords)
        
        if body_length > 1000 or has_attachments or has_complex_content:
            return EnergyLevel.HIGH
        elif body_length > 300 or self.is_important:
            return EnergyLevel.MEDIUM
        else:
            return EnergyLevel.LOW
    
    def _estimate_duration(self) -> int:
        """估算处理邮件所需时间（分钟）"""
        
        base_time = 10  # 基础回复时间
        
        # 根据邮件长度调整
        body_length = len(self.body)
        if body_length > 1000:
            base_time += 30
        elif body_length > 500:
            base_time += 15
        
        # 根据附件调整
        if self.attachments:
            base_time += len(self.attachments) * 10
        
        # 根据重要性调整
        if self.is_urgent:
            base_time += 20
        elif self.is_important:
            base_time += 10
        
        return min(base_time, 120)  # 最多2小时
    
    def _generate_task_description(self) -> str:
        """生成任务描述"""
        
        desc_parts = [
            f"发件人: {self.sender}",
            f"主题: {self.subject}",
            f"收到时间: {self.received_date.strftime('%Y-%m-%d %H:%M')}",
            f"重要性评分: {self.importance_score:.2f}"
        ]
        
        if self.attachments:
            desc_parts.append(f"附件: {len(self.attachments)}个")
        
        if self.labels:
            desc_parts.append(f"标签: {', '.join(self.labels[:3])}")
        
        # 邮件摘要（前200字符）
        body_summary = self.body[:200] + "..." if len(self.body) > 200 else self.body
        desc_parts.append(f"内容摘要: {body_summary}")
        
        desc_parts.append(f"来源: Gmail")
        
        return "\\n".join(desc_parts)


class GmailProcessor:
    """Gmail重要邮件处理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.google_auth = GoogleAuthManager(config)
        
        logger.info("Gmail processor initialized")
    
    def scan_important_emails(self, days_back: int = 1, max_emails: int = 20) -> Tuple[List[EmailMessage], List[str]]:
        """扫描重要邮件
        
        Args:
            days_back: 扫描过去多少天的邮件
            max_emails: 最大邮件数量
            
        Returns:
            Tuple[重要邮件列表, 错误信息列表]
        """
        
        if not self.google_auth.is_google_authenticated():
            return [], ["未通过Google认证，请先运行: pm auth login google"]
        
        try:
            # 获取原始邮件数据
            raw_emails = self._fetch_emails(days_back, max_emails)
            
            if not raw_emails:
                logger.info("No emails found", days_back=days_back)
                return [], []
            
            # 分析和过滤重要邮件
            important_emails = []
            errors = []
            
            for email_data in raw_emails:
                try:
                    email_msg = self._parse_email(email_data)
                    
                    # 计算重要性评分
                    importance_score = self._calculate_importance(email_msg)
                    email_msg.importance_score = importance_score
                    
                    # 只保留重要邮件
                    if email_msg.is_important:
                        important_emails.append(email_msg)
                        logger.info("Found important email",
                                  subject=email_msg.subject,
                                  sender=email_msg.sender_name,
                                  importance=importance_score)
                
                except Exception as e:
                    error_msg = f"处理邮件时出错: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Error processing email", error=str(e))
            
            # 按重要性排序
            important_emails.sort(key=lambda x: x.importance_score, reverse=True)
            
            logger.info("Email scan completed", 
                       total_emails=len(raw_emails),
                       important_count=len(important_emails),
                       errors_count=len(errors))
            
            return important_emails, errors
        
        except Exception as e:
            error_msg = f"扫描邮件时发生错误: {str(e)}"
            logger.error("Email scan failed", error=str(e))
            return [], [error_msg]
    
    def convert_emails_to_tasks(self, emails: List[EmailMessage]) -> Tuple[int, List[str]]:
        """将重要邮件转换为GTD任务
        
        Args:
            emails: 邮件列表
            
        Returns:
            Tuple[转换任务数量, 错误信息列表]
        """
        
        from pm.agents.gtd_agent import GTDAgent
        agent = GTDAgent(self.config)
        
        converted_count = 0
        errors = []
        
        # 获取现有任务（避免重复转换）
        existing_tasks = agent.storage.get_all_tasks()
        existing_email_ids = {
            task.source_id for task in existing_tasks 
            if task.source_id and task.source == "gmail"
        }
        
        for email in emails:
            try:
                # 检查是否已经转换过
                if email.message_id in existing_email_ids:
                    continue
                
                # 转换为GTD任务
                task = email.to_gtd_task()
                
                # 保存任务
                success = agent.storage.save_task(task)
                if success:
                    converted_count += 1
                    logger.info("Converted email to task",
                              email_subject=email.subject,
                              task_title=task.title)
                else:
                    errors.append(f"保存邮件任务失败: {email.subject}")
            
            except Exception as e:
                error_msg = f"转换邮件'{email.subject}'为任务时出错: {str(e)}"
                errors.append(error_msg)
                logger.error("Error converting email to task",
                           email_subject=email.subject, error=str(e))
        
        logger.info("Email to task conversion completed",
                   converted_count=converted_count,
                   errors_count=len(errors))
        
        return converted_count, errors
    
    def _fetch_emails(self, days_back: int, max_emails: int) -> List[Dict[str, Any]]:
        """获取Gmail邮件数据 - 使用真实Gmail API"""
        
        logger.info("Fetching emails from Gmail API", days_back=days_back, max_emails=max_emails)
        
        try:
            # 获取访问令牌
            token_info = self.google_auth.get_google_token()
            if not token_info or token_info.is_expired:
                logger.error("No valid Google token for Gmail API")
                return []
            
            access_token = token_info.access_token
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 构建查询条件（过去N天的邮件）
            cutoff_date = datetime.now() - timedelta(days=days_back)
            # Gmail API 使用 YYYY/MM/DD 格式，并且查询需要在收件箱中的邮件
            query = f"in:inbox after:{cutoff_date.strftime('%Y/%m/%d')}"
            
            # 第一步：获取邮件列表
            list_url = 'https://www.googleapis.com/gmail/v1/users/me/messages'
            list_params = {
                'q': query,
                'maxResults': max_emails
            }
            
            response = requests.get(list_url, headers=headers, params=list_params, timeout=30)
            response.raise_for_status()
            
            messages_data = response.json()
            message_ids = messages_data.get('messages', [])
            
            if not message_ids:
                logger.info("No messages found in specified time range")
                return []
            
            logger.info(f"Found {len(message_ids)} messages, fetching details...")
            
            # 第二步：获取每封邮件的详细信息
            emails = []
            for msg_info in message_ids[:max_emails]:
                try:
                    msg_id = msg_info['id']
                    detail_url = f'https://www.googleapis.com/gmail/v1/users/me/messages/{msg_id}'
                    detail_params = {'format': 'full'}
                    
                    detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=30)
                    detail_response.raise_for_status()
                    
                    email_data = detail_response.json()
                    emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Failed to fetch email {msg_id}", error=str(e))
                    continue
            
            logger.info("Successfully fetched emails", count=len(emails))
            return emails
            
        except requests.exceptions.RequestException as e:
            logger.error("HTTP request failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Failed to fetch emails", error=str(e))
            return []
    
    def _parse_email(self, email_data: Dict[str, Any]) -> EmailMessage:
        """解析Gmail API响应数据为EmailMessage对象"""
        
        # 解析邮件头信息
        headers = {h['name']: h['value'] for h in email_data['payload'].get('headers', [])}
        
        subject = headers.get('Subject', '(无主题)')
        sender = headers.get('From', '(未知发件人)')
        recipient = headers.get('To', headers.get('Delivered-To', '(未知收件人)'))
        date_str = headers.get('Date', '')
        
        # 解析日期
        received_date = self._parse_email_date(date_str)
        
        # 解析邮件正文
        body = self._extract_email_body(email_data['payload'])
        
        # 获取标签
        labels = email_data.get('labelIds', [])
        
        # 检查附件
        attachments = self._extract_attachments(email_data['payload'])
        
        return EmailMessage(
            message_id=email_data['id'],
            thread_id=email_data['threadId'],
            subject=subject,
            sender=sender,
            recipient=recipient,
            body=body,
            received_date=received_date,
            labels=labels,
            attachments=attachments
        )
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """解析邮件日期字符串"""
        try:
            # Gmail日期格式示例: "Mon, 11 Sep 2025 15:30:45 -0400"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            # 如果解析失败，返回当前时间
            return datetime.now()
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """从Gmail API payload中提取邮件正文"""
        try:
            # 处理multipart邮件
            if payload.get('mimeType') == 'multipart/mixed' or payload.get('mimeType') == 'multipart/alternative':
                parts = payload.get('parts', [])
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    elif part.get('mimeType') == 'text/html':
                        # 如果没有纯文本，提取HTML（简单处理）
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            html_content = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                            # 简单的HTML标签移除
                            import re
                            text_content = re.sub(r'<[^>]+>', '', html_content)
                            return text_content.strip()
            
            # 处理单部分邮件
            elif payload.get('mimeType') == 'text/plain':
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
            # 如果以上都不匹配，返回空内容
            return "(无法解析邮件内容)"
            
        except Exception as e:
            logger.error("Failed to extract email body", error=str(e))
            return "(邮件内容解析失败)"
    
    def _extract_attachments(self, payload: Dict[str, Any]) -> List[str]:
        """提取附件列表"""
        attachments = []
        try:
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('filename'):
                        attachments.append(part['filename'])
        except Exception as e:
            logger.error("Failed to extract attachments", error=str(e))
        
        return attachments
    
    def _calculate_importance(self, email: EmailMessage) -> float:
        """计算邮件重要性评分（0.0 - 1.0）"""
        
        score = 0.0
        
        # 发件人重要性（0.3权重）
        sender_score = self._evaluate_sender_importance(email.sender)
        score += sender_score * 0.3
        
        # 主题重要性（0.25权重）
        subject_score = self._evaluate_subject_importance(email.subject)
        score += subject_score * 0.25
        
        # 内容重要性（0.25权重）
        content_score = self._evaluate_content_importance(email.body)
        score += content_score * 0.25
        
        # 时间敏感性（0.1权重）
        urgency_score = self._evaluate_urgency(email)
        score += urgency_score * 0.1
        
        # 标签和附件（0.1权重）
        metadata_score = self._evaluate_metadata(email)
        score += metadata_score * 0.1
        
        return min(score, 1.0)  # 确保不超过1.0
    
    def _evaluate_sender_importance(self, sender: str) -> float:
        """评估发件人重要性"""
        
        sender_lower = sender.lower()
        
        # VIP发件人关键词
        vip_keywords = ['ceo', 'director', '总监', '经理', 'manager', '客户', 'customer', 'client']
        vip_score = 0.8 if any(keyword in sender_lower for keyword in vip_keywords) else 0.3
        
        # 内部邮件通常更重要
        if '@company.com' in sender_lower or '@work.com' in sender_lower:
            vip_score += 0.2
        
        return min(vip_score, 1.0)
    
    def _evaluate_subject_importance(self, subject: str) -> float:
        """评估主题重要性"""
        
        subject_lower = subject.lower()
        
        # 紧急关键词
        urgent_keywords = ['紧急', 'urgent', '立即', 'asap', '重要', 'important']
        urgent_score = 0.9 if any(keyword in subject_lower for keyword in urgent_keywords) else 0.0
        
        # 业务关键词
        business_keywords = ['会议', 'meeting', '项目', 'project', '客户', 'customer', '反馈', 'feedback']
        business_score = 0.7 if any(keyword in subject_lower for keyword in business_keywords) else 0.0
        
        # 问题关键词
        issue_keywords = ['问题', 'issue', '错误', 'error', 'bug', '故障', 'failure']
        issue_score = 0.8 if any(keyword in subject_lower for keyword in issue_keywords) else 0.0
        
        return max(urgent_score, business_score, issue_score, 0.2)
    
    def _evaluate_content_importance(self, body: str) -> float:
        """评估邮件内容重要性"""
        
        body_lower = body.lower()
        
        # 行动导向关键词
        action_keywords = ['请', '需要', '确认', '回复', '处理', 'please', 'need', 'confirm', 'reply']
        action_score = 0.7 if any(keyword in body_lower for keyword in action_keywords) else 0.0
        
        # 内容长度（较长的邮件通常更重要）
        length_score = min(len(body) / 500, 0.5)  # 最大0.5分
        
        return max(action_score, length_score, 0.2)
    
    def _evaluate_urgency(self, email: EmailMessage) -> float:
        """评估时间敏感性"""
        
        # 最近收到的邮件可能更紧急
        hours_ago = (datetime.now() - email.received_date).total_seconds() / 3600
        
        if hours_ago < 1:
            return 1.0
        elif hours_ago < 6:
            return 0.8
        elif hours_ago < 24:
            return 0.5
        else:
            return 0.2
    
    def _evaluate_metadata(self, email: EmailMessage) -> float:
        """评估邮件元数据重要性"""
        
        score = 0.0
        
        # 重要标签
        important_labels = ['IMPORTANT', 'CATEGORY_PRIMARY', 'STARRED']
        if any(label in email.labels for label in important_labels):
            score += 0.8
        
        # 有附件的邮件通常更重要
        if email.attachments:
            score += 0.5
        
        return min(score, 1.0)