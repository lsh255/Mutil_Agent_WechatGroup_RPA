"""
测试运行脚本
"""
import subprocess
import sys
import os


def run_unit_tests():
    """
    运行单元测试
    """
    print("=" * 60)
    print("运行单元测试...")
    print("=" * 60)
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_queue_manager.py",
            "tests/test_producer_service.py",
            "-v",
            "-m", "unit"
        ],
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode


def run_api_tests():
    """
    运行API测试
    """
    print("=" * 60)
    print("运行API测试...")
    print("=" * 60)
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_api_server.py",
            "-v",
            "-m", "api"
        ],
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode


def run_integration_tests():
    """
    运行集成测试
    """
    print("=" * 60)
    print("运行集成测试...")
    print("=" * 60)
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_integration.py",
            "-v",
            "-m", "integration"
        ],
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode


def run_all_tests():
    """
    运行所有测试
    """
    print("=" * 60)
    print("运行所有测试...")
    print("=" * 60)
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v"
        ],
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode


def run_docker_tests():
    """
    运行Docker相关测试
    """
    print("=" * 60)
    print("运行Docker测试...")
    print("=" * 60)
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_integration.py",
            "-v",
            "-m", "docker"
        ],
        cwd=os.path.dirname(__file__)
    )
    
    return result.returncode


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python run_tests.py unit        # 运行单元测试")
        print("  python run_tests.py api         # 运行API测试")
        print("  python run_tests.py integration # 运行集成测试")
        print("  python run_tests.py docker      # 运行Docker测试")
        print("  python run_tests.py all         # 运行所有测试")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "unit":
        exit_code = run_unit_tests()
    elif test_type == "api":
        exit_code = run_api_tests()
    elif test_type == "integration":
        exit_code = run_integration_tests()
    elif test_type == "docker":
        exit_code = run_docker_tests()
    elif test_type == "all":
        exit_code = run_all_tests()
    else:
        print(f"未知的测试类型: {test_type}")
        sys.exit(1)
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("测试失败！")
        print("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
