#!/usr/bin/env python3
"""
测试运行脚本
提供便捷的测试执行命令
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.stdout:
            print("输出:")
            print(result.stdout)
        
        if result.stderr:
            print("错误:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} 成功完成")
        else:
            print(f"❌ {description} 失败 (退出码: {result.returncode})")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ 执行命令时发生异常: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    return run_command(cmd, "运行所有测试")


def run_unit_tests():
    """运行单元测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit", "-v"]
    return run_command(cmd, "运行单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration", "-v"]
    return run_command(cmd, "运行集成测试")


def run_api_tests():
    """运行API测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "api", "-v"]
    return run_command(cmd, "运行API测试")


def run_websocket_tests():
    """运行WebSocket测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "websocket", "-v"]
    return run_command(cmd, "运行WebSocket测试")


def run_database_tests():
    """运行数据库测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "database", "-v"]
    return run_command(cmd, "运行数据库测试")


def run_slow_tests():
    """运行慢速测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "slow", "-v"]
    return run_command(cmd, "运行慢速测试")


def run_coverage_tests():
    """运行测试并生成覆盖率报告"""
    cmd = [
        "python", "-m", "pytest", "tests/",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v"
    ]
    return run_command(cmd, "运行测试并生成覆盖率报告")


def run_specific_test(test_path):
    """运行特定测试文件或测试函数"""
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    return run_command(cmd, f"运行特定测试: {test_path}")


def run_parallel_tests():
    """并行运行测试"""
    cmd = ["python", "-m", "pytest", "tests/", "-n", "auto", "-v"]
    return run_command(cmd, "并行运行测试")


def run_failed_tests():
    """重新运行失败的测试"""
    cmd = ["python", "-m", "pytest", "--lf", "-v"]
    return run_command(cmd, "重新运行失败的测试")


def run_lint_checks():
    """运行代码质量检查"""
    print("\n运行代码质量检查...")
    
    # 检查是否安装了必要的工具
    tools = {
        "flake8": "代码风格检查",
        "black": "代码格式化检查",
        "isort": "导入排序检查",
        "mypy": "类型检查"
    }
    
    available_tools = []
    for tool, description in tools.items():
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            available_tools.append((tool, description))
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {tool} 未安装，跳过 {description}")
    
    if not available_tools:
        print("❌ 没有可用的代码质量检查工具")
        return False
    
    success = True
    
    for tool, description in available_tools:
        if tool == "flake8":
            cmd = ["flake8", "app/", "tests/", "--max-line-length=88", "--extend-ignore=E203,W503"]
        elif tool == "black":
            cmd = ["black", "--check", "app/", "tests/"]
        elif tool == "isort":
            cmd = ["isort", "--check-only", "app/", "tests/"]
        elif tool == "mypy":
            cmd = ["mypy", "app/"]
        else:
            continue
        
        if not run_command(cmd, description):
            success = False
    
    return success


def setup_test_environment():
    """设置测试环境"""
    print("设置测试环境...")
    
    # 检查必要的依赖
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "httpx",
        "fastapi"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要的测试依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    # 检查测试数据库配置
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        print("⚠️  未设置 TEST_DATABASE_URL 环境变量")
        print("将使用内存数据库进行测试")
    
    print("✅ 测试环境检查完成")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试运行脚本")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=[
            "all", "unit", "integration", "api", "websocket", 
            "database", "slow", "coverage", "parallel", 
            "failed", "lint", "setup"
        ],
        default="all",
        help="要运行的测试类型"
    )
    parser.add_argument(
        "--file",
        "-f",
        help="运行特定的测试文件或测试函数"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python 版本: {sys.version}")
    
    # 如果指定了特定文件
    if args.file:
        success = run_specific_test(args.file)
    else:
        # 根据测试类型运行相应的测试
        test_functions = {
            "all": run_all_tests,
            "unit": run_unit_tests,
            "integration": run_integration_tests,
            "api": run_api_tests,
            "websocket": run_websocket_tests,
            "database": run_database_tests,
            "slow": run_slow_tests,
            "coverage": run_coverage_tests,
            "parallel": run_parallel_tests,
            "failed": run_failed_tests,
            "lint": run_lint_checks,
            "setup": setup_test_environment
        }
        
        test_function = test_functions.get(args.test_type)
        if test_function:
            success = test_function()
        else:
            print(f"❌ 未知的测试类型: {args.test_type}")
            success = False
    
    if success:
        print("\n🎉 测试执行成功！")
        sys.exit(0)
    else:
        print("\n❌ 测试执行失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()