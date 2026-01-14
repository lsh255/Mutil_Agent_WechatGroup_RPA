"""
API服务器测试
"""
import pytest
import requests
import json
from unittest.mock import Mock, patch


class TestAPIServer:
    """
    API服务器测试类
    """
    
    @pytest.fixture
    def api_client(self, api_base_url, wait_for_service):
        """
        API客户端
        """
        if not wait_for_service(f"{api_base_url}/health"):
            pytest.skip("API服务未启动")
        
        return api_base_url
    
    def test_root_endpoint(self, api_client):
        """
        测试根路径
        """
        response = requests.get(f"{api_client}/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
    
    def test_health_endpoint(self, api_client):
        """
        测试健康检查端点
        """
        response = requests.get(f"{api_client}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_status_endpoint(self, api_client):
        """
        测试状态端点
        """
        response = requests.get(f"{api_client}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "producers" in data
    
    def test_ui_endpoint(self, api_client):
        """
        测试Web界面端点
        """
        response = requests.get(f"{api_client}/api/ui")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["Content-Type"]
        assert "VNC" in response.text
    
    def test_update_roi_endpoint(self, api_client):
        """
        测试更新ROI端点
        """
        roi_data = {
            "left": 100,
            "top": 200,
            "right": 500,
            "bottom": 800
        }
        
        response = requests.post(
            f"{api_client}/api/roi",
            json=roi_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_update_roi_invalid_data(self, api_client):
        """
        测试更新ROI端点（无效数据）
        """
        roi_data = {
            "left": -1,
            "top": 200,
            "right": 500,
            "bottom": 800
        }
        
        response = requests.post(
            f"{api_client}/api/roi",
            json=roi_data
        )
        
        assert response.status_code == 422
    
    def test_screenshot_endpoint(self, api_client):
        """
        测试截图端点
        """
        response = requests.get(f"{api_client}/api/screenshot")
        
        assert response.status_code == 200
        data = response.json()
        assert "screenshot" in data
    
    def test_restart_endpoint(self, api_client):
        """
        测试重启端点
        """
        response = requests.post(f"{api_client}/api/restart")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_stream_endpoint(self, api_client):
        """
        测试流式端点
        """
        response = requests.get(
            f"{api_client}/stream",
            stream=True,
            timeout=5
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        
        response.close()
    
    def test_invalid_endpoint(self, api_client):
        """
        测试无效端点
        """
        response = requests.get(f"{api_client}/invalid")
        
        assert response.status_code == 404


class TestAPIModels:
    """
    API模型测试类
    """
    
    def test_roi_model_validation(self):
        """
        测试ROI模型验证
        """
        from pydantic import ValidationError
        from api.config import ROIModel
        
        valid_data = {
            "left": 100,
            "top": 200,
            "right": 500,
            "bottom": 800
        }
        
        roi = ROIModel(**valid_data)
        
        assert roi.left == 100
        assert roi.top == 200
        assert roi.right == 500
        assert roi.bottom == 800
    
    def test_roi_model_negative_validation(self):
        """
        测试ROI模型负数验证
        """
        from pydantic import ValidationError
        from api.config import ROIModel
        
        invalid_data = {
            "left": -100,
            "top": 200,
            "right": 500,
            "bottom": 800
        }
        
        with pytest.raises(ValidationError):
            ROIModel(**invalid_data)
    
    def test_roi_model_order_validation(self):
        """
        测试ROI模型顺序验证
        """
        from pydantic import ValidationError
        from api.config import ROIModel

        invalid_data = {
            "left": 500,
            "top": 200,
            "right": 100,
            "bottom": 800
        }

        # 应该抛出 ValidationError
        with pytest.raises(ValidationError):
            ROIModel(**invalid_data)
    
    def test_missing_field_validation(self):
        """
        测试缺失字段验证
        """
        from pydantic import ValidationError
        from api.config import ROIModel
        
        invalid_data = {
            "left": 100,
            "top": 200
        }
        
        with pytest.raises(ValidationError):
            ROIModel(**invalid_data)


class TestAPIIntegration:
    """
    API集成测试类
    """
    
    @pytest.fixture
    def api_client(self, api_base_url, wait_for_service):
        """
        API客户端
        """
        if not wait_for_service(f"{api_base_url}/health"):
            pytest.skip("API服务未启动")
        
        return api_base_url
    
    def test_full_workflow(self, api_client):
        """
        测试完整工作流
        """
        response = requests.get(f"{api_client}/status")
        assert response.status_code == 200
        
        roi_data = {
            "left": 100,
            "top": 200,
            "right": 500,
            "bottom": 800
        }
        
        response = requests.post(
            f"{api_client}/api/roi",
            json=roi_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{api_client}/api/screenshot")
        assert response.status_code == 200
        
        response = requests.get(f"{api_client}/health")
        assert response.status_code == 200
    
    def test_concurrent_requests(self, api_client):
        """
        测试并发请求
        """
        import concurrent.futures
        
        def make_request():
            response = requests.get(f"{api_client}/status")
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        assert all(status == 200 for status in results)
    
    def test_error_handling(self, api_client):
        """
        测试错误处理
        """
        response = requests.post(
            f"{api_client}/api/roi",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
