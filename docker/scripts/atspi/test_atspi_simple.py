#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的AT-SPI测试脚本"""

import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("AT-SPI简单测试")
print("=" * 60)

try:
    import pyatspi
    print("✅ pyatspi已导入")
    print(f"   版本: {pyatspi.__version__}")
except ImportError as e:
    print(f"❌ pyatspi导入失败: {e}")
    sys.exit(1)

try:
    print("\n正在获取Registry...")
    registry = pyatspi.Registry
    print("✅ 获取Registry成功")

    print("\n正在获取Desktop...")
    desktop = pyatspi.Registry.getDesktop(0)
    print(f"✅ 获取Desktop成功: {desktop}")

    print(f"\nDesktop类型: {type(desktop)}")
    print(f"Desktop名称: {desktop.name}")
    print(f"Desktop角色: {desktop.getRoleName()}")

    child_count = getattr(desktop, 'childCount', 0)
    print(f"Desktop子项数量: {child_count}")

    if child_count > 0:
        print(f"\n正在遍历{child_count}个应用...")
        for i in range(child_count):
            try:
                app = desktop.getChildAtIndex(i)
                app_name = app.name or "(无名称)"
                app_role = app.getRoleName()
                print(f"  [{i}] {app_name} (角色: {app_role})")
            except Exception as e:
                print(f"  [{i}] 获取失败: {e}")
    else:
        print("\n⚠️  没有找到任何应用")
        print("\n可能的原因:")
        print("  1. 微信未启动")
        print("  2. QT_ACCESSIBILITY未设置")
        print("  3. AT-SPI服务未正常工作")
        print("  4. 微信版本不支持AT-SPI")

        print("\n尝试直接使用Accerciser检查...")

except Exception as e:
    print(f"\n❌ AT-SPI测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
