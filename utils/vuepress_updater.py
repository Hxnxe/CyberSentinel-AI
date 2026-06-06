import os
import re
from datetime import datetime
import shutil
import subprocess # <-- Import subprocess
# 修改相对导入为绝对导入
try:
    from utils.logger import get_logger
except ImportError:
    # 备用方案 - 如果作为模块导入时
    try:
        from .logger import get_logger
    except ImportError:
        # 如果logger模块不存在，创建一个简单的日志函数
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        def get_logger(name):
            return logging.getLogger(name)

# Get logger for this module
logger = get_logger('vuepress_updater_simple') # 使用新的日志记录器名称

# --- Configuration ---
# Use absolute path for the blog's docs directory
# Adjust this path if your blog directory structure is different
BLOG_DOCS_PATH = os.path.normpath('/home/p/new/docs')
# Define Blog Root Path for running build commands
BLOG_ROOT_PATH = os.path.normpath('/home/p/new/')

# Derive other paths from the absolute BLOG_DOCS_PATH
NOTES_TS_PATH = os.path.join(BLOG_DOCS_PATH, '.vuepress', 'notes.ts')
DEMO_NOTES_DIR = os.path.join(BLOG_DOCS_PATH, 'notes', 'demo')
DEMO_README_PATH = os.path.join(DEMO_NOTES_DIR, 'README.md')
# --- End Configuration ---

def _add_frontmatter(filepath, date_str, create_time_str):
    """为 Markdown 文件添加 Frontmatter (保留此功能)"""
    try:
        frontmatter = f"""---
title: AI 安全分析日报 {date_str}
createTime: {create_time_str}
permalink: /notes/demo/{date_str}/
---

"""
        with open(filepath, 'r+', encoding='utf-8') as f:
            content = f.read()
            f.seek(0, 0)
            if not content.startswith('---'):
                f.write(frontmatter + content)
                logger.info(f"为文件 {filepath} 添加了前置元数据")
            else:
                logger.info(f"文件 {filepath} 已存在前置元数据，跳过")
        return True
    except Exception as e:
        logger.error(f"为文件 {filepath} 添加前置元数据时出错: {e}")
        return False

def copy_and_prepare_md(source_md_path, date_str):
    """复制源 Markdown 文件到博客目录，重命名并添加 Frontmatter。"""
    try:
        if not os.path.exists(source_md_path):
            logger.error(f"源 Markdown 文件未找到: {source_md_path}")
            return None

        target_filename = f"{date_str}.md"
        target_filepath = os.path.join(DEMO_NOTES_DIR, target_filename)

        os.makedirs(DEMO_NOTES_DIR, exist_ok=True)
        
        if os.path.exists(target_filepath):
            logger.info(f"目标文件已存在，先删除: {target_filepath}")
            os.remove(target_filepath)

        shutil.copy2(source_md_path, target_filepath)
        logger.info(f"已复制 {source_md_path} 到 {target_filepath}")

        now = datetime.now()
        create_time_str = now.strftime('%Y/%m/%d %H:%M:%S')
        if _add_frontmatter(target_filepath, date_str, create_time_str):
            return target_filepath
        else:
            if os.path.exists(target_filepath):
                os.remove(target_filepath)
            return None

    except Exception as e:
        logger.error(f"复制/准备 Markdown 文件 {source_md_path} 时出错: {e}")
        return None

