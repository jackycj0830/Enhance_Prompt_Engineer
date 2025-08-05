"""
API性能测试
"""

import asyncio
import time
import statistics
from typing import List, Dict
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.results: Dict[str, List[float]] = {}
    
    def record_time(self, test_name: str, execution_time: float):
        """记录执行时间"""
        if test_name not in self.results:
            self.results[test_name] = []
        self.results[test_name].append(execution_time)
    
    def get_statistics(self, test_name: str) -> Dict:
        """获取统计信息"""
        if test_name not in self.results:
            return {}
        
        times = self.results[test_name]
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "p95": self._percentile(times, 95),
            "p99": self._percentile(times, 99)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def print_report(self):
        """打印性能报告"""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*80)
        
        for test_name, times in self.results.items():
            stats = self.get_statistics(test_name)
            print(f"\n{test_name}:")
            print(f"  Count: {stats['count']}")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  Min: {stats['min']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
            print(f"  P95: {stats['p95']:.2f}ms")
            print(f"  P99: {stats['p99']:.2f}ms")
            print(f"  Std Dev: {stats['std_dev']:.2f}ms")


# 全局基准测试实例
benchmark = PerformanceBenchmark()


@pytest.mark.performance
class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.mark.asyncio
    async def test_auth_login_performance(self, integration_async_client: AsyncClient, 
                                        integration_user):
        """测试登录API性能"""
        login_data = {
            "username": integration_user.username,
            "password": "secret"
        }
        
        # 预热
        await integration_async_client.post("/api/v1/auth/login", data=login_data)
        
        # 性能测试
        iterations = 100
        for i in range(iterations):
            start_time = time.time()
            
            response = await integration_async_client.post("/api/v1/auth/login", data=login_data)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # 毫秒
            
            assert response.status_code == 200
            benchmark.record_time("auth_login", execution_time)
        
        # 验证性能要求
        stats = benchmark.get_statistics("auth_login")
        assert stats["mean"] < 100, f"Login API mean response time {stats['mean']:.2f}ms exceeds 100ms"
        assert stats["p95"] < 200, f"Login API P95 response time {stats['p95']:.2f}ms exceeds 200ms"
    
    @pytest.mark.asyncio
    async def test_prompt_list_performance(self, integration_async_client: AsyncClient,
                                         integration_auth_headers):
        """测试提示词列表API性能"""
        # 预热
        await integration_async_client.get("/api/v1/prompts/", headers=integration_auth_headers)
        
        # 性能测试
        iterations = 50
        for i in range(iterations):
            start_time = time.time()
            
            response = await integration_async_client.get("/api/v1/prompts/", headers=integration_auth_headers)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            benchmark.record_time("prompt_list", execution_time)
        
        # 验证性能要求
        stats = benchmark.get_statistics("prompt_list")
        assert stats["mean"] < 150, f"Prompt list API mean response time {stats['mean']:.2f}ms exceeds 150ms"
        assert stats["p95"] < 300, f"Prompt list API P95 response time {stats['p95']:.2f}ms exceeds 300ms"
    
    @pytest.mark.asyncio
    async def test_template_search_performance(self, integration_async_client: AsyncClient):
        """测试模板搜索API性能"""
        # 预热
        await integration_async_client.get("/api/v1/templates/search?q=test")
        
        # 性能测试
        iterations = 30
        search_queries = ["test", "example", "prompt", "template", "ai"]
        
        for i in range(iterations):
            query = search_queries[i % len(search_queries)]
            start_time = time.time()
            
            response = await integration_async_client.get(f"/api/v1/templates/search?q={query}")
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            benchmark.record_time("template_search", execution_time)
        
        # 验证性能要求
        stats = benchmark.get_statistics("template_search")
        assert stats["mean"] < 200, f"Template search API mean response time {stats['mean']:.2f}ms exceeds 200ms"
        assert stats["p95"] < 400, f"Template search API P95 response time {stats['p95']:.2f}ms exceeds 400ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, integration_async_client: AsyncClient,
                                                 integration_auth_headers):
        """测试并发请求性能"""
        async def make_request():
            start_time = time.time()
            response = await integration_async_client.get("/api/v1/templates/", headers=integration_auth_headers)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            return execution_time
        
        # 并发测试
        concurrent_requests = 20
        tasks = [make_request() for _ in range(concurrent_requests)]
        
        start_time = time.time()
        execution_times = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # 记录结果
        for exec_time in execution_times:
            benchmark.record_time("concurrent_requests", exec_time)
        
        # 验证性能要求
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        assert avg_time < 300, f"Concurrent requests average time {avg_time:.2f}ms exceeds 300ms"
        assert max_time < 1000, f"Concurrent requests max time {max_time:.2f}ms exceeds 1000ms"
        assert total_time < 5000, f"Total concurrent execution time {total_time:.2f}ms exceeds 5000ms"
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_load(self, integration_async_client: AsyncClient,
                                          integration_auth_headers):
        """测试负载下的内存使用"""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # 记录初始内存
        gc.collect()  # 强制垃圾回收
        initial_memory = process.memory_info().rss
        
        # 执行大量请求
        iterations = 100
        for i in range(iterations):
            response = await integration_async_client.get("/api/v1/templates/", headers=integration_auth_headers)
            assert response.status_code == 200
            
            # 每10次请求检查一次内存
            if i % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # 内存增长不应超过100MB
                assert memory_increase < 100 * 1024 * 1024, \
                    f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"
        
        # 最终内存检查
        gc.collect()
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        print(f"Memory usage: Initial={initial_memory/1024/1024:.2f}MB, "
              f"Final={final_memory/1024/1024:.2f}MB, "
              f"Increase={total_increase/1024/1024:.2f}MB")
        
        # 总内存增长不应超过50MB
        assert total_increase < 50 * 1024 * 1024, \
            f"Total memory increase {total_increase / 1024 / 1024:.2f}MB exceeds 50MB"


