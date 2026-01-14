"""
基准测试

建立系统性能基准，用于对比不同版本或配置
"""

import pytest
import requests
import time
import json
from typing import List, Dict


@pytest.mark.benchmark
class TestAPIBenchmark:
    """
    API 性能基准测试
    """

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8000"

    @pytest.fixture
    def wait_for_service(self, api_base_url):
        """等待服务启动"""
        health_url = f"{api_base_url}/health"

        for _ in range(30):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)

        pytest.skip("API 服务启动超时")

    def benchmark_endpoint(self, url: str, num_requests: int = 100) -> Dict:
        """
        对指定端点进行基准测试

        返回统计信息
        """
        response_times = []

        # 预热
        for _ in range(10):
            requests.get(url, timeout=10)

        # 实际测试
        for _ in range(num_requests):
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            response_times.append(elapsed_time)

        # 统计
        sorted_times = sorted(response_times)

        return {
            "requests": num_requests,
            "min": min(response_times),
            "max": max(response_times),
            "avg": sum(response_times) / len(response_times),
            "median": sorted_times[len(sorted_times) // 2],
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
            "rps": num_requests / sum(response_times)  # requests per second
        }

    def test_benchmark_root(self, api_base_url, wait_for_service):
        """
        基准测试：根路径 /

        基准指标：
        - 平均响应时间 < 10ms
        - P95 < 20ms
        - RPS > 1000
        """
        print("\n📊 基准测试：根路径 /")

        stats = self.benchmark_endpoint(f"{api_base_url}/")

        print(f"✅ 请求数: {stats['requests']}")
        print(f"✅ 最小: {stats['min']*1000:.2f}ms")
        print(f"✅ 最大: {stats['max']*1000:.2f}ms")
        print(f"✅ 平均: {stats['avg']*1000:.2f}ms")
        print(f"✅ 中位数: {stats['median']*1000:.2f}ms")
        print(f"✅ P95: {stats['p95']*1000:.2f}ms")
        print(f"✅ P99: {stats['p99']*1000:.2f}ms")
        print(f"✅ RPS: {stats['rps']:.2f}")

        # 验证基准
        assert stats['avg'] < 0.01  # < 10ms
        assert stats['p95'] < 0.02  # < 20ms
        assert stats['rps'] > 1000  # > 1000 req/s

    def test_benchmark_health(self, api_base_url, wait_for_service):
        """
        基准测试：健康检查 /health

        基准指标：
        - 平均响应时间 < 10ms
        - P95 < 20ms
        - RPS > 1000
        """
        print("\n📊 基准测试：健康检查 /health")

        stats = self.benchmark_endpoint(f"{api_base_url}/health")

        print(f"✅ 请求数: {stats['requests']}")
        print(f"✅ 最小: {stats['min']*1000:.2f}ms")
        print(f"✅ 最大: {stats['max']*1000:.2f}ms")
        print(f"✅ 平均: {stats['avg']*1000:.2f}ms")
        print(f"✅ 中位数: {stats['median']*1000:.2f}ms")
        print(f"✅ P95: {stats['p95']*1000:.2f}ms")
        print(f"✅ P99: {stats['p99']*1000:.2f}ms")
        print(f"✅ RPS: {stats['rps']:.2f}")

        # 验证基准
        assert stats['avg'] < 0.01  # < 10ms
        assert stats['p95'] < 0.02  # < 20ms
        assert stats['rps'] > 1000  # > 1000 req/s

    def test_benchmark_status(self, api_base_url, wait_for_service):
        """
        基准测试：状态端点 /status

        基准指标：
        - 平均响应时间 < 50ms
        - P95 < 100ms
        - RPS > 500
        """
        print("\n📊 基准测试：状态端点 /status")

        stats = self.benchmark_endpoint(f"{api_base_url}/status")

        print(f"✅ 请求数: {stats['requests']}")
        print(f"✅ 最小: {stats['min']*1000:.2f}ms")
        print(f"✅ 最大: {stats['max']*1000:.2f}ms")
        print(f"✅ 平均: {stats['avg']*1000:.2f}ms")
        print(f"✅ 中位数: {stats['median']*1000:.2f}ms")
        print(f"✅ P95: {stats['p95']*1000:.2f}ms")
        print(f"✅ P99: {stats['p99']*1000:.2f}ms")
        print(f"✅ RPS: {stats['rps']:.2f}")

        # 验证基准
        assert stats['avg'] < 0.05  # < 50ms
        assert stats['p95'] < 0.1  # < 100ms
        assert stats['rps'] > 500  # > 500 req/s

    def test_benchmark_screenshot(self, api_base_url, wait_for_service):
        """
        基准测试：截图端点 /api/screenshot

        基准指标：
        - 平均响应时间 < 500ms
        - P95 < 1000ms
        - RPS > 10
        """
        print("\n📊 基准测试：截图端点 /api/screenshot")

        # 截图请求较多，减少测试数量
        stats = self.benchmark_endpoint(f"{api_base_url}/api/screenshot", num_requests=20)

        print(f"✅ 请求数: {stats['requests']}")
        print(f"✅ 最小: {stats['min']*1000:.2f}ms")
        print(f"✅ 最大: {stats['max']*1000:.2f}ms")
        print(f"✅ 平均: {stats['avg']*1000:.2f}ms")
        print(f"✅ 中位数: {stats['median']*1000:.2f}ms")
        print(f"✅ P95: {stats['p95']*1000:.2f}ms")
        print(f"✅ P99: {stats['p99']*1000:.2f}ms")
        print(f"✅ RPS: {stats['rps']:.2f}")

        # 验证基准
        assert stats['avg'] < 0.5  # < 500ms
        assert stats['p95'] < 1.0  # < 1000ms
        assert stats['rps'] > 10  # > 10 req/s


@pytest.mark.benchmark
class TestSSEBenchmark:
    """
    SSE 性能基准测试
    """

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8000"

    @pytest.fixture
    def wait_for_service(self, api_base_url):
        """等待服务启动"""
        health_url = f"{api_base_url}/health"

        for _ in range(30):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)

        pytest.skip("API 服务启动超时")

    def test_sse_connection_latency(self, api_base_url, wait_for_service):
        """
        SSE 连接延迟基准测试

        基准指标：
        - 连接建立时间 < 100ms
        """
        print("\n📊 SSE 连接延迟基准测试")

        num_tests = 10
        connection_times = []

        for _ in range(num_tests):
            start_time = time.time()

            response = requests.get(
                f"{api_base_url}/api/stream/messages",
                stream=True,
                timeout=10
            )

            elapsed_time = time.time() - start_time
            connection_times.append(elapsed_time)

            assert response.status_code == 200
            response.close()

        # 统计
        avg_time = sum(connection_times) / len(connection_times)
        max_time = max(connection_times)

        print(f"✅ 平均连接时间: {avg_time*1000:.2f}ms")
        print(f"✅ 最大连接时间: {max_time*1000:.2f}ms")

        # 验证基准
        assert avg_time < 0.1  # < 100ms

    def test_sse_message_latency(self, api_base_url, wait_for_service):
        """
        SSE 消息延迟基准测试

        基准指标：
        - 消息推送延迟 < 100ms
        """
        print("\n📊 SSE 消息延迟基准测试")

        response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=30
        )

        assert response.status_code == 200

        # 收集消息时间戳
        message_times = []

        start_time = time.time()
        timeout = 30  # 30 秒

        for line in response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    message = json.loads(json_str)

                    # 记录时间戳
                    message_time = time.time()
                    message_times.append(message_time)

                    # 收集 10 条消息即可
                    if len(message_times) >= 10:
                        break

        response.close()

        if len(message_times) >= 2:
            # 计算消息间隔
            intervals = [
                message_times[i] - message_times[i-1]
                for i in range(1, len(message_times))
            ]

            avg_interval = sum(intervals) / len(intervals)

            print(f"✅ 收到消息数: {len(message_times)}")
            print(f"✅ 平均消息间隔: {avg_interval*1000:.2f}ms")

            # 验证基准
            assert avg_interval < 0.1  # < 100ms
        else:
            pytest.skip("未收到足够的消息")


