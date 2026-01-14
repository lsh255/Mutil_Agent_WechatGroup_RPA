"""
API 集成测试

验证 FastAPI 服务器的完整功能
"""

import pytest
import requests
import time
import json
from typing import Generator, Dict, Any


@pytest.fixture(scope="module")
def api_base_url() -> str:
    """
    API 基础 URL
    """
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def wait_for_service(api_base_url: str) -> Generator[None, None, None]:
    """
    等待服务启动

    最多等待 30 秒
    """
    health_url = f"{api_base_url}/health"

    for _ in range(30):
        try:
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                yield
                return
        except:
            pass

        time.sleep(1)

    pytest.skip("API 服务启动超时")


@pytest.mark.integration
@pytest.mark.api
class TestAPIHealth:
    """
    API 健康检查测试
    """

    def test_root_endpoint(self, api_base_url: str, wait_for_service):
        """
        测试根路径端点

        验证返回服务信息
        """
        response = requests.get(f"{api_base_url}/")

        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "version" in data

        print(f"✅ 服务名称: {data['service']}")
        print(f"✅ 版本: {data['version']}")

    def test_health_endpoint(self, api_base_url: str, wait_for_service):
        """
        测试健康检查端点

        验证服务健康状态
        """
        response = requests.get(f"{api_base_url}/health")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

        print(f"✅ 健康状态: {data['status']}")

    def test_status_endpoint(self, api_base_url: str, wait_for_service):
        """
        测试状态端点

        验证返回详细状态信息
        """
        response = requests.get(f"{api_base_url}/status")

        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "producers" in data
        assert "timestamp" in data

        print(f"✅ 服务状态: {data['service']}")
        print(f"✅ 生产者状态: {data['producers']}")


@pytest.mark.integration
@pytest.mark.api
class TestAPIConfiguration:
    """
    API 配置管理测试
    """

    def test_get_config(self, api_base_url: str, wait_for_service):
        """
        测试获取配置

        验证可以读取当前配置
        """
        response = requests.get(f"{api_base_url}/api/config")

        assert response.status_code == 200

        config = response.json()
        assert isinstance(config, dict)

        print(f"✅ 配置键: {list(config.keys())}")

    def test_get_roi(self, api_base_url: str, wait_for_service):
        """
        测试获取 ROI 配置

        验证返回当前 ROI 坐标
        """
        response = requests.get(f"{api_base_url}/api/config/roi")

        assert response.status_code == 200

        roi = response.json()
        assert "left" in roi
        assert "top" in roi
        assert "right" in roi
        assert "bottom" in roi

        print(f"✅ ROI 配置: {roi}")

    def test_update_roi(self, api_base_url: str, wait_for_service):
        """
        测试更新 ROI 配置

        验证可以修改 ROI 坐标
        """
        new_roi = {
            "left": 100,
            "top": 200,
            "right": 500,
            "bottom": 800
        }

        response = requests.post(
            f"{api_base_url}/api/config/roi",
            json=new_roi
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        print(f"✅ ROI 更新成功")

        # 验证更新
        response = requests.get(f"{api_base_url}/api/config/roi")
        updated_roi = response.json()

        assert updated_roi["left"] == new_roi["left"]
        assert updated_roi["top"] == new_roi["top"]
        assert updated_roi["right"] == new_roi["right"]
        assert updated_roi["bottom"] == new_roi["bottom"]

    def test_update_roi_invalid(self, api_base_url: str, wait_for_service):
        """
        测试更新 ROI 配置（无效数据）

        验证参数验证正常工作
        """
        invalid_roi = {
            "left": -1,
            "top": 200,
            "right": 500,
            "bottom": 800
        }

        response = requests.post(
            f"{api_base_url}/api/config/roi",
            json=invalid_roi
        )

        assert response.status_code == 422

        print(f"✅ 参数验证正常")


@pytest.mark.integration
@pytest.mark.api
class TestAPIScreenshot:
    """
    API 截图功能测试
    """

    def test_screenshot(self, api_base_url: str, wait_for_service):
        """
        测试截图功能

        验证可以获取当前屏幕截图
        """
        response = requests.get(f"{api_base_url}/api/screenshot")

        assert response.status_code == 200

        data = response.json()
        assert "screenshot" in data

        print(f"✅ 截图成功")

    def test_screenshot_with_roi(self, api_base_url: str, wait_for_service):
        """
        测试带 ROI 的截图

        验证可以截取指定区域
        """
        # 先设置 ROI
        roi_data = {
            "left": 100,
            "top": 100,
            "right": 500,
            "bottom": 500
        }

        requests.post(
            f"{api_base_url}/api/config/roi",
            json=roi_data
        )

        # 获取截图
        response = requests.get(f"{api_base_url}/api/screenshot")

        assert response.status_code == 200

        data = response.json()
        assert "screenshot" in data

        print(f"✅ ROI 截图成功")


@pytest.mark.integration
@pytest.mark.api
class TestAPIStreaming:
    """
    API 流式推送测试
    """

    def test_sse_connection(self, api_base_url: str, wait_for_service):
        """
        测试 SSE 连接

        验证可以建立 SSE 连接
        """
        response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=10
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")

        # 读取前几行
        lines_received = 0
        for line in response.iter_lines():
            if line:
                lines_received += 1
                if lines_received >= 3:
                    break

        response.close()

        print(f"✅ SSE 连接成功")

    def test_sse_message_format(self, api_base_url: str, wait_for_service):
        """
        测试 SSE 消息格式

        验证消息符合 JSONL 格式
        """
        response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=10
        )

        assert response.status_code == 200

        # 读取消息
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')

                # 验证 data: 前缀
                assert line_str.startswith("data: ")

                # 解析 JSON
                json_str = line_str[6:]  # 移除 "data: " 前缀
                message = json.loads(json_str)

                # 验证必需字段
                assert "id" in message
                assert "type" in message
                assert "sender" in message
                assert "content" in message

                print(f"✅ 消息格式验证通过: {message['type']}")

                # 只验证第一条消息
                break

        response.close()

    def test_sse_message_types(self, api_base_url: str, wait_for_service):
        """
        测试 SSE 消息类型

        验证只推送 text、photo、video 类型
        """
        response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=10
        )

        assert response.status_code == 200

        valid_types = {"text", "photo", "video"}
        messages_checked = 0

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                json_str = line_str[6:]
                message = json.loads(json_str)

                # 验证消息类型
                assert message["type"] in valid_types

                messages_checked += 1
                if messages_checked >= 5:
                    break

        response.close()

        print(f"✅ 消息类型验证通过（检查了 {messages_checked} 条）")