def update_readme_md(date_str):
    """更新 demo README.md 文件以包含指向新笔记的链接 (保留此功能)
       **覆盖更新逻辑**：如果链接已存在，则移除旧链接，并将新链接添加到列表顶部。
    """
    try:
        if not os.path.exists(DEMO_README_PATH):
            # 如果 README 不存在，尝试创建它或记录错误
            logger.warning(f"README.md 文件未找到: {DEMO_README_PATH}。将尝试创建。")
            try:
                with open(DEMO_README_PATH, 'w', encoding='utf-8') as f:
                     f.write("""---
title: 安全资讯
createTime: 2025/03/28 00:07:14
permalink: /demo/
---

""") # 创建基础 README
                logger.info(f"已创建空的 README.md: {DEMO_README_PATH}")
            except Exception as create_e:
                logger.error(f"创建 README.md 文件失败: {create_e}")
                return False
                
        new_link = f"- [{date_str}](./{date_str}.md)\n"
        link_pattern = f"./{date_str}.md"

        with open(DEMO_README_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        list_start_index = -1
        found_list_or_content = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('- ['):
                list_start_index = i
                found_list_or_content = True
                break
            if stripped_line == '---' and i + 1 < len(lines) and lines[i+1].strip() == '' and not found_list_or_content:
                 list_start_index = i + 2
                 found_list_or_content = True

        readme_updated = False
        
        # --- 修改部分：实现覆盖更新 --- 
        
        # 先移除所有匹配当天日期的旧链接
        initial_length = len(lines)
        lines = [line for line in lines if link_pattern not in line]
        removed_count = initial_length - len(lines)
        if removed_count > 0:
            logger.info(f"移除了 {removed_count} 个指向 '{date_str}' 的旧链接。")
            readme_updated = True # 标记为需要更新
            # 因为移除了行，需要重新计算插入点
            # 这里简单处理：如果原来有列表，就在列表开头插入；否则在末尾插入
            list_start_index = -1 # 重置
            for i, line in enumerate(lines):
                 if line.strip().startswith('- ['):
                      list_start_index = i
                      break
            if list_start_index == -1: # 如果移除后没列表了，尝试找 Frontmatter 后的空行
                 for i, line in enumerate(lines):
                     if line.strip() == '---' and i + 1 < len(lines) and lines[i+1].strip() == '':
                          list_start_index = i + 2
                          break

        # 现在执行插入逻辑
        # 如果找到了插入点（列表开头或 Frontmatter 后）
        if list_start_index != -1:
             # 确保插入点有效
             list_start_index = max(0, list_start_index)
             list_start_index = min(len(lines), list_start_index) 
             # 插入新链接
             lines.insert(list_start_index, new_link)
             logger.info(f"已将 '{date_str}' 的新链接插入到列表顶部 (或 Frontmatter 后)。")
             readme_updated = True # 再次确认需要更新
        # 如果没找到合适的插入点（例如文件是空的或格式不规范）
        else:
            logger.warning(f"在 {DEMO_README_PATH} 中未找到列表或 Frontmatter 后的插入点，将附加到文件末尾。")
            if lines and not lines[-1].endswith('\n'): 
                 lines[-1] += '\n'
            if lines and lines[-1].strip() != '':
                 lines.append('\n')
            lines.append(new_link)
            readme_updated = True
            
        # --- 结束修改部分 ---

        if readme_updated:
            with open(DEMO_README_PATH, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.info(f"成功更新 {DEMO_README_PATH} (覆盖模式)")
        else:
             # 如果没有移除旧链接，也没有找到插入点（理论上不应发生）
             # 或者如果移除了但无法插入（理论上也不应发生）
             # 但保留此日志以防万一
             logger.info(f"{DEMO_README_PATH} 未执行更新。")

        return True

    except Exception as e:
        logger.error(f"更新 {DEMO_README_PATH} 时出错: {e}")
        return False

def update_blog_content(source_md_path):
    """简化版：仅复制 Markdown 文件并更新 README.md。"""
    logger.info(f"开始简化博客内容更新流程: {source_md_path}")
    try:
        filename = os.path.basename(source_md_path)
        match = re.search(r'(\d{4})_(\d{2})_(\d{2})', filename)
        if not match:
            logger.error(f"无法从文件名中提取日期: {filename}")
            return False

        year, month, day = match.groups()
        date_str = f"{year}-{month}-{day}"

        # 1. 复制和准备 Markdown 文件（包括添加 Frontmatter）
        target_md_path = copy_and_prepare_md(source_md_path, date_str)
        if not target_md_path:
            logger.error("处理 Markdown 文件失败。中止更新。")
            return False
        logger.info(f"已准备博客文章: {target_md_path}")

        # 2. 更新 README.md
        if not update_readme_md(date_str):
            logger.warning("更新 README.md 失败，但内容已复制。")
            # 根据需要决定这是否算作整体失败
            # return False 

        logger.info(f"成功完成 {date_str} 的博客内容更新（仅文件和 README）")
        return True

    except Exception as e:
        logger.error(f"为 {source_md_path} 更新博客内容时出错: {e}")
        return False

# 主执行块修改为调用简化版函数
if __name__ == '__main__':
    print("测试简化版 VuePress 更新器 (仅内容)...")
    
    # --- 测试设置 --- 
    # 保持测试文件的创建逻辑
    test_source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results', 'ai_analysis'))
    test_source_file = os.path.join(test_source_dir, f"Ai_{datetime.now().strftime('%Y_%m_%d')}.md")
    os.makedirs(test_source_dir, exist_ok=True)
    if not os.path.exists(test_source_file):
         with open(test_source_file, 'w', encoding='utf-8') as f:
              f.write("# Test Analysis Content\n\n这是简化流程的测试内容。")
         print(f"创建了测试源文件: {test_source_file}")

    # 确保目标目录和 README 存在，用于测试
    os.makedirs(DEMO_NOTES_DIR, exist_ok=True)
    if not os.path.exists(DEMO_README_PATH):
        with open(DEMO_README_PATH, 'w', encoding='utf-8') as f:
            # 使用三引号定义多行字符串
            f.write("""---
title: 安全资讯
createTime: 2025/03/28 00:07:14
permalink: /demo/
---

- [2025-03-23](./2025-03-23.md)
""") # 模拟一个旧的 README
        print(f"创建了测试 {DEMO_README_PATH}")
    # --- 结束测试设置 ---

    # 运行简化版更新
    success = update_blog_content(test_source_file)
    print(f"测试内容更新成功: {success}")

    # 可以选择性地再次运行以测试幂等性
    print("\n再次运行以测试幂等性...")
    success_idem = update_blog_content(test_source_file)
    print(f"第二次内容更新成功 (幂等性测试): {success_idem}")
    
    print("\n检查以下文件是否按预期更新:")
    print(f"- {DEMO_NOTES_DIR}/{datetime.now().strftime('%Y-%m-%d')}.md")
    print(f"- {DEMO_README_PATH}")
    print("注意：此脚本不再执行 VuePress 构建。") 