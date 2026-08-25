#!/usr/bin/env python3
"""
sync_agents.py - AGENTS.md 同步脚本

功能：
1. 从 knowledge-base/项目模板/AGENTS.md 复制通用规则母版
2. 同步到 portfolio-projects 下所有子项目
3. 每个子项目保留自己的 AGENTS.md（项目特有内容）
4. 自动生成复盘记录模板（如果不存在）

使用方法：
    python sync_agents.py

触发时机：
- 项目复盘后更新通用规则
- 新建项目时自动运行
"""

import os
import shutil
import sys
from pathlib import Path

# 设置 UTF-8 编码输出
sys.stdout.reconfigure(encoding='utf-8')

# 路径配置
SCRIPT_DIR = Path(__file__).parent  # D:\projects\portfolio-projects\scripts
PROJECTS_DIR = SCRIPT_DIR.parent  # D:\projects\portfolio-projects
BASE_DIR = PROJECTS_DIR.parent  # D:\projects
TEMPLATE_DIR = BASE_DIR / "knowledge-base" / "项目模板"

# 复盘记录模板
REVIEW_TEMPLATE = """# {project_name} 复盘记录

> 本文件记录项目开发过程中遇到的问题和解决方法
> 每个阶段结束时更新，AI 会自动比对 AGENTS.md 补充避坑指南

---

## {date} 项目启动

### 已完成
（暂无，项目刚开始）

### 遇到的问题
（暂无）

### 解决方法
（暂无）

---

*后续复盘追加在下方，格式保持一致*
"""


def sync_agents():
    """同步 AGENTS.md 到所有子项目"""
    template_file = TEMPLATE_DIR / "AGENTS.md"
    
    if not template_file.exists():
        print(f"❌ 模板文件不存在：{template_file}")
        return False
    
    print(f"📋 模板文件：{template_file}")
    print(f" 项目目录：{PROJECTS_DIR}\n")
    
    # 遍历所有子项目
    synced = 0
    skip_dirs = {'.git', 'scripts', '.trae', 'node_modules', '__pycache__'}
    
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        if project_dir.name.startswith('.') or project_dir.name in skip_dirs:
            continue
        
        agents_file = project_dir / "AGENTS.md"
        review_file = project_dir / "复盘记录.md"
        
        print(f"🔍 检查项目：{project_dir.name}")
        
        # 1. 同步 AGENTS.md（如果不存在则创建）
        if not agents_file.exists():
            print(f"   📄 创建 AGENTS.md...")
            shutil.copy2(template_file, agents_file)
            synced += 1
        else:
            print(f"   ✅ AGENTS.md 已存在（保留项目特有内容）")
        
        # 2. 创建复盘记录模板（如果不存在）
        if not review_file.exists():
            print(f"   📝 创建复盘记录模板...")
            review_content = REVIEW_TEMPLATE.format(
                project_name=project_dir.name,
                date="2026-08-25"
            )
            review_file.write_text(review_content, encoding='utf-8')
            synced += 1
        else:
            print(f"   ✅ 复盘记录已存在")
        
        print()
    
    print(f"✨ 同步完成！更新了 {synced} 个文件")
    return True


def create_new_project(project_name: str):
    """创建新项目并初始化 AGENTS.md"""
    project_dir = PROJECTS_DIR / project_name
    
    if project_dir.exists():
        print(f"❌ 项目目录已存在：{project_dir}")
        return False
    
    print(f"🚀 创建新项目：{project_name}")
    
    # 创建项目目录
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 AGENTS.md
    template_file = TEMPLATE_DIR / "AGENTS.md"
    agents_file = project_dir / "AGENTS.md"
    shutil.copy2(template_file, agents_file)
    print(f"   📄 创建 AGENTS.md")
    
    # 创建复盘记录
    review_file = project_dir / "复盘记录.md"
    review_content = REVIEW_TEMPLATE.format(
        project_name=project_name,
        date="2026-08-25"
    )
    review_file.write_text(review_content, encoding='utf-8')
    print(f"   📝 创建复盘记录模板")
    
    # 创建基础目录结构
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "src" / "modules").mkdir(exist_ok=True)
    (project_dir / "src" / "utils").mkdir(exist_ok=True)
    (project_dir / "data").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    print(f"   📁 创建项目结构")
    
    print(f"\n✨ 项目 {project_name} 创建完成！")
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 创建新项目
        project_name = sys.argv[1]
        create_new_project(project_name)
    else:
        # 同步所有项目
        sync_agents()
