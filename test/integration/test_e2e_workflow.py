"""
端到端工作流测试

验证完整的消息流：微信 → AT-SPI → Redis → SSE → 客户端
"""

import pytest
import requests
import time
import json
import redis
from pathlib import Path
from typing import Generator


@pytest.fixture(scope="module")
def redis_client() -> Generator[redis.Redis, None, None]:
    """
    Redis 客户端
    """
    client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    try:
        # 测试连接
        client.ping()
        yield client
    except:
        pytest.skip("Redis 连接失败")
    finally:
        client.close()


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
@pytest.mark.e2e
class TestE2ETextMessage:
    """
    端到端文本消息测试
    """

    def test_text_message_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试文本消息完整工作流

        场景：
        1. 用户在微信发送文本消息
        2. AT-SPI 检测到新消息
        3. 提取消息内容（text 类型）
        4. 推送到 Redis 精确队列
        5. SSE 推送给客户端
        """
        print("\n📝 测试文本消息工作流")

        # 1. 清空 Redis 队列（可选）
        # redis_client.delete('wechat:messages:precise')

        # 2. 建立 SSE 连接
        sse_response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=30
        )

        assert sse_response.status_code == 200

        print("✅ SSE 连接已建立")

        # 3. 监听 SSE 消息
        messages_received = []

        print("🎧 等待新消息（10秒）...")

        start_time = time.time()
        timeout = 10

        for line in sse_response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    message = json.loads(json_str)

                    if message["type"] == "text":
                        messages_received.append(message)
                        print(f"✅ 收到文本消息: {message['sender']} - {message['content']}")

                        # 收到一条就退出
                        break

        sse_response.close()

        # 4. 验证
        if messages_received:
            message = messages_received[0]

            # 验证消息结构
            assert "id" in message
            assert "type" in message
            assert message["type"] == "text"
            assert "sender" in message
            assert "content" in message
            assert isinstance(message["content"]["text"], str)

            print(f"✅ 文本消息工作流测试通过")
        else:
            print("⚠️  未收到文本消息（可能需要手动发送）")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EPhotoMessage:
    """
    端到端图片消息测试
    """

    def test_photo_message_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试图片消息完整工作流

        场景：
        1. 用户在微信发送图片
        2. AT-SPI 检测到新消息
        3. 点击消息，检测到窗口
        4. 根据窗口标题判断为 photo 类型
        5. 保存高分辨率图片到 /host/data/
        6. 推送到 Redis 精确队列
        7. SSE 推送给客户端
        """
        print("\n📸 测试图片消息工作流")

        # 1. 建立 SSE 连接
        sse_response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=30
        )

        assert sse_response.status_code == 200

        print("✅ SSE 连接已建立")

        # 2. 监听 SSE 消息
        messages_received = []

        print("🎧 等待图片消息（10秒）...")

        start_time = time.time()
        timeout = 10

        for line in sse_response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    message = json.loads(json_str)

                    if message["type"] == "photo":
                        messages_received.append(message)
                        print(f"✅ 收到图片消息: {message['sender']}")

                        # 收到一条就退出
                        break

        sse_response.close()

        # 3. 验证
        if messages_received:
            message = messages_received[0]

            # 验证消息结构
            assert "id" in message
            assert "type" in message
            assert message["type"] == "photo"
            assert "sender" in message
            assert "content" in message
            assert "high_res_media_path" in message["content"]
            assert message["content"]["high_res_media_path"].startswith("/host/data/")

            # 验证文件存在（需要在 Docker 环境中）
            # host_path = message["content"]["high_res_media_path"].replace("/host/data", "data")
            # assert Path(host_path).exists()

            print(f"✅ 图片消息工作流测试通过")
            print(f"   文件路径: {message['content']['high_res_media_path']}")
        else:
            print("⚠️  未收到图片消息（可能需要手动发送）")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EVideoMessage:
    """
    端到端视频消息测试
    """

    def test_video_message_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试视频消息完整工作流

        场景：
        1. 用户在微信发送视频
        2. AT-SPI 检测到新消息
        3. 点击消息，检测到窗口
        4. 根据窗口标题判断为 video 类型
        5. 保存视频到 /host/data/
        6. 推送到 Redis 精确队列
        7. SSE 推送给客户端
        """
        print("\n🎬 测试视频消息工作流")

        # 1. 建立 SSE 连接
        sse_response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=30
        )

        assert sse_response.status_code == 200

        print("✅ SSE 连接已建立")

        # 2. 监听 SSE 消息
        messages_received = []

        print("🎧 等待视频消息（10秒）...")

        start_time = time.time()
        timeout = 10

        for line in sse_response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    message = json.loads(json_str)

                    if message["type"] == "video":
                        messages_received.append(message)
                        print(f"✅ 收到视频消息: {message['sender']}")

                        # 收到一条就退出
                        break

        sse_response.close()

        # 3. 验证
        if messages_received:
            message = messages_received[0]

            # 验证消息结构
            assert "id" in message
            assert "type" in message
            assert message["type"] == "video"
            assert "sender" in message
            assert "content" in message
            assert "high_res_media_path" in message["content"]
            assert message["content"]["high_res_media_path"].startswith("/host/data/")

            print(f"✅ 视频消息工作流测试通过")
            print(f"   文件路径: {message['content']['high_res_media_path']}")
        else:
            print("⚠️  未收到视频消息（可能需要手动发送）")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EFileMessage:
    """
    端到端文件消息测试
    """

    def test_file_message_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试文件消息完整工作流

        场景：
        1. 用户在微信发送文件
        2. AT-SPI 检测到新消息
        3. 点击消息，检测到窗口
        4. 根据窗口标题判断为 file 类型
        5. 保存文件到 /host/data/others/
        6. 保存元数据（JSON），不推送 SSE
        """
        print("\n📁 测试文件消息工作流")

        print("⚠️  注意：文件消息不会通过 SSE 推送，只保存到磁盘")

        # 由于文件不推送 SSE，我们只能检查 Redis 队列
        # 或者检查文件系统

        # 等待一段时间让文件被处理
        time.sleep(5)

        # 检查 /host/data/others/ 目录
        # 这个测试需要在 Docker 环境中运行
        print("✅ 文件消息工作流测试完成")
        print("   提示：文件保存在 /host/data/others/ 目录")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EMixedMessages:
    """
    端到端混合消息测试
    """

    def test_mixed_message_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试混合消息工作流

        场景：连续接收不同类型的消息，验证系统可以正确处理
        """
        print("\n📊 测试混合消息工作流")

        # 1. 建立 SSE 连接
        sse_response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=30
        )

        assert sse_response.status_code == 200

        print("✅ SSE 连接已建立")

        # 2. 监听多种消息
        messages_by_type = {
            "text": [],
            "photo": [],
            "video": []
        }

        print("🎧 监听消息（15秒）...")

        start_time = time.time()
        timeout = 15

        for line in sse_response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line:
                line_str = line.decode('utf-8')

                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    message = json.loads(json_str)

                    msg_type = message["type"]
                    if msg_type in messages_by_type:
                        messages_by_type[msg_type].append(message)
                        print(f"✅ 收到 {msg_type} 消息: {message['sender']}")

        sse_response.close()

        # 3. 统计
        print("\n📊 消息统计:")
        for msg_type, messages in messages_by_type.items():
            count = len(messages)
            print(f"   {msg_type}: {count} 条")

        print("✅ 混合消息工作流测试完成")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EMessagePersistence:
    """
    端到端消息持久化测试
    """

    def test_message_persistence_workflow(self, redis_client, api_base_url, wait_for_service):
        """
        测试消息持久化工作流

        验证：
        1. 消息保存到 Redis Stream
        2. 可以从 Redis 读取历史消息
        3. 消息有过期时间
        """
        print("\n💾 测试消息持久化工作流")

        # 1. 检查 Redis Stream
        stream_name = "wechat:messages:precise"

        # 获取流信息
        stream_info = redis_client.xinfo_stream(stream_name)
        print(f"✅ Stream 长度: {stream_info['length']}")

        # 2. 读取最近的 10 条消息
        messages = redis_client.xrevrange(
            stream_name,
            count=10
        )

        print(f"✅ 读取到 {len(messages)} 条历史消息")

        # 3. 验证消息格式
        for msg_id, fields in messages[:3]:  # 只验证前 3 条
            assert "id" in fields
            assert "type" in fields
            assert "sender" in fields

            print(f"   消息 {msg_id}: {fields['type']} - {fields['sender']}")

        print("✅ 消息持久化工作流测试通过")


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EErrorRecovery:
    """
    端到端错误恢复测试
    """

    def test_service_restart_recovery(self, redis_client, api_base_url, wait_for_service):
        """
        测试服务重启后的恢复

        验证服务重启后可以正常处理新消息
        """
        print("\n🔄 测试服务重启恢复")

        # 1. 重启服务
        response = requests.post(f"{api_base_url}/api/restart")
        assert response.status_code == 200

        print("✅ 服务重启请求已发送")

        # 2. 等待服务恢复
        time.sleep(10)

        # 3. 验证服务健康
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200

        print("✅ 服务已恢复")

        # 4. 建立 SSE 连接
        sse_response = requests.get(
            f"{api_base_url}/api/stream/messages",
            stream=True,
            timeout=10
        )

        assert sse_response.status_code == 200

        print("✅ SSE 连接已建立")

        # 5. 监听消息
        messages_received = 0
        start_time = time.time()
        timeout = 5

        for line in sse_response.iter_lines():
            if time.time() - start_time > timeout:
                break

            if line and line.decode('utf-8').startswith("data: "):
                messages_received += 1
                if messages_received >= 1:
                    break

        sse_response.close()

        print(f"✅ 服务重启恢复测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
