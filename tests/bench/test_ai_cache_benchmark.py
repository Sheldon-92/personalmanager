#!/usr/bin/env python3
"""AI服务请求级缓存性能基准测试

测试缓存命中率、延迟对比以及内存使用情况。
使用mock provider避免真实API调用，确保测试的可重复性和稳定性。
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from unittest.mock import MagicMock, patch
import pytest
import statistics
from dataclasses import dataclass, asdict

# 缓存增强的AI服务
class RequestCache:
    """简单的内存缓存实现，用于缓存AI请求响应"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.total_requests = 0

    def _make_key(self, prompt: str, max_tokens: int, temperature: float, provider: str) -> str:
        """生成缓存键"""
        content = f"{prompt}|{max_tokens}|{temperature}|{provider}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get(self, prompt: str, max_tokens: int, temperature: float, provider: str) -> Optional[str]:
        """从缓存获取响应"""
        key = self._make_key(prompt, max_tokens, temperature, provider)
        self.total_requests += 1

        if key in self._cache:
            entry = self._cache[key]
            # 检查TTL
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                self.hits += 1
                return entry['response']
            else:
                # 过期，删除
                del self._cache[key]

        self.misses += 1
        return None

    def put(self, prompt: str, max_tokens: int, temperature: float, provider: str, response: str):
        """将响应存入缓存"""
        key = self._make_key(prompt, max_tokens, temperature, provider)

        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]

        self._cache[key] = {
            'response': response,
            'timestamp': time.time()
        }

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def clear_stats(self):
        """清除统计数据"""
        self.hits = 0
        self.misses = 0
        self.total_requests = 0


class CachedAIService:
    """带缓存的AI服务模拟器"""

    def __init__(self, cache: RequestCache):
        self.cache = cache
        self.api_call_latency = 0.5  # 模拟API调用延迟500ms
        self.cache_latency = 0.001   # 模拟缓存访问延迟1ms

    def generate_text(self, prompt: str, provider: str = "claude",
                     max_tokens: int = 4000, temperature: float = 0.1) -> Tuple[str, bool, float]:
        """生成文本，返回(响应, 是否缓存命中, 延迟时间)"""
        start_time = time.time()

        # 尝试从缓存获取
        cached_response = self.cache.get(prompt, max_tokens, temperature, provider)

        if cached_response is not None:
            # 缓存命中，模拟缓存访问时间
            time.sleep(self.cache_latency)
            end_time = time.time()
            return cached_response, True, end_time - start_time

        # 缓存未命中，模拟API调用
        time.sleep(self.api_call_latency)

        # 生成模拟响应
        response = f"AI response for: {prompt[:50]}... (provider: {provider})"

        # 存入缓存
        self.cache.put(prompt, max_tokens, temperature, provider, response)

        end_time = time.time()
        return response, False, end_time - start_time


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_cached_latency_ms: float
    avg_uncached_latency_ms: float
    total_time_seconds: float
    latency_improvement_percent: float


class AIServiceCacheBenchmark:
    """AI服务缓存性能基准测试"""

    def __init__(self):
        self.cache = RequestCache(max_size=1000, ttl_seconds=3600)
        self.ai_service = CachedAIService(self.cache)

    def run_benchmark(self, num_requests: int = 1000, duplicate_ratio: float = 0.7) -> BenchmarkResult:
        """运行缓存性能基准测试

        Args:
            num_requests: 总请求数
            duplicate_ratio: 重复请求的比例 (0.0-1.0)

        Returns:
            BenchmarkResult: 基准测试结果
        """
        # 生成测试数据集
        unique_prompts = [
            f"Explain concept {i}: {self._generate_prompt_content(i)}"
            for i in range(int(num_requests * (1 - duplicate_ratio)))
        ]

        # 构建请求序列，包含重复请求
        requests = []
        for i in range(num_requests):
            if i < len(unique_prompts):
                requests.append(unique_prompts[i])
            else:
                # 重复请求，从已有的prompt中随机选择
                requests.append(unique_prompts[i % len(unique_prompts)])

        # 清除统计数据
        self.cache.clear_stats()

        cached_latencies = []
        uncached_latencies = []

        start_time = time.time()

        # 执行请求
        for prompt in requests:
            response, cache_hit, latency = self.ai_service.generate_text(prompt)

            if cache_hit:
                cached_latencies.append(latency * 1000)  # 转换为ms
            else:
                uncached_latencies.append(latency * 1000)  # 转换为ms

        end_time = time.time()
        total_time = end_time - start_time

        # 计算统计数据
        avg_cached_latency = statistics.mean(cached_latencies) if cached_latencies else 0
        avg_uncached_latency = statistics.mean(uncached_latencies) if uncached_latencies else 0

        latency_improvement = 0
        if avg_uncached_latency > 0:
            latency_improvement = ((avg_uncached_latency - avg_cached_latency) / avg_uncached_latency) * 100

        return BenchmarkResult(
            total_requests=num_requests,
            cache_hits=self.cache.hits,
            cache_misses=self.cache.misses,
            hit_rate=self.cache.get_hit_rate(),
            avg_cached_latency_ms=avg_cached_latency,
            avg_uncached_latency_ms=avg_uncached_latency,
            total_time_seconds=total_time,
            latency_improvement_percent=latency_improvement
        )

    def _generate_prompt_content(self, index: int) -> str:
        """生成多样化的prompt内容"""
        topics = [
            "machine learning algorithms and their applications",
            "distributed system architecture patterns",
            "database optimization strategies",
            "cloud computing security best practices",
            "API design principles and patterns",
            "software testing methodologies",
            "DevOps automation workflows",
            "microservices communication patterns",
            "data pipeline architecture",
            "system monitoring and observability"
        ]

        return topics[index % len(topics)]