@pytest.mark.benchmark
class TestMemoryBenchmark:
    """
    内存使用基准测试
    """

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8000"

    @pytest.fixture
    def wait_for_service(self, api_base_url):
        """等待服务启动"""
        health_url = f"{api_base_url}/health"

        for _ in range(30):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)

        pytest.skip("API 服务启动超时")

    def test_memory_baseline(self, api_base_url, wait_for_service):
        """
        内存使用基准测试

        基准指标：
        - 空闲时内存 < 200MB
        - 运行 1000 请求后内存增长 < 50MB
        """
        print("\n📊 内存使用基准测试")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())

            # 初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024
            print(f"✅ 初始内存: {initial_memory:.2f}MB")

            # 发送请求
            num_requests = 1000
            for i in range(num_requests):
                response = requests.get(f"{api_base_url}/status", timeout=10)
                assert response.status_code == 200

                if (i + 1) % 200 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"📊 进度: {i+1}/{num_requests}, 内存: {current_memory:.2f}MB")

            # 最终内存
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory

            print(f"✅ 最终内存: {final_memory:.2f}MB")
            print(f"✅ 内存增长: {memory_growth:.2f}MB")

            # 验证基准
            assert initial_memory < 200  # < 200MB
            assert memory_growth < 50  # 增长 < 50MB

        except ImportError:
            pytest.skip("psutil 未安装")


