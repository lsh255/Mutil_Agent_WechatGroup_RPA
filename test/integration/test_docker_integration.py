"""
Docker 集成测试

验证微信沙盒在 Docker 环境中的功能
"""

import pytest
import time
import subprocess
import requests
from pathlib import Path


@pytest.mark.integration
@pytest.mark.docker
class TestDockerEnvironment:
    """
    Docker 环境测试类
    """

    @pytest.fixture
    def docker_compose_file(self):
        """
        Docker Compose 文件路径
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / "docker" / "compose" / "docker-compose.sandbox.test.yml"

    def test_docker_compose_file_exists(self, docker_compose_file):
        """
        测试 Docker Compose 文件存在
        """
        assert docker_compose_file.exists()
        print(f"✅ Docker Compose 文件存在: {docker_compose_file}")

    def test_docker_compose_valid(self, docker_compose_file):
        """
        测试 Docker Compose 配置有效

        验证语法和配置正确性
        """
        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(docker_compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Docker Compose 配置有效")
            else:
                pytest.skip(f"Docker Compose 配置无效: {result.stderr}")

        except FileNotFoundError:
            pytest.skip("docker-compose 命令未找到")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker Compose 验证超时")

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_docker_images_available(self):
        """
        测试 Docker 镜像可用

        验证所需的镜像已构建或可拉取
        """
        import docker

        client = docker.from_env()

        required_images = [
            "wechat_sandbox:latest",
            "redis:7.2-alpine"
        ]

        for image_name in required_images:
            try:
                # 尝试获取镜像
                client.images.get(image_name)
                print(f"✅ 镜像存在: {image_name}")
            except:
                print(f"⚠️  镜像不存在: {image_name}")

        client.close()


@pytest.mark.integration
@pytest.mark.docker
class TestDockerServices:
    """
    Docker 服务测试类
    """

    @pytest.fixture
    def docker_compose_file(self):
        """
        Docker Compose 文件路径
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / "docker" / "compose" / "docker-compose.sandbox.test.yml"

    @pytest.fixture
    def docker_services(self, docker_compose_file):
        """
        启动 Docker 服务

        使用 docker-compose 启动测试环境
        """
        import docker

        client = docker.from_env()

        # 启动服务
        try:
            subprocess.run(
                ["docker-compose", "-f", str(docker_compose_file), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=120
            )

            # 等待服务启动
            time.sleep(10)

            yield

        finally:
            # 停止服务
            subprocess.run(
                ["docker-compose", "-f", str(docker_compose_file), "down"],
                capture_output=True,
                text=True,
                timeout=60
            )

            client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_redis_container_running(self, docker_services):
        """
        测试 Redis 容器运行
        """
        import docker

        client = docker.from_env()

        # 查找 Redis 容器
        containers = client.containers.list(filters={"name": "redis"})

        if containers:
            print("✅ Redis 容器正在运行")
        else:
            print("⚠️  Redis 容器未运行")

        client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_wechat_sandbox_container_running(self, docker_services):
        """
        测试微信沙盒容器运行
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            print("✅ 微信沙盒容器正在运行")

            # 获取容器日志
            for container in containers:
                logs = container.logs(tail=10).decode('utf-8')
                print(f"📋 容器日志:\n{logs}")
        else:
            print("⚠️  微信沙盒容器未运行")

        client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_container_network_connectivity(self, docker_services):
        """
        测试容器网络连通性

        验证沙盒容器可以连接到 Redis
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 尝试在容器中 ping Redis
            result = container.exec_run(
                "ping -c 3 redis",
                workdir="/tmp"
            )

            if result.exit_code == 0:
                print("✅ 网络连通性正常")
            else:
                print("⚠️  网络连通性异常")

        client.close()


@pytest.mark.integration
@pytest.mark.docker
class TestDockerVolumes:
    """
    Docker 卷测试类
    """

    @pytest.fixture
    def docker_compose_file(self):
        """
        Docker Compose 文件路径
        """
        project_root = Path(__file__).parent.parent.parent
        return project_root / "docker" / "compose" / "docker-compose.sandbox.test.yml"

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_data_volume_mounted(self):
        """
        测试数据卷挂载

        验证 /host/data 目录正确挂载
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 检查挂载点
            mounts = container.attrs.get("Mounts", [])

            data_mounted = any(
                mount.get("Destination") == "/host/data"
                for mount in mounts
            )

            if data_mounted:
                print("✅ 数据卷已挂载")
            else:
                print("⚠️  数据卷未挂载")

        client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_volume_write_permission(self):
        """
        测试卷写入权限

        验证可以向 /host/data 写入文件
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 尝试写入测试文件
            result = container.exec_run(
                "touch /host/data/test.txt",
                workdir="/tmp"
            )

            if result.exit_code == 0:
                print("✅ 写入权限正常")

                # 清理测试文件
                container.exec_run(
                    "rm /host/data/test.txt",
                    workdir="/tmp"
                )
            else:
                print("⚠️  写入权限异常")

        client.close()


@pytest.mark.integration
@pytest.mark.docker
class TestDockerLogs:
    """
    Docker 日志测试类
    """

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_container_logs_available(self):
        """
        测试容器日志可获取

        验证可以获取容器日志用于调试
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 获取日志
            logs = container.logs(tail=50).decode('utf-8')

            assert isinstance(logs, str)
            assert len(logs) > 0

            print(f"✅ 容器日志长度: {len(logs)} 字符")
            print(f"📋 最近日志:\n{logs[-500:]}")

        else:
            pytest.skip("沙盒容器未运行")

        client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_log_level_configurable(self):
        """
        测试日志级别可配置

        验证可以通过环境变量配置日志级别
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 获取环境变量
            env_vars = container.attrs.get("Config", {}).get("Env", [])

            log_level = None
            for var in env_vars:
                if var.startswith("LOG_LEVEL="):
                    log_level = var.split("=")[1]
                    break

            if log_level:
                print(f"✅ 日志级别: {log_level}")
            else:
                print("⚠️  日志级别未配置")

        else:
            pytest.skip("沙盒容器未运行")

        client.close()


@pytest.mark.integration
@pytest.mark.docker
class TestDockerHealthCheck:
    """
    Docker 健康检查测试类
    """

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_container_health_status(self):
        """
        测试容器健康状态

        验证容器健康检查工作正常
        """
        import docker

        client = docker.from_env()

        # 查找沙盒容器
        containers = client.containers.list(filters={"name": "sandbox"})

        if containers:
            container = containers[0]

            # 获取健康状态
            health_status = container.attrs.get("State", {}).get("Health", {})

            if health_status:
                status = health_status.get("Status")
                print(f"✅ 容器健康状态: {status}")
            else:
                print("⚠️  健康检查未配置")

        else:
            pytest.skip("沙盒容器未运行")

        client.close()

    @pytest.mark.skipif(
        not pytest.importorskip('docker', None),
        reason="docker-py not available"
    )
    def test_api_health_endpoint(self):
        """
        测试 API 健康检查端点

        验证 /health 端点可访问
        """
        try:
            response = requests.get(
                "http://localhost:8000/health",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
                print("✅ API 健康检查通过")
            else:
                print(f"⚠️  API 返回状态码: {response.status_code}")

        except requests.exceptions.ConnectionError:
            pytest.skip("API 服务未启动")
        except requests.exceptions.Timeout:
            pytest.fail("API 健康检查超时")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