@pytest.mark.integration
@pytest.mark.api
class TestAPIRestart:
    """
    API 重启功能测试
    """

    def test_restart_service(self, api_base_url: str, wait_for_service):
        """
        测试重启服务

        验证可以触发服务重启
        """
        response = requests.post(f"{api_base_url}/api/restart")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        print(f"✅ 重启请求成功")

        # 等待服务恢复
        time.sleep(5)

        # 验证服务恢复
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200

        print(f"✅ 服务已恢复")


@pytest.mark.integration
@pytest.mark.api
class TestAPIWebUI:
    """
    API Web UI 测试
    """

    def test_ui_endpoint(self, api_base_url: str, wait_for_service):
        """
        测试 Web UI 端点

        验证返回 HTML 界面
        """
        response = requests.get(f"{api_base_url}/api/ui")

        assert response.status_code == 200
        assert "text/html" in response.headers["Content-Type"]

        html = response.text
        assert "VNC" in html or "noVNC" in html

        print(f"✅ Web UI 可用")

    def test_vnc_connection_info(self, api_base_url: str, wait_for_service):
        """
        测试 VNC 连接信息

        验证可以获取 VNC 连接配置
        """
        response = requests.get(f"{api_base_url}/api/config")

        assert response.status_code == 200

        config = response.json()

        # 验证 VNC 配置存在
        if "vnc" in config:
            vnc_config = config["vnc"]
            assert "port" in vnc_config or "host" in vnc_config

            print(f"✅ VNC 配置: {vnc_config}")


@pytest.mark.integration
@pytest.mark.api
class TestAPIErrorHandling:
    """
    API 错误处理测试
    """

    def test_invalid_endpoint(self, api_base_url: str, wait_for_service):
        """
        测试无效端点

        验证返回 404 错误
        """
        response = requests.get(f"{api_base_url}/invalid/endpoint")

        assert response.status_code == 404

        print(f"✅ 404 错误处理正常")

    def test_invalid_json(self, api_base_url: str, wait_for_service):
        """
        测试无效 JSON

        验证返回 422 错误
        """
        response = requests.post(
            f"{api_base_url}/api/config/roi",
            json={"invalid": "data"}
        )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

        print(f"✅ JSON 验证错误处理正常")

    def test_method_not_allowed(self, api_base_url: str, wait_for_service):
        """
        测试不允许的方法

        验证返回 405 错误
        """
        response = requests.post(f"{api_base_url}/health")

        assert response.status_code == 405

        print(f"✅ 方法不允许错误处理正常")


@pytest.mark.integration
@pytest.mark.api
class TestAPIPerformance:
    """
    API 性能测试
    """

    def test_response_time(self, api_base_url: str, wait_for_service):
        """
        测试响应时间

        验证 API 响应时间合理
        """
        import time

        start_time = time.time()
        response = requests.get(f"{api_base_url}/status")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 1.0  # 应该 < 1秒

        print(f"✅ 响应时间: {elapsed_time:.3f}秒")

    def test_concurrent_requests(self, api_base_url: str, wait_for_service):
        """
        测试并发请求

        验证可以处理多个并发请求
        """
        import concurrent.futures

        def make_request():
            response = requests.get(f"{api_base_url}/status")
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status == 200 for status in results)
        print(f"✅ 并发请求测试通过（20个请求）")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
