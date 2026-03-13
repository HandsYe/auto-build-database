#!/usr/bin/env python3
"""
完整功能测试脚本

测试所有CLI命令和核心功能。
"""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✓ {description} - 成功")
            return True
        else:
            print(f"✗ {description} - 失败 (返回码: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - 超时")
        return False
    except Exception as e:
        print(f"✗ {description} - 异常: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("BioDeploy 完整功能测试")
    print("="*60)
    
    tests = [
        # 基础命令
        (["python", "-m", "biodeploy.cli.main", "--help"], "查看帮助"),
        (["python", "-m", "biodeploy.cli.main", "--version"], "查看版本"),
        
        # list命令
        (["python", "-m", "biodeploy.cli.main", "list"], "列出可用数据库"),
        (["python", "-m", "biodeploy.cli.main", "list", "--installed"], "列出已安装数据库"),
        
        # status命令
        (["python", "-m", "biodeploy.cli.main", "status"], "查看所有状态"),
        
        # update命令
        (["python", "-m", "biodeploy.cli.main", "update", "--check-only"], "检查更新"),
        
        # 命令帮助
        (["python", "-m", "biodeploy.cli.main", "install", "--help"], "安装命令帮助"),
        (["python", "-m", "biodeploy.cli.main", "update", "--help"], "更新命令帮助"),
        (["python", "-m", "biodeploy.cli.main", "remove", "--help"], "卸载命令帮助"),
        (["python", "-m", "biodeploy.cli.main", "status", "--help"], "状态命令帮助"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总计: {passed + failed} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed / (passed + failed) * 100:.1f}%")
    
    if failed == 0:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
