"""PersonalManager 智能引擎模块

包含智能推荐、分析和决策支持功能
"""

from .recommendation_engine import (
    IntelligentRecommendationEngine, 
    TheoryFramework, 
    RecommendationScore,
    UserPreferences
)

__all__ = [
    'IntelligentRecommendationEngine',
    'TheoryFramework', 
    'RecommendationScore',
    'UserPreferences'
]