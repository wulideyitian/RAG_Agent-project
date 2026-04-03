#!/usr/bin/env python3
"""
测试覆盖率检查脚本
用于生成详细的测试覆盖率报告
"""
import subprocess
import sys
from pathlib import Path


def run_coverage_report():
    """运行覆盖率测试并生成报告"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("📊 开始运行测试覆盖率分析")
    print("=" * 80)
    
    # 运行 pytest 带覆盖率
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit_tests",
        "-v",
        "--tb=short",
        "--cov=core",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "-ra",
    ]
    
    print(f"\n执行命令：{' '.join(cmd)}\n")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False,  # 不抛出异常，即使测试失败
        )
        
        print("\n" + "=" * 80)
        if result.returncode == 0:
            print("✅ 测试覆盖率分析完成！")
        else:
            print("⚠️  部分测试未通过，请查看上面的错误信息")
        print("=" * 80)
        
        print("\n📁 HTML 报告已生成到：htmlcov/index.html")
        print("💡 提示：在浏览器中打开该文件可查看详细的覆盖率报告\n")
        
        return result.returncode
        
    except Exception as e:
        print(f"\n❌ 运行覆盖率分析时发生错误：{e}")
        return 1


def show_summary():
    """显示测试文件摘要"""
    tests_dir = Path(__file__).parent / "unit_tests"
    
    print("\n" + "=" * 80)
    print("📋 当前测试文件列表")
    print("=" * 80)
    
    test_files = sorted(tests_dir.glob("test_*.py"))
    
    for i, test_file in enumerate(test_files, 1):
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        print(f"{i}. {test_file.name:<40} ({line_count} 行)")
    
    print(f"\n总计：{len(test_files)} 个测试文件")
    print("=" * 80)


if __name__ == "__main__":
    show_summary()
    exit_code = run_coverage_report()
    sys.exit(exit_code)
