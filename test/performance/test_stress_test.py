"""
压力测试

验证系统在极端条件下的稳定性和恢复能力
"""

import pytest
import requests
import time
import threading
import queue
import psutil
import os


@pytest.mark.performance
@pytest.mark.stress
class TestAPIStress:
    """
    API 压力测试
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

    def make_request(self, api_base_url: str, result_queue: queue.Queue, duration: int = 60):
        """
        持续发送请求
        """
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                response = requests.get(f"{api_base_url}/status", timeout=5)
                result_queue.put({
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                result_queue.put({
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                })

            time.sleep(0.1)  # 10 req/s per thread

    def test_sustained_high_load(self, api_base_url, wait_for_service):
        """
        持续高负载测试：10 个线程，持续 1 分钟

        验证：系统在持续高负载下保持稳定
        """
        print("\n🔥 持续高负载测试：10 个线程 × 1 分钟")

        num_threads = 10
        duration = 60

        result_queue = queue.Queue()
        threads = []

        # 创建线程
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.make_request,
                args=(api_base_url, result_queue, duration)
            )
            threads.append(thread)

        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()

        # 监控进度
        while any(t.is_alive() for t in threads):
            time.sleep(10)
            elapsed = time.time() - start_time
            print(f"⏱️  已运行: {elapsed:.0f} 秒")

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
        success_rate = successful / len(results) * 100

        print(f"\n✅ 总请求数: {len(results)}")
        print(f"✅ 成功: {successful}")
        print(f"✅ 失败: {failed}")
        print(f"✅ 成功率: {success_rate:.2f}%")
        print(f"✅ 总耗时: {total_time:.2f}秒")

        # 验证
        assert success_rate >= 99  # 成功率应该 >= 99%

    def test_burst_load(self, api_base_url, wait_for_service):
        """
        突发负载测试：多个突发周期

        验证：系统可以处理负载波动
        """
        print("\n⚡ 突发负载测试")

        num_bursts = 5
        requests_per_burst = 100

        for burst in range(num_bursts):
            print(f"💥 突发 {burst + 1}/{num_bursts}")

            # 发送突发请求
            for i in range(requests_per_burst):
                response = requests.get(f"{api_base_url}/status", timeout=10)
                assert response.status_code == 200

            # 休息
            time.sleep(5)

        print(f"✅ 突发负载测试完成")


@pytest.mark.performance
@pytest.mark.stress
class TestResourceStress:
    """
    资源压力测试
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

    def get_process_metrics(self):
        """
        获取当前进程资源指标
        """
        process = psutil.Process(os.getpid())

        return {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
        }

    def test_memory_stress(self, api_base_url, wait_for_service):
        """
        内存压力测试

        验证：内存占用稳定，无泄漏
        """
        print("\n💾 内存压力测试")

        num_requests = 1000
        memory_samples = []

        # 获取初始内存
        initial_memory = self.get_process_metrics()["memory_mb"]
        print(f"📊 初始内存: {initial_memory:.2f}MB")

        # 发送大量请求
        for i in range(num_requests):
            response = requests.get(f"{api_base_url}/status", timeout=10)
            assert response.status_code == 200

            # 每 100 个请求采样一次
            if i % 100 == 0:
                metrics = self.get_process_metrics()
                memory_samples.append(metrics["memory_mb"])
                print(f"📊 进度: {i}/{num_requests}, 内存: {metrics['memory_mb']:.2f}MB")

        # 获取最终内存
        final_memory = self.get_process_metrics()["memory_mb"]
        memory_growth = final_memory - initial_memory

        print(f"\n📊 初始内存: {initial_memory:.2f}MB")
        print(f"📊 最终内存: {final_memory:.2f}MB")
        print(f"📊 内存增长: {memory_growth:.2f}MB")

        # 验证：内存增长应该 < 100MB
        assert memory_growth < 100

    def test_cpu_stress(self, api_base_url, wait_for_service):
        """
        CPU 压力测试

        验证：CPU 占用合理
        """
        print("\n🖥️  CPU 压力测试")

        duration = 30  # 30 秒

        print(f"⏱️  监控 CPU 占用（{duration}秒）...")

        cpu_samples = []

        # 监控 CPU
        start_time = time.time()

        while time.time() - start_time < duration:
            # 发送请求
            response = requests.get(f"{api_base_url}/status", timeout=10)
            assert response.status_code == 200

            # 采样 CPU
            cpu_percent = self.get_process_metrics()["cpu_percent"]
            cpu_samples.append(cpu_percent)

            time.sleep(0.5)

        # 统计
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)

        print(f"\n📊 平均 CPU: {avg_cpu:.2f}%")
        print(f"📊 最大 CPU: {max_cpu:.2f}%")

        # 验证：平均 CPU 应该 < 80%
        assert avg_cpu < 80


