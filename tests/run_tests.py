#!/usr/bin/env python3
"""
测试运行脚本
用于快速运行所有单元测试
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """运行所有测试"""
    project_root = Path(__file__).parent.parent
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit_tests",
        "-v",
        "--tb=short",
        "-ra",
    ]
    
    print("=" * 60)
    print("开始运行单元测试...")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("\n" + "=" * 60)
        print("✅ 所有测试运行完成！")
        print("=" * 60)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ 部分测试失败，请查看上面的错误信息")
        print("=" * 60)
        return e.returncode
    except Exception as e:
        print(f"\n❌ 运行测试时发生错误：{e}")
        return 1


def run_single_test(test_file: str):
    """运行单个测试文件"""
    project_root = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/unit_tests/{test_file}",
        "-v",
        "-s",
    ]
    
    print(f"运行测试文件：{test_file}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行单个测试
        test_file = sys.argv[1]
        exit_code = run_single_test(test_file)
    else:
        # 运行所有测试
        exit_code = run_tests()
    
    sys.exit(exit_code)
