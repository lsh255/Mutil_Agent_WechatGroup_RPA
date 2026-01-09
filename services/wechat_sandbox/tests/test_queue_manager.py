"""
Redis队列管理器测试
"""
import pytest
import time
import json


class TestQueueManager:
    """
    队列管理器测试类
    """
    
    def test_connection(self, queue_manager):
        """
        测试Redis连接
        """
        assert queue_manager is not None
        assert queue_manager.redis_client is not None
    
    def test_send_raw_message(self, queue_manager, clean_redis):
        """
        测试发送原始消息
        """
        test_message = {
            "message_id": "test_001",
            "bubble_position": {"x": 100, "y": 200, "width": 50, "height": 30},
            "screenshot": "base64_image_data"
        }
        
        result = queue_manager.send_raw_message(test_message)
        
        assert result is True
    
    def test_send_precise_message(self, queue_manager, clean_redis):
        """
        测试发送精确消息
        """
        test_message = {
            "message_id": "test_002",
            "content": "测试消息内容",
            "sender": "张三",
            "timestamp": int(time.time())
        }
        
        result = queue_manager.send_precise_message(test_message)
        
        assert result is True
    
    def test_read_raw_messages(self, queue_manager, clean_redis):
        """
        测试读取原始消息
        """
        test_message = {
            "message_id": "test_003",
            "bubble_position": {"x": 100, "y": 200, "width": 50, "height": 30}
        }
        
        queue_manager.send_raw_message(test_message)
        
        messages = queue_manager.read_raw_messages(count=1)
        
        assert len(messages) >= 1
        assert messages[0]["message_id"] == "test_003"
    
    def test_read_precise_messages(self, queue_manager, clean_redis):
        """
        测试读取精确消息
        """
        test_message = {
            "message_id": "test_004",
            "content": "测试消息内容",
            "sender": "李四"
        }
        
        queue_manager.send_precise_message(test_message)
        
        messages = queue_manager.read_precise_messages(count=1)
        
        assert len(messages) >= 1
        assert messages[0]["message_id"] == "test_004"
    
    def test_message_persistence(self, queue_manager, clean_redis):
        """
        测试消息持久化
        """
        test_message = {
            "message_id": "test_005",
            "content": "持久化测试"
        }
        
        queue_manager.send_precise_message(test_message)
        
        time.sleep(1)
        
        messages = queue_manager.read_precise_messages(count=1)
        
        assert len(messages) >= 1
        assert messages[0]["message_id"] == "test_005"
    
    def test_multiple_messages(self, queue_manager, clean_redis):
        """
        测试多条消息处理
        """
        messages = []
        for i in range(5):
            msg = {
                "message_id": f"test_multi_{i}",
                "content": f"消息内容_{i}"
            }
            messages.append(msg)
            queue_manager.send_precise_message(msg)
        
        time.sleep(1)
        
        result = queue_manager.read_precise_messages(count=5)
        
        assert len(result) >= 5
    
    def test_consumer_group(self, queue_manager, clean_redis):
        """
        测试消费者组
        """
        group_name = "test_consumer_group"
        
        test_message = {
            "message_id": "test_group_001",
            "content": "消费者组测试"
        }
        
        queue_manager.send_precise_message(test_message)
        
        queue_manager.create_consumer_group(group_name)
        
        messages = queue_manager.read_precise_messages(
            group_name=group_name,
            consumer_name="consumer1",
            count=1
        )
        
        assert len(messages) >= 1
    
    def test_message_acknowledge(self, queue_manager, clean_redis):
        """
        测试消息确认
        """
        group_name = "test_ack_group"
        
        test_message = {
            "message_id": "test_ack_001",
            "content": "消息确认测试"
        }
        
        queue_manager.send_precise_message(test_message)
        
        queue_manager.create_consumer_group(group_name)
        
        messages = queue_manager.read_precise_messages(
            group_name=group_name,
            consumer_name="consumer1",
            count=1
        )
        
        if messages:
            result = queue_manager.acknowledge_message(
                queue_manager.stream_precise,
                group_name,
                messages[0][0]
            )
            assert result is True
    
    def test_stream_info(self, queue_manager, clean_redis):
        """
        测试流信息
        """
        test_message = {
            "message_id": "test_info_001",
            "content": "流信息测试"
        }
        
        queue_manager.send_precise_message(test_message)
        
        info = queue_manager.get_stream_info(queue_manager.stream_precise)
        
        assert info is not None
        assert "length" in info
    
    def test_close_connection(self, queue_manager):
        """
        测试关闭连接
        """
        assert queue_manager.close() is True