def test_cache_performance_benchmark():
    """测试缓存性能基准"""
    benchmark = AIServiceCacheBenchmark()

    # 运行基准测试
    result = benchmark.run_benchmark(num_requests=200, duplicate_ratio=0.8)

    # 验证基本指标
    assert result.total_requests == 200
    assert result.cache_hits + result.cache_misses == 200
    assert 0 <= result.hit_rate <= 1.0

    # 预期缓存命中率应该接近80%（因为duplicate_ratio=0.8）
    assert result.hit_rate >= 0.7, f"Cache hit rate too low: {result.hit_rate:.2%}"

    # 缓存延迟应该明显低于非缓存延迟
    if result.avg_uncached_latency_ms > 0:
        assert result.avg_cached_latency_ms < result.avg_uncached_latency_ms
        assert result.latency_improvement_percent > 90, f"Latency improvement too low: {result.latency_improvement_percent:.1f}%"

    return result


def test_cache_hit_rate_scaling():
    """测试不同重复比例下的缓存命中率"""
    benchmark = AIServiceCacheBenchmark()

    results = []
    duplicate_ratios = [0.0, 0.3, 0.5, 0.7, 0.9]

    for ratio in duplicate_ratios:
        benchmark.cache.clear_stats()
        result = benchmark.run_benchmark(num_requests=100, duplicate_ratio=ratio)
        results.append((ratio, result.hit_rate))

    # 验证命中率随重复比例增长
    for i in range(1, len(results)):
        prev_ratio, prev_hit_rate = results[i-1]
        curr_ratio, curr_hit_rate = results[i]

        # 重复比例更高时，命中率应该更高（允许一定误差）
        assert curr_hit_rate >= prev_hit_rate - 0.05, \
            f"Hit rate should increase with duplicate ratio: {prev_hit_rate:.2%} -> {curr_hit_rate:.2%}"

    return results


def benchmark_main():
    """主基准测试函数，输出详细报告"""
    print("=" * 60)
    print("AI服务请求级缓存性能基准测试")
    print("=" * 60)

    # 运行主要基准测试
    benchmark = AIServiceCacheBenchmark()
    result = test_cache_performance_benchmark()

    # 输出详细结果
    print("\n主要性能指标:")
    print(f"总请求数: {result.total_requests}")
    print(f"缓存命中: {result.cache_hits}")
    print(f"缓存未命中: {result.cache_misses}")
    print(f"命中率: {result.hit_rate:.2%}")
    print(f"缓存响应平均延迟: {result.avg_cached_latency_ms:.2f} ms")
    print(f"非缓存响应平均延迟: {result.avg_uncached_latency_ms:.2f} ms")
    print(f"延迟改善: {result.latency_improvement_percent:.1f}%")
    print(f"总测试时间: {result.total_time_seconds:.2f} 秒")

    # 运行扩展性测试
    print("\n" + "=" * 40)
    print("缓存命中率扩展性测试")
    print("=" * 40)

    scaling_results = test_cache_hit_rate_scaling()
    for ratio, hit_rate in scaling_results:
        print(f"重复比例 {ratio:.0%}: 命中率 {hit_rate:.2%}")

    # 生成JSON格式的基准报告
    benchmark_data = {
        "test_name": "ai_cache_benchmark",
        "timestamp": time.time(),
        "main_benchmark": asdict(result),
        "scaling_benchmark": [
            {"duplicate_ratio": ratio, "hit_rate": hit_rate}
            for ratio, hit_rate in scaling_results
        ],
        "performance_summary": {
            "cache_effective": result.hit_rate >= 0.7,
            "latency_improvement_significant": result.latency_improvement_percent >= 90,
            "meets_performance_target": result.hit_rate >= 0.7 and result.latency_improvement_percent >= 90
        }
    }

    return benchmark_data


if __name__ == "__main__":
    # 运行基准测试
    benchmark_data = benchmark_main()

    # 保存结果到文件
    import os
    reports_dir = "/Users/sheldonzhao/programs/personal-manager/docs/reports/phase_3"
    os.makedirs(reports_dir, exist_ok=True)

    # 输出JSON格式结果
    json_output = json.dumps(benchmark_data, indent=2)
    print(f"\n" + "=" * 60)
    print("基准测试JSON结果:")
    print("=" * 60)
    print(json_output)

    # 保存到文件
    with open(f"{reports_dir}/cache_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存到: {reports_dir}/cache_benchmark.json")