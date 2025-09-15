"""
Custom Recommender Plugin
Provides advanced recommendation algorithms and custom scoring models
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import math

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.pm.plugins.sdk import (
    PluginBase,
    PluginMetadata,
    PluginPermission,
    HookType,
    HookContext
)

logger = logging.getLogger(__name__)


class CustomRecommenderPlugin(PluginBase):
    """Plugin for custom recommendation algorithms"""

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="custom_recommender",
            version="1.0.0",
            author="PM Team",
            description="Advanced recommendation algorithms with ML-based scoring and personalization",
            required_permissions={
                PluginPermission.READ_DATA,
                PluginPermission.WRITE_DATA,
                PluginPermission.HOOK_REGISTRATION,
                PluginPermission.API_ACCESS
            },
            hooks={
                HookType.PRE_RECOMMENDATION: ["on_pre_recommendation"],
                HookType.POST_RECOMMENDATION: ["on_post_recommendation"],
                HookType.PRE_COMMAND: ["on_command_check"]
            },
            config_schema={
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "enum": ["collaborative", "content_based", "hybrid", "ml_enhanced"],
                        "default": "hybrid"
                    },
                    "min_confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.6
                    },
                    "max_recommendations": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    },
                    "personalization_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium"
                    },
                    "use_context": {
                        "type": "boolean",
                        "default": True
                    },
                    "feature_weights": {
                        "type": "object",
                        "properties": {
                            "frequency": {"type": "number", "default": 0.3},
                            "recency": {"type": "number", "default": 0.2},
                            "similarity": {"type": "number", "default": 0.3},
                            "popularity": {"type": "number", "default": 0.2}
                        }
                    }
                },
                "required": []
            }
        )

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Set default configuration
            self._set_defaults()

            # Initialize recommendation engine components
            self.user_profiles = {}
            self.item_features = {}
            self.interaction_history = []
            self.recommendation_cache = {}
            self.model_metrics = {
                "total_recommendations": 0,
                "successful_recommendations": 0,
                "average_confidence": 0.0,
                "algorithm_usage": defaultdict(int)
            }

            # Initialize feature extractors
            self.feature_extractors = {
                "frequency": self._extract_frequency_features,
                "recency": self._extract_recency_features,
                "similarity": self._extract_similarity_features,
                "popularity": self._extract_popularity_features
            }

            # Initialize algorithms
            self.algorithms = {
                "collaborative": self._collaborative_filtering,
                "content_based": self._content_based_filtering,
                "hybrid": self._hybrid_recommendation,
                "ml_enhanced": self._ml_enhanced_recommendation
            }

            self._logger.info(f"Custom Recommender initialized with algorithm: {self.config['algorithm']}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize Custom Recommender: {e}")
            return False

    async def shutdown(self) -> None:
        """Clean up resources"""
        # Save model metrics
        try:
            metrics_file = "/tmp/recommender_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.model_metrics, f, indent=2)
            self._logger.info("Custom Recommender shutdown complete")
        except Exception as e:
            self._logger.error(f"Error saving metrics: {e}")

    def _set_defaults(self) -> None:
        """Set default configuration values"""
        defaults = {
            "algorithm": "hybrid",
            "min_confidence": 0.6,
            "max_recommendations": 10,
            "personalization_level": "medium",
            "use_context": True,
            "feature_weights": {
                "frequency": 0.3,
                "recency": 0.2,
                "similarity": 0.3,
                "popularity": 0.2
            }
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    async def generate_recommendations(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        item_pool: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        try:
            # Check cache
            cache_key = f"{user_id}_{hash(str(context))}"
            if cache_key in self.recommendation_cache:
                cached = self.recommendation_cache[cache_key]
                if self._is_cache_valid(cached):
                    return cached["recommendations"]

            # Get user profile
            user_profile = await self._get_user_profile(user_id)

            # Get candidate items
            if item_pool is None:
                item_pool = await self._get_candidate_items(user_id, context)

            # Apply selected algorithm
            algorithm = self.config["algorithm"]
            recommendations = await self.algorithms[algorithm](
                user_profile, item_pool, context
            )

            # Filter by confidence threshold
            recommendations = [
                r for r in recommendations
                if r["confidence"] >= self.config["min_confidence"]
            ]

            # Limit number of recommendations
            recommendations = recommendations[:self.config["max_recommendations"]]

            # Add metadata
            for rec in recommendations:
                rec["algorithm"] = algorithm
                rec["timestamp"] = datetime.now().isoformat()
                rec["user_id"] = user_id

            # Update cache
            self.recommendation_cache[cache_key] = {
                "recommendations": recommendations,
                "timestamp": datetime.now()
            }

            # Update metrics
            self._update_metrics(algorithm, recommendations)

            return recommendations

        except Exception as e:
            self._logger.error(f"Failed to generate recommendations: {e}")
            return []

    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "user_id": user_id,
                "preferences": {},
                "interaction_history": [],
                "feature_vector": [],
                "created_at": datetime.now().isoformat()
            }
        return self.user_profiles[user_id]

    async def _get_candidate_items(
        self, user_id: str, context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get candidate items for recommendation"""
        # Simulate getting items from database
        # In production, this would query actual data
        items = []
        for i in range(50):  # Generate sample items
            items.append({
                "id": f"item_{i}",
                "name": f"Item {i}",
                "category": random.choice(["task", "project", "document", "resource"]),
                "tags": random.sample(["urgent", "important", "review", "pending", "new"], k=2),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "popularity": random.random(),
                "features": [random.random() for _ in range(10)]
            })
        return items

    async def _collaborative_filtering(
        self,
        user_profile: Dict[str, Any],
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendation"""
        recommendations = []

        for item in items:
            # Calculate similarity with other users who liked this item
            similarity_score = self._calculate_user_similarity(user_profile, item)

            # Calculate collaborative score
            score = similarity_score * 0.7 + random.random() * 0.3  # Add some randomness

            recommendations.append({
                "item": item,
                "score": score,
                "confidence": min(score, 1.0),
                "method": "collaborative",
                "explanation": f"Users with similar preferences liked this"
            })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    async def _content_based_filtering(
        self,
        user_profile: Dict[str, Any],
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Content-based filtering recommendation"""
        recommendations = []

        # Get user preference vector
        user_vector = user_profile.get("feature_vector", [0] * 10)

        for item in items:
            # Calculate content similarity
            item_vector = item.get("features", [0] * 10)
            similarity = self._cosine_similarity(user_vector, item_vector)

            # Add context boost if applicable
            if context and self.config["use_context"]:
                context_boost = self._calculate_context_relevance(item, context)
                similarity = similarity * 0.7 + context_boost * 0.3

            recommendations.append({
                "item": item,
                "score": similarity,
                "confidence": similarity,
                "method": "content_based",
                "explanation": f"Matches your content preferences"
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    async def _hybrid_recommendation(
        self,
        user_profile: Dict[str, Any],
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Hybrid recommendation combining multiple methods"""
        # Get recommendations from different algorithms
        collab_recs = await self._collaborative_filtering(user_profile, items, context)
        content_recs = await self._content_based_filtering(user_profile, items, context)

        # Create recommendation map
        rec_map = {}

        # Combine scores
        for rec in collab_recs:
            item_id = rec["item"]["id"]
            rec_map[item_id] = {
                "item": rec["item"],
                "collab_score": rec["score"],
                "content_score": 0,
                "method": "hybrid"
            }

        for rec in content_recs:
            item_id = rec["item"]["id"]
            if item_id in rec_map:
                rec_map[item_id]["content_score"] = rec["score"]
            else:
                rec_map[item_id] = {
                    "item": rec["item"],
                    "collab_score": 0,
                    "content_score": rec["score"],
                    "method": "hybrid"
                }

        # Calculate hybrid scores
        recommendations = []
        for item_id, data in rec_map.items():
            # Weighted combination
            hybrid_score = (
                data["collab_score"] * 0.5 +
                data["content_score"] * 0.5
            )

            # Apply feature weights
            feature_scores = await self._calculate_feature_scores(data["item"], user_profile)
            weighted_score = self._apply_feature_weights(hybrid_score, feature_scores)

            recommendations.append({
                "item": data["item"],
                "score": weighted_score,
                "confidence": min(weighted_score, 1.0),
                "method": "hybrid",
                "explanation": "Combined collaborative and content-based signals",
                "breakdown": {
                    "collaborative": data["collab_score"],
                    "content": data["content_score"],
                    "features": feature_scores
                }
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    async def _ml_enhanced_recommendation(
        self,
        user_profile: Dict[str, Any],
        items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """ML-enhanced recommendation with advanced features"""
        # This would use actual ML models in production
        # For now, simulate with enhanced scoring

        recommendations = []

        for item in items:
            # Extract all features
            features = await self._extract_all_features(item, user_profile, context)

            # Simulate ML model prediction
            ml_score = self._simulate_ml_prediction(features)

            # Apply personalization
            personalized_score = self._apply_personalization(
                ml_score, user_profile, self.config["personalization_level"]
            )

            recommendations.append({
                "item": item,
                "score": personalized_score,
                "confidence": self._calculate_confidence(features, personalized_score),
                "method": "ml_enhanced",
                "explanation": "Advanced ML model with personalization",
                "features": features
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    async def _calculate_feature_scores(
        self, item: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate individual feature scores"""
        scores = {}

        for feature_name, extractor in self.feature_extractors.items():
            scores[feature_name] = extractor(item, user_profile)

        return scores

    async def _extract_all_features(
        self,
        item: Dict[str, Any],
        user_profile: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract all features for ML model"""
        features = {
            "item_features": item.get("features", []),
            "user_features": user_profile.get("feature_vector", []),
            "interaction_count": len(user_profile.get("interaction_history", [])),
            "item_popularity": item.get("popularity", 0),
            "recency_score": self._calculate_recency(item),
            "category_match": 1.0 if item.get("category") in user_profile.get("preferences", {}).get("categories", []) else 0.0
        }

        if context:
            features["context_relevance"] = self._calculate_context_relevance(item, context)

        return features

    def _extract_frequency_features(self, item: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Extract frequency-based features"""
        # Check how often user interacted with similar items
        similar_interactions = 0
        for interaction in user_profile.get("interaction_history", []):
            if interaction.get("category") == item.get("category"):
                similar_interactions += 1

        total_interactions = len(user_profile.get("interaction_history", [])) or 1
        return similar_interactions / total_interactions

    def _extract_recency_features(self, item: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Extract recency-based features"""
        return self._calculate_recency(item)

    def _extract_similarity_features(self, item: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Extract similarity-based features"""
        user_vector = user_profile.get("feature_vector", [0] * 10)
        item_vector = item.get("features", [0] * 10)
        return self._cosine_similarity(user_vector, item_vector)

    def _extract_popularity_features(self, item: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Extract popularity-based features"""
        return item.get("popularity", 0.5)

    def _calculate_user_similarity(self, user_profile: Dict[str, Any], item: Dict[str, Any]) -> float:
        """Calculate similarity between users based on item interactions"""
        # Simplified similarity calculation
        return random.random() * 0.8 + 0.2  # Random value between 0.2 and 1.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a ** 2 for a in vec1))
        norm2 = math.sqrt(sum(b ** 2 for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_context_relevance(self, item: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate how relevant an item is to the current context"""
        relevance = 0.0

        # Check category match
        if context.get("category") == item.get("category"):
            relevance += 0.5

        # Check tag overlap
        context_tags = set(context.get("tags", []))
        item_tags = set(item.get("tags", []))
        if context_tags and item_tags:
            overlap = len(context_tags & item_tags) / len(context_tags | item_tags)
            relevance += overlap * 0.5

        return min(relevance, 1.0)

    def _calculate_recency(self, item: Dict[str, Any]) -> float:
        """Calculate recency score for an item"""
        try:
            created_at = datetime.fromisoformat(item.get("created_at", datetime.now().isoformat()))
            days_old = (datetime.now() - created_at).days

            # Exponential decay
            return math.exp(-days_old / 30)  # Decay over 30 days
        except:
            return 0.5

    def _apply_feature_weights(self, base_score: float, feature_scores: Dict[str, float]) -> float:
        """Apply feature weights to calculate final score"""
        weights = self.config["feature_weights"]
        weighted_sum = base_score * 0.5  # Base score contribution

        for feature, score in feature_scores.items():
            weight = weights.get(feature, 0.1)
            weighted_sum += score * weight * 0.5

        return min(weighted_sum, 1.0)

    def _simulate_ml_prediction(self, features: Dict[str, Any]) -> float:
        """Simulate ML model prediction"""
        # In production, this would use a trained model
        # For now, use a weighted combination of features

        score = 0.0
        score += sum(features.get("item_features", [])) * 0.2
        score += sum(features.get("user_features", [])) * 0.2
        score += features.get("item_popularity", 0) * 0.2
        score += features.get("recency_score", 0) * 0.2
        score += features.get("category_match", 0) * 0.1
        score += features.get("context_relevance", 0) * 0.1

        # Normalize
        return min(score / 2, 1.0)

    def _apply_personalization(
        self, score: float, user_profile: Dict[str, Any], level: str
    ) -> float:
        """Apply personalization based on user profile"""
        personalization_factor = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.5
        }.get(level, 0.3)

        # Calculate user-specific adjustment
        user_adjustment = len(user_profile.get("preferences", {})) * 0.05
        user_adjustment = min(user_adjustment, personalization_factor)

        return score * (1 - personalization_factor) + user_adjustment

    def _calculate_confidence(self, features: Dict[str, Any], score: float) -> float:
        """Calculate confidence in the recommendation"""
        # Base confidence on score
        confidence = score

        # Adjust based on feature quality
        if features.get("interaction_count", 0) < 5:
            confidence *= 0.8  # Lower confidence for new users

        if features.get("context_relevance", 0) > 0.7:
            confidence *= 1.1  # Higher confidence with strong context match

        return min(confidence, 1.0)

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached recommendations are still valid"""
        if "timestamp" not in cached_data:
            return False

        cache_age = (datetime.now() - cached_data["timestamp"]).seconds
        return cache_age < 300  # 5 minutes cache

    def _update_metrics(self, algorithm: str, recommendations: List[Dict[str, Any]]) -> None:
        """Update recommendation metrics"""
        self.model_metrics["total_recommendations"] += len(recommendations)
        self.model_metrics["algorithm_usage"][algorithm] += 1

        if recommendations:
            avg_confidence = sum(r["confidence"] for r in recommendations) / len(recommendations)
            # Update running average
            current_avg = self.model_metrics["average_confidence"]
            total = self.model_metrics["total_recommendations"]
            self.model_metrics["average_confidence"] = (
                (current_avg * (total - len(recommendations)) + avg_confidence * len(recommendations)) / total
            )

    # Hook handlers
    async def on_pre_recommendation(self, context: HookContext) -> HookContext:
        """Hook handler for pre-recommendation"""
        user_id = context.get("user_id")
        request_context = context.get("context")

        if user_id:
            # Generate custom recommendations
            recommendations = await self.generate_recommendations(
                user_id, request_context
            )

            # Add to context for potential modification by other plugins
            context.set("custom_recommendations", recommendations)

        return context

    async def on_post_recommendation(self, context: HookContext) -> HookContext:
        """Hook handler for post-recommendation"""
        recommendations = context.get("recommendations", [])
        user_id = context.get("user_id")

        if recommendations and user_id:
            # Track interaction for learning
            self.interaction_history.append({
                "user_id": user_id,
                "recommendations": [r.get("item", {}).get("id") for r in recommendations],
                "timestamp": datetime.now().isoformat()
            })

            # Update user profile
            if user_id in self.user_profiles:
                profile = self.user_profiles[user_id]
                profile["interaction_history"].extend(recommendations[:3])  # Top 3

        return context

    async def on_command_check(self, context: HookContext) -> HookContext:
        """Hook handler for command processing"""
        command = context.get("command", "")

        if command.startswith("recommend"):
            parts = command.split()
            if len(parts) >= 2:
                user_id = parts[1] if len(parts) > 1 else "default"
                algorithm = parts[2] if len(parts) > 2 else self.config["algorithm"]

                # Override algorithm for this request
                original_algorithm = self.config["algorithm"]
                self.config["algorithm"] = algorithm

                recommendations = await self.generate_recommendations(user_id)

                # Restore original algorithm
                self.config["algorithm"] = original_algorithm

                context.set("recommendations", recommendations)

        return context

    def get_recommendation_metrics(self) -> Dict[str, Any]:
        """Get recommendation system metrics"""
        return {
            "metrics": self.model_metrics,
            "config": {
                "algorithm": self.config["algorithm"],
                "min_confidence": self.config["min_confidence"],
                "max_recommendations": self.config["max_recommendations"],
                "personalization_level": self.config["personalization_level"]
            },
            "cache_size": len(self.recommendation_cache),
            "user_profiles": len(self.user_profiles)
        }


# For direct testing
if __name__ == "__main__":
    async def test_plugin():
        """Test the Custom Recommender plugin"""
        plugin = CustomRecommenderPlugin({
            "algorithm": "hybrid",
            "min_confidence": 0.5,
            "max_recommendations": 5,
            "personalization_level": "high"
        })

        if await plugin.initialize():
            # Test recommendation generation
            recommendations = await plugin.generate_recommendations(
                user_id="test_user",
                context={"category": "task", "tags": ["urgent"]}
            )

            print(f"Generated {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['item']['name']} (confidence: {rec['confidence']:.2f})")
                print(f"   Method: {rec['method']}")
                print(f"   Explanation: {rec['explanation']}")

            # Get metrics
            metrics = plugin.get_recommendation_metrics()
            print(f"\nMetrics: {json.dumps(metrics, indent=2)}")

            await plugin.shutdown()

    # Run test
    asyncio.run(test_plugin())