@pytest.mark.performance
class TestDatabasePerformance:
    """数据库性能测试"""
    
    @pytest.mark.asyncio
    async def test_query_performance(self, integration_db_session):
        """测试数据库查询性能"""
        from sqlalchemy import text
        
        # 测试简单查询
        iterations = 100
        for i in range(iterations):
            start_time = time.time()
            
            result = await integration_db_session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            benchmark.record_time("db_simple_query", execution_time)
        
        # 验证性能要求
        stats = benchmark.get_statistics("db_simple_query")
        assert stats["mean"] < 10, f"Database query mean time {stats['mean']:.2f}ms exceeds 10ms"
        assert stats["p95"] < 20, f"Database query P95 time {stats['p95']:.2f}ms exceeds 20ms"
    
    @pytest.mark.asyncio
    async def test_complex_query_performance(self, integration_db_session):
        """测试复杂查询性能"""
        from sqlalchemy import text
        
        # 测试复杂查询（JOIN查询）
        complex_query = """
        SELECT u.username, COUNT(p.id) as prompt_count, COUNT(a.id) as analysis_count
        FROM users u
        LEFT JOIN prompts p ON u.id = p.user_id
        LEFT JOIN analyses a ON u.id = a.user_id
        GROUP BY u.id, u.username
        ORDER BY prompt_count DESC
        LIMIT 10
        """
        
        iterations = 20
        for i in range(iterations):
            start_time = time.time()
            
            result = await integration_db_session.execute(text(complex_query))
            rows = result.fetchall()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            benchmark.record_time("db_complex_query", execution_time)
        
        # 验证性能要求
        stats = benchmark.get_statistics("db_complex_query")
        assert stats["mean"] < 50, f"Complex query mean time {stats['mean']:.2f}ms exceeds 50ms"
        assert stats["p95"] < 100, f"Complex query P95 time {stats['p95']:.2f}ms exceeds 100ms"


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时打印性能报告"""
    if hasattr(session.config, 'option') and getattr(session.config.option, 'performance', False):
        benchmark.print_report()