@pytest.mark.performance
@pytest.mark.stress
class TestConnectionStress:
    """
    连接压力测试
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

    def test_max_sse_connections(self, api_base_url, wait_for_service):
        """
        最大 SSE 连接测试

        验证：系统可以处理多个并发 SSE 连接
        """
        print("\n🔌 最大 SSE 连接测试")

        num_connections = 50
        connections = []

        try:
            # 建立连接
            for i in range(num_connections):
                response = requests.get(
                    f"{api_base_url}/api/stream/messages",
                    stream=True,
                    timeout=60
                )

                assert response.status_code == 200
                connections.append(response)

                if (i + 1) % 10 == 0:
                    print(f"✅ 已建立 {i + 1} 个连接")

            # 等待 10 秒
            time.sleep(10)

            print(f"✅ 成功建立 {num_connections} 个并发 SSE 连接")

        finally:
            # 关闭所有连接
            for response in connections:
                response.close()

            print(f"✅ 所有连接已关闭")

    def test_connection_reuse(self, api_base_url, wait_for_service):
        """
        连接复用测试

        验证：HTTP 连接可以正确复用
        """
        print("\n🔄 连接复用测试")

        # 创建 Session（启用连接池）
        session = requests.Session()

        num_requests = 100

        start_time = time.time()

        for i in range(num_requests):
            response = session.get(f"{api_base_url}/status", timeout=10)
            assert response.status_code == 200

        total_time = time.time() - start_time

        session.close()

        avg_time = total_time / num_requests

        print(f"✅ 总请求数: {num_requests}")
        print(f"✅ 总耗时: {total_time:.2f}秒")
        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")

        # 验证：连接复用应该提高性能
        assert avg_time < 0.1  # 平均 < 100ms


@pytest.mark.performance
@pytest.mark.stress
class TestErrorRecovery:
    """
    错误恢复测试
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

    def test_service_restart_during_load(self, api_base_url, wait_for_service):
        """
        负载下重启测试

        验证：服务重启后可以恢复处理请求
        """
        print("\n🔄 负载下重启测试")

        # 启动负载
        def send_requests(result_queue):
            while True:
                try:
                    response = requests.get(f"{api_base_url}/status", timeout=5)
                    result_queue.put({
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                except:
                    result_queue.put({
                        "status_code": None,
                        "success": False
                    })
                time.sleep(0.1)

        result_queue = queue.Queue()
        threads = []

        # 启动负载线程
        for i in range(5):
            thread = threading.Thread(target=send_requests, args=(result_queue,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        print("✅ 负载已启动")

        # 运行 5 秒
        time.sleep(5)

        # 重启服务
        print("🔄 重启服务...")
        response = requests.post(f"{api_base_url}/api/restart")
        assert response.status_code == 200

        # 等待服务恢复
        time.sleep(10)

        # 验证服务恢复
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200

        print("✅ 服务已恢复")

        # 再运行 5 秒
        time.sleep(5)

        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # 统计后期的成功率
        recent_results = results[-50:]  # 最近 50 个请求
        success_rate = sum(1 for r in recent_results if r["success"]) / len(recent_results) * 100

        print(f"✅ 恢复后成功率: {success_rate:.2f}%")

        # 验证：恢复后成功率应该 >= 90%
        assert success_rate >= 90


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
