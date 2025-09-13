"""回顾与反思数据存储管理器 - Sprint 16核心功能

提供回顾条目、项目复盘、决策跟踪的持久化存储，支持AI工具调用
"""

import json
import structlog
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from pm.core.config import PMConfig
from pm.models.review import (
    ReviewEntry, WeeklyReview, ProjectRetrospective, DecisionReview,
    ReviewType, GrowthInsight, ActionItem, DecisionOutcome, GrowthArea
)

logger = structlog.get_logger()


class ReviewStorage:
    """回顾与反思数据存储管理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.data_dir = Path(config.data_dir) / "reviews"
        self.reviews_file = self.data_dir / "reviews.json"
        self.decisions_file = self.data_dir / "decisions.json"
        self.insights_file = self.data_dir / "insights.json"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._reviews_cache: Dict[str, ReviewEntry] = {}
        self._decisions_cache: Dict[str, DecisionReview] = {}
        self._insights_cache: Dict[str, GrowthInsight] = {}
        
        self._reviews_cache_loaded = False
        self._decisions_cache_loaded = False
        self._insights_cache_loaded = False
        
        logger.info("ReviewStorage initialized", 
                   data_dir=str(self.data_dir),
                   reviews_file=str(self.reviews_file),
                   decisions_file=str(self.decisions_file),
                   insights_file=str(self.insights_file))
    
    # ========== 回顾条目管理 ==========
    
    def _load_reviews_cache(self) -> None:
        """加载回顾数据到内存缓存"""
        if self._reviews_cache_loaded:
            return
            
        try:
            if self.reviews_file.exists():
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._reviews_cache = {}
                for review_data in data.get("reviews", []):
                    try:
                        review_type = ReviewType(review_data["review_type"])
                        
                        # 根据类型创建对应的回顾对象
                        if review_type == ReviewType.WEEKLY:
                            review = WeeklyReview.from_dict(review_data)
                        elif review_type == ReviewType.PROJECT:
                            review = ProjectRetrospective.from_dict(review_data)
                        else:
                            review = ReviewEntry.from_dict(review_data)
                        
                        self._reviews_cache[review.review_id] = review
                    except Exception as e:
                        logger.error("Failed to load review", 
                                   review_id=review_data.get("review_id", "unknown"),
                                   error=str(e))
                
                logger.info("Reviews loaded from storage", count=len(self._reviews_cache))
            else:
                logger.info("No existing reviews file, starting fresh")
                
        except Exception as e:
            logger.error("Failed to load reviews cache", error=str(e))
            self._reviews_cache = {}
        
        self._reviews_cache_loaded = True
    
    def _save_reviews_cache(self) -> bool:
        """保存回顾缓存到文件"""
        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._reviews_cache),
                "reviews": [review.to_dict() for review in self._reviews_cache.values()]
            }
            
            with open(self.reviews_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Reviews saved to storage", count=len(self._reviews_cache))
            return True
            
        except Exception as e:
            logger.error("Failed to save reviews cache", error=str(e))
            return False
    
    def save_review(self, review: ReviewEntry) -> bool:
        """保存回顾条目"""
        self._load_reviews_cache()
        
        try:
            self._reviews_cache[review.review_id] = review
            success = self._save_reviews_cache()
            
            if success:
                logger.info("Review saved", 
                           review_id=review.review_id,
                           review_type=review.review_type.value,
                           title=review.title)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save review", 
                        review_id=review.review_id,
                        error=str(e))
            return False
    
    def get_review(self, review_id: str) -> Optional[ReviewEntry]:
        """获取指定回顾条目"""
        self._load_reviews_cache()
        return self._reviews_cache.get(review_id)
    
    def get_all_reviews(self) -> List[ReviewEntry]:
        """获取所有回顾条目"""
        self._load_reviews_cache()
        return list(self._reviews_cache.values())
    
    def get_reviews_by_type(self, review_type: ReviewType) -> List[ReviewEntry]:
        """获取指定类型的回顾条目"""
        self._load_reviews_cache()
        return [review for review in self._reviews_cache.values() 
                if review.review_type == review_type]
    
    def get_reviews_by_date_range(self, start_date: date, end_date: date) -> List[ReviewEntry]:
        """获取指定日期范围内的回顾条目"""
        self._load_reviews_cache()
        
        reviews = []
        for review in self._reviews_cache.values():
            # 检查回顾时间段是否与查询范围重叠
            if (review.review_period_start <= end_date and 
                review.review_period_end >= start_date):
                reviews.append(review)
        
        return sorted(reviews, key=lambda r: r.review_period_start, reverse=True)
    
    def get_recent_reviews(self, days: int = 30, review_type: Optional[ReviewType] = None) -> List[ReviewEntry]:
        """获取最近的回顾条目"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        reviews = self.get_reviews_by_date_range(start_date, end_date)
        
        if review_type:
            reviews = [r for r in reviews if r.review_type == review_type]
        
        return reviews
    
    def delete_review(self, review_id: str) -> bool:
        """删除回顾条目"""
        self._load_reviews_cache()
        
        try:
            if review_id in self._reviews_cache:
                del self._reviews_cache[review_id]
                success = self._save_reviews_cache()
                
                if success:
                    logger.info("Review deleted", review_id=review_id)
                
                return success
            else:
                logger.warning("Review not found for deletion", review_id=review_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete review", 
                        review_id=review_id,
                        error=str(e))
            return False
    
    # ========== 决策跟踪管理 ==========
    
    def _load_decisions_cache(self) -> None:
        """加载决策数据到内存缓存"""
        if self._decisions_cache_loaded:
            return
            
        try:
            if self.decisions_file.exists():
                with open(self.decisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._decisions_cache = {}
                for decision_data in data.get("decisions", []):
                    try:
                        decision = DecisionReview.from_dict(decision_data)
                        self._decisions_cache[decision.decision_id] = decision
                    except Exception as e:
                        logger.error("Failed to load decision", 
                                   decision_id=decision_data.get("decision_id", "unknown"),
                                   error=str(e))
                
                logger.info("Decisions loaded from storage", count=len(self._decisions_cache))
            else:
                logger.info("No existing decisions file, starting fresh")
                
        except Exception as e:
            logger.error("Failed to load decisions cache", error=str(e))
            self._decisions_cache = {}
        
        self._decisions_cache_loaded = True
    
    def _save_decisions_cache(self) -> bool:
        """保存决策缓存到文件"""
        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._decisions_cache),
                "decisions": [decision.to_dict() for decision in self._decisions_cache.values()]
            }
            
            with open(self.decisions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Decisions saved to storage", count=len(self._decisions_cache))
            return True
            
        except Exception as e:
            logger.error("Failed to save decisions cache", error=str(e))
            return False
    
    def save_decision(self, decision: DecisionReview) -> bool:
        """保存决策记录"""
        self._load_decisions_cache()
        
        try:
            self._decisions_cache[decision.decision_id] = decision
            success = self._save_decisions_cache()
            
            if success:
                logger.info("Decision saved", 
                           decision_id=decision.decision_id,
                           title=decision.title)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save decision", 
                        decision_id=decision.decision_id,
                        error=str(e))
            return False
    
    def get_decision(self, decision_id: str) -> Optional[DecisionReview]:
        """获取指定决策记录"""
        self._load_decisions_cache()
        return self._decisions_cache.get(decision_id)
    
    def get_all_decisions(self) -> List[DecisionReview]:
        """获取所有决策记录"""
        self._load_decisions_cache()
        return list(self._decisions_cache.values())
    
    def get_decisions_by_date_range(self, start_date: date, end_date: date) -> List[DecisionReview]:
        """获取指定日期范围内的决策记录"""
        self._load_decisions_cache()
        
        decisions = []
        for decision in self._decisions_cache.values():
            if start_date <= decision.decision_date <= end_date:
                decisions.append(decision)
        
        return sorted(decisions, key=lambda d: d.decision_date, reverse=True)
    
    def get_recent_decisions(self, days: int = 30) -> List[DecisionReview]:
        """获取最近的决策记录"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        return self.get_decisions_by_date_range(start_date, end_date)
    
    def get_pending_decision_evaluations(self) -> List[DecisionReview]:
        """获取待评估的决策"""
        self._load_decisions_cache()
        
        pending = []
        for decision in self._decisions_cache.values():
            # 决策时间超过30天且尚未评估结果的决策
            if (decision.outcome_rating is None and 
                (date.today() - decision.decision_date).days >= 30):
                pending.append(decision)
        
        return sorted(pending, key=lambda d: d.decision_date)
    
    # ========== 成长洞察管理 ==========
    
    def _load_insights_cache(self) -> None:
        """加载成长洞察到内存缓存"""
        if self._insights_cache_loaded:
            return
            
        try:
            if self.insights_file.exists():
                with open(self.insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._insights_cache = {}
                for insight_data in data.get("insights", []):
                    try:
                        insight = GrowthInsight.from_dict(insight_data)
                        self._insights_cache[insight.insight_id] = insight
                    except Exception as e:
                        logger.error("Failed to load insight", 
                                   insight_id=insight_data.get("insight_id", "unknown"),
                                   error=str(e))
                
                logger.info("Growth insights loaded from storage", count=len(self._insights_cache))
            else:
                logger.info("No existing insights file, starting fresh")
                
        except Exception as e:
            logger.error("Failed to load insights cache", error=str(e))
            self._insights_cache = {}
        
        self._insights_cache_loaded = True
    
    def _save_insights_cache(self) -> bool:
        """保存洞察缓存到文件"""
        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._insights_cache),
                "insights": [insight.to_dict() for insight in self._insights_cache.values()]
            }
            
            with open(self.insights_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Growth insights saved to storage", count=len(self._insights_cache))
            return True
            
        except Exception as e:
            logger.error("Failed to save insights cache", error=str(e))
            return False
    
    def save_insight(self, insight: GrowthInsight) -> bool:
        """保存成长洞察"""
        self._load_insights_cache()
        
        try:
            self._insights_cache[insight.insight_id] = insight
            success = self._save_insights_cache()
            
            if success:
                logger.info("Growth insight saved", 
                           insight_id=insight.insight_id,
                           title=insight.title,
                           growth_area=insight.growth_area.value)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save insight", 
                        insight_id=insight.insight_id,
                        error=str(e))
            return False
    
    def get_insight(self, insight_id: str) -> Optional[GrowthInsight]:
        """获取指定成长洞察"""
        self._load_insights_cache()
        return self._insights_cache.get(insight_id)
    
    def get_insights_by_growth_area(self, growth_area: GrowthArea) -> List[GrowthInsight]:
        """获取指定成长领域的洞察"""
        self._load_insights_cache()
        return [insight for insight in self._insights_cache.values()
                if insight.growth_area == growth_area]
    
    def get_recent_insights(self, days: int = 30) -> List[GrowthInsight]:
        """获取最近的成长洞察"""
        self._load_insights_cache()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_insights = []
        
        for insight in self._insights_cache.values():
            if insight.created_at >= cutoff_date:
                recent_insights.append(insight)
        
        return sorted(recent_insights, key=lambda i: i.created_at, reverse=True)
    
    # ========== 统计和分析方法 ==========
    
    def get_review_statistics(self, days: int = 90) -> Dict[str, Any]:
        """获取回顾统计信息"""
        recent_reviews = self.get_recent_reviews(days)
        
        if not recent_reviews:
            return {
                "total_reviews": 0,
                "reviews_by_type": {},
                "completed_reviews": 0,
                "average_ratings": {},
                "most_active_growth_areas": []
            }
        
        # 按类型统计
        reviews_by_type = {}
        for review in recent_reviews:
            review_type = review.review_type.value
            reviews_by_type[review_type] = reviews_by_type.get(review_type, 0) + 1
        
        # 完成率
        completed_reviews = len([r for r in recent_reviews if r.is_completed])
        completion_rate = completed_reviews / len(recent_reviews) * 100 if recent_reviews else 0
        
        # 平均评分
        total_satisfaction = sum(r.overall_satisfaction for r in recent_reviews)
        total_productivity = sum(r.productivity_rating for r in recent_reviews)
        total_learning = sum(r.learning_rating for r in recent_reviews)
        
        avg_satisfaction = total_satisfaction / len(recent_reviews)
        avg_productivity = total_productivity / len(recent_reviews)
        avg_learning = total_learning / len(recent_reviews)
        
        # 成长领域统计
        all_insights = []
        for review in recent_reviews:
            all_insights.extend(review.growth_insights)
        
        growth_area_counts = {}
        for insight in all_insights:
            area = insight.growth_area.value
            growth_area_counts[area] = growth_area_counts.get(area, 0) + 1
        
        most_active_areas = sorted(growth_area_counts.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_reviews": len(recent_reviews),
            "reviews_by_type": reviews_by_type,
            "completed_reviews": completed_reviews,
            "completion_rate": round(completion_rate, 1),
            "average_ratings": {
                "satisfaction": round(avg_satisfaction, 1),
                "productivity": round(avg_productivity, 1),
                "learning": round(avg_learning, 1)
            },
            "total_action_items": sum(len(r.action_items) for r in recent_reviews),
            "total_insights": len(all_insights),
            "most_active_growth_areas": most_active_areas
        }
    
    def get_decision_quality_trends(self, months: int = 6) -> Dict[str, Any]:
        """获取决策质量趋势"""
        start_date = date.today() - timedelta(days=months * 30)
        decisions = self.get_decisions_by_date_range(start_date, date.today())
        
        if not decisions:
            return {
                "total_decisions": 0,
                "evaluated_decisions": 0,
                "average_quality_score": 0,
                "outcome_distribution": {},
                "quality_trend": []
            }
        
        evaluated_decisions = [d for d in decisions if d.outcome_rating is not None]
        
        # 结果分布
        outcome_counts = {}
        for decision in evaluated_decisions:
            outcome = decision.outcome_rating.value
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        
        # 平均质量评分
        quality_scores = [d.calculate_decision_quality_score() for d in evaluated_decisions]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # 按月统计质量趋势
        monthly_quality = {}
        for decision in evaluated_decisions:
            month_key = decision.decision_date.strftime("%Y-%m")
            if month_key not in monthly_quality:
                monthly_quality[month_key] = []
            monthly_quality[month_key].append(decision.calculate_decision_quality_score())
        
        quality_trend = []
        for month, scores in sorted(monthly_quality.items()):
            avg_month_quality = sum(scores) / len(scores)
            quality_trend.append({
                "month": month,
                "average_quality": round(avg_month_quality, 1),
                "decision_count": len(scores)
            })
        
        return {
            "total_decisions": len(decisions),
            "evaluated_decisions": len(evaluated_decisions),
            "evaluation_rate": round(len(evaluated_decisions) / len(decisions) * 100, 1) if decisions else 0,
            "average_quality_score": round(avg_quality, 1),
            "outcome_distribution": outcome_counts,
            "quality_trend": quality_trend,
            "pending_evaluations": len(self.get_pending_decision_evaluations())
        }
    
    def get_growth_insights_analysis(self, months: int = 12) -> Dict[str, Any]:
        """获取成长洞察分析"""
        days = months * 30
        insights = self.get_recent_insights(days)
        
        if not insights:
            return {
                "total_insights": 0,
                "insights_by_area": {},
                "confidence_distribution": {},
                "insights_timeline": []
            }
        
        # 按领域统计
        insights_by_area = {}
        for insight in insights:
            area = insight.growth_area.value
            insights_by_area[area] = insights_by_area.get(area, 0) + 1
        
        # 信心程度分布
        confidence_counts = {}
        for insight in insights:
            conf = insight.confidence_level
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        # 时间线分析（按月统计）
        monthly_insights = {}
        for insight in insights:
            month_key = insight.created_at.strftime("%Y-%m")
            if month_key not in monthly_insights:
                monthly_insights[month_key] = []
            monthly_insights[month_key].append(insight)
        
        insights_timeline = []
        for month, month_insights in sorted(monthly_insights.items()):
            avg_confidence = sum(i.confidence_level for i in month_insights) / len(month_insights)
            insights_timeline.append({
                "month": month,
                "count": len(month_insights),
                "average_confidence": round(avg_confidence, 1),
                "top_growth_area": max(
                    set(i.growth_area.value for i in month_insights),
                    key=lambda x: len([i for i in month_insights if i.growth_area.value == x])
                )
            })
        
        return {
            "total_insights": len(insights),
            "insights_by_area": dict(sorted(insights_by_area.items(), 
                                          key=lambda x: x[1], reverse=True)),
            "confidence_distribution": confidence_counts,
            "average_confidence": round(sum(i.confidence_level for i in insights) / len(insights), 1),
            "insights_timeline": insights_timeline,
            "most_productive_area": max(insights_by_area.items(), 
                                      key=lambda x: x[1])[0] if insights_by_area else None
        }