@pytest.mark.benchmark
class TestBenchmarkComparison:
    """
    基准对比测试

    用于对比不同版本或配置的性能
    """

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8000"

    @pytest.fixture
    def wait_for_service(self, api_base_url):
        """等待服务启动"""
        health_url = f"{api_base_url}/health"

        for _ in range(30):
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)

        pytest.skip("API 服务启动超时")

    def run_comprehensive_benchmark(self, api_base_url: str) -> Dict:
        """
        运行综合基准测试

        返回所有基准指标
        """
        endpoints = {
            "root": f"{api_base_url}/",
            "health": f"{api_base_url}/health",
            "status": f"{api_base_url}/status",
            "screenshot": f"{api_base_url}/api/screenshot"
        }

        results = {}

        for name, url in endpoints.items():
            try:
                response_times = []

                # 预热
                for _ in range(10):
                    requests.get(url, timeout=10)

                # 实际测试
                num_requests = 50 if name == "screenshot" else 100
                for _ in range(num_requests):
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    elapsed_time = time.time() - start_time

                    if response.status_code == 200:
                        response_times.append(elapsed_time)

                # 统计
                if response_times:
                    sorted_times = sorted(response_times)
                    results[name] = {
                        "avg": sum(response_times) / len(response_times),
                        "min": min(response_times),
                        "max": max(response_times),
                        "p95": sorted_times[int(len(sorted_times) * 0.95)],
                        "p99": sorted_times[int(len(sorted_times) * 0.99)],
                        "rps": num_requests / sum(response_times)
                    }
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def test_comprehensive_benchmark(self, api_base_url, wait_for_service):
        """
        综合基准测试

        输出所有基准指标，用于版本对比
        """
        print("\n📊 综合基准测试")
        print("=" * 60)

        results = self.run_comprehensive_benchmark(api_base_url)

        for endpoint, stats in results.items():
            print(f"\n📍 端点: {endpoint}")

            if "error" in stats:
                print(f"   ❌ 错误: {stats['error']}")
            else:
                print(f"   平均: {stats['avg']*1000:.2f}ms")
                print(f"   最小: {stats['min']*1000:.2f}ms")
                print(f"   最大: {stats['max']*1000:.2f}ms")
                print(f"   P95: {stats['p95']*1000:.2f}ms")
                print(f"   P99: {stats['p99']*1000:.2f}ms")
                print(f"   RPS: {stats['rps']:.2f}")

        print("\n" + "=" * 60)
        print("✅ 综合基准测试完成")
        print("💡 提示：保存此结果用于版本对比")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
