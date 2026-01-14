"""
负载测试

验证系统在不同负载下的表现
"""

import pytest
import requests
import time
import threading
import queue
from typing import List


@pytest.mark.performance
class TestAPILoad:
    """
    API 负载测试
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

    def test_low_load(self, api_base_url, wait_for_service):
        """
        低负载测试：10 请求/秒

        验证：响应时间 < 100ms
        """
        print("\n⚡ 低负载测试：10 请求/秒")

        num_requests = 50
        interval = 0.1  # 100ms = 10 req/s

        response_times = []

        for i in range(num_requests):
            start_time = time.time()

            response = requests.get(f"{api_base_url}/status")

            elapsed_time = time.time() - start_time
            response_times.append(elapsed_time)

            assert response.status_code == 200

            time.sleep(interval)

        # 统计
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 最大响应时间: {max_time*1000:.2f}ms")
        print(f"✅ 最小响应时间: {min_time*1000:.2f}ms")

        # 验证
        assert avg_time < 0.1  # 平均 < 100ms

    def test_medium_load(self, api_base_url, wait_for_service):
        """
        中等负载测试：50 请求/秒

        验证：响应时间 < 200ms
        """
        print("\n⚡ 中等负载测试：50 请求/秒")

        num_requests = 100
        interval = 0.02  # 20ms = 50 req/s

        response_times = []

        for i in range(num_requests):
            start_time = time.time()

            response = requests.get(f"{api_base_url}/status")

            elapsed_time = time.time() - start_time
            response_times.append(elapsed_time)

            assert response.status_code == 200

            time.sleep(interval)

        # 统计
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 最大响应时间: {max_time*1000:.2f}ms")
        print(f"✅ 最小响应时间: {min_time*1000:.2f}ms")

        # 验证
        assert avg_time < 0.2  # 平均 < 200ms

    def test_high_load(self, api_base_url, wait_for_service):
        """
        高负载测试：100 请求/秒

        验证：响应时间 < 500ms
        """
        print("\n⚡ 高负载测试：100 请求/秒")

        num_requests = 200
        interval = 0.01  # 10ms = 100 req/s

        response_times = []

        for i in range(num_requests):
            start_time = time.time()

            response = requests.get(f"{api_base_url}/status")

            elapsed_time = time.time() - start_time
            response_times.append(elapsed_time)

            assert response.status_code == 200

            time.sleep(interval)

        # 统计
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 最大响应时间: {max_time*1000:.2f}ms")
        print(f"✅ 最小响应时间: {min_time*1000:.2f}ms")

        # 验证
        assert avg_time < 0.5  # 平均 < 500ms


@pytest.mark.performance
class TestSSELoad:
    """
    SSE 负载测试
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

    def test_multiple_sse_connections(self, api_base_url, wait_for_service):
        """
        多连接测试：10 个并发 SSE 连接

        验证：所有连接都能正常接收消息
        """
        print("\n🌊 多 SSE 连接测试：10 个并发连接")

        num_connections = 10
        connections = []

        # 建立多个连接
        for i in range(num_connections):
            response = requests.get(
                f"{api_base_url}/api/stream/messages",
                stream=True,
                timeout=30
            )

            assert response.status_code == 200
            connections.append(response)

            print(f"✅ 连接 {i+1} 已建立")

        # 等待 5 秒
        time.sleep(5)

        # 关闭所有连接
        for i, response in enumerate(connections):
            response.close()
            print(f"✅ 连接 {i+1} 已关闭")

        print(f"✅ 所有 {num_connections} 个连接正常")

    def test_sse_message_throughput(self, api_base_url, wait_for_service):
        """
        SSE 消息吞吐量测试

        验证：可以处理 100 消息/分钟
        """
        print("\n📊 SSE 消息吞吐量测试")

        response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=60
        )

        assert response.status_code == 200

        # 收集消息
        messages_received = []
        start_time = time.time()
        duration = 30  # 30 秒

        for line in response.iter_lines():
            if time.time() - start_time > duration:
                break

            if line and line.decode('utf-8').startswith("data: "):
                messages_received.append(line)

        response.close()

        # 计算吞吐量
        elapsed_time = time.time() - start_time
        messages_per_minute = len(messages_received) / elapsed_time * 60

        print(f"✅ 收到消息数: {len(messages_received)}")
        print(f"✅ 吞吐量: {messages_per_minute:.2f} 消息/分钟")

        # 验证
        assert messages_per_minute >= 100  # 至少 100 消息/分钟


@pytest.mark.performance
class TestConcurrentRequests:
    """
    并发请求测试
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

    def make_request(self, api_base_url: str, result_queue: queue.Queue):
        """
        执行单个请求
        """
        try:
            start_time = time.time()
            response = requests.get(f"{api_base_url}/status", timeout=10)
            elapsed_time = time.time() - start_time

            result_queue.put({
                "status_code": response.status_code,
                "elapsed_time": elapsed_time,
                "success": response.status_code == 200
            })
        except Exception as e:
            result_queue.put({
                "status_code": None,
                "elapsed_time": None,
                "success": False,
                "error": str(e)
            })

    def test_concurrent_users(self, api_base_url, wait_for_service):
        """
        并发用户测试：10 个并发用户

        验证：所有请求都成功
        """
        print("\n👥 并发用户测试：10 个并发用户")

        num_users = 10
        requests_per_user = 10

        result_queue = queue.Queue()
        threads = []

        # 创建线程
        for i in range(num_users):
            for j in range(requests_per_user):
                thread = threading.Thread(
                    target=self.make_request,
                    args=(api_base_url, result_queue)
                )
                threads.append(thread)

        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # 统计
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        avg_time = sum(r["elapsed_time"] for r in results if r["elapsed_time"]) / len(results)

        print(f"✅ 总请求数: {len(results)}")
        print(f"✅ 成功: {successful}")
        print(f"✅ 失败: {failed}")
        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")
        print(f"✅ 总耗时: {total_time:.2f}秒")

        # 验证
        assert successful == len(results)  # 所有请求都成功

    def test_spike_load(self, api_base_url, wait_for_service):
        """
        尖峰负载测试：瞬间 50 个并发请求

        验证：系统可以处理尖峰
        """
        print("\n⚡ 尖峰负载测试：瞬间 50 个并发请求")

        num_requests = 50
        result_queue = queue.Queue()
        threads = []

        # 创建线程
        for i in range(num_requests):
            thread = threading.Thread(
                target=self.make_request,
                args=(api_base_url, result_queue)
            )
            threads.append(thread)

        # 同时启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # 统计
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        print(f"✅ 总请求数: {len(results)}")
        print(f"✅ 成功: {successful}")
        print(f"✅ 失败: {failed}")
        print(f"✅ 总耗时: {total_time:.2f}秒")

        # 验证
        assert successful >= num_requests * 0.95  # 至少 95% 成功率


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
