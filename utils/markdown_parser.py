import os
import re
import markdown
import argparse
from datetime import datetime
import random
import logging  # 确保导入 logging

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VulnerabilityReportConverter:
    def __init__(self):
        self.html_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width initial-scale=1'>
    <title>{title}</title>
    <style>
        :root {{
            --primary-color: #4a89dc;
            --primary-light: #6aa2e8;
            --primary-dark: #357abd;
            --bg-color: #f5f7fa;
            --card-bg: #ffffff;
            --text-color: #2c3e50;
            --text-light: #7f8c8d;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --critical-color: #c0392b;
            --info-color: #3498db;
            --low-color: #2ecc71;
            --border-color: #e1e8ed;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
            --max-width: 1600px;
            --header-height: 80px;
            --spacing: 20px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .header {{
            background: var(--card-bg);
            min-height: var(--header-height);
            box-shadow: var(--shadow-md);
            display: flex;
            align-items: center;
            justify-content: center;
            position: sticky;
            top: 0;
            z-index: 100;
            transition: var(--transition);
            padding: 20px 0;
        }}

        .header.scrolled {{
            height: 60px;
            box-shadow: var(--shadow-lg);
        }}

        .container {{
            width: 100%;
            max-width: var(--max-width);
            margin: 0 auto;
            padding: var(--spacing);
            flex: 1;
        }}

        h1 {{
            text-align: center;
            font-size: 2.2em;
            color: var(--primary-color);
            font-weight: 600;
            margin: 0;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }}

        h1 .emoji {{
            font-size: 1.2em;
            animation: float 3s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}

        .list-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: var(--spacing);
            margin: var(--spacing) 0;
            animation: fadeIn 0.5s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .cve-item {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
        }}

        .cve-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
            transform: scaleX(0);
            transition: var(--transition);
            transform-origin: left;
        }}

        .cve-item:hover {{
            transform: translateY(-3px);
            box-shadow: var(--shadow-md);
        }}

        .cve-item:hover::before {{
            transform: scaleX(1);
        }}

        .cve-icon {{
            font-size: 2em;
            color: var(--primary-color);
            flex-shrink: 0;
            transition: var(--transition);
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            background: rgba(74, 137, 220, 0.1);
        }}

        .cve-item:hover .cve-icon {{
            transform: scale(1.1);
            background: var(--primary-color);
            color: white;
        }}

        .cve-info {{
            flex-grow: 1;
            min-width: 0;
        }}

        .cve-title {{
            margin: 0 0 8px 0;
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.4;
        }}

        .cve-meta {{
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 0.9em;
            color: var(--text-light);
        }}

        .risk-level {{
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 500;
            gap: 5px;
        }}

        .risk-critical {{
            background: rgba(192, 57, 43, 0.15);
            color: var(--critical-color);
        }}

        .risk-high {{
            background: rgba(231, 76, 60, 0.15);
            color: var(--danger-color);
        }}

        .risk-medium {{
            background: rgba(243, 156, 18, 0.15);
            color: var(--warning-color);
        }}

        .risk-low {{
            background: rgba(46, 204, 113, 0.15);
            color: var(--low-color);
        }}

        .risk-info {{
            background: rgba(52, 152, 219, 0.15);
            color: var(--info-color);
        }}

        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            overflow-y: auto;
            backdrop-filter: blur(8px);
            transition: var(--transition);
            padding: 20px;
        }}

        .modal-content {{
            background: var(--bg-color);
            margin: 40px auto;
            padding: 40px;
            max-width: 1000px;
            border-radius: 20px;
            position: relative;
            box-shadow: var(--shadow-lg);
            animation: modalSlideIn 0.4s ease;
        }}

        @keyframes modalSlideIn {{
            from {{ transform: translateY(-30px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .close-btn {{
            position: absolute;
            right: 25px;
            top: 25px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--card-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
            font-size: 1.5em;
            color: var(--text-light);
            border: 1px solid var(--border-color);
        }}

        .close-btn:hover {{
            background: var(--danger-color);
            color: white;
            transform: rotate(90deg);
            border-color: var(--danger-color);
        }}

        .modal h2 {{
            font-size: 1.8em;
            color: var(--primary-color);
            margin-bottom: 30px;
            padding-right: 50px;
            line-height: 1.4;
        }}

        .card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            transition: var(--transition);
        }}

        .card:hover {{
            box-shadow: var(--shadow-md);
        }}

        .card h3 {{
            color: var(--primary-color);
            font-size: 1.4em;
            margin-top: 0;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }}

        .table-container {{
            margin: 20px 0;
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            background: var(--bg-color);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            table-layout: fixed;
            font-size: 0.95em;
        }}

        th, td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
            line-height: 1.6;
            vertical-align: top;
        }}

        td {{
            word-wrap: break-word;
            overflow-wrap: break-word;
            background: var(--card-bg);
        }}

        td:first-child {{
            width: 120px;
            font-weight: 500;
            color: var(--text-color);
            background: var(--bg-color);
        }}

        td a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            transition: var(--transition);
            display: inline-block;
        }}

        td a:hover {{
            color: var(--primary-dark);
            text-decoration: underline;
            transform: translateX(2px);
        }}

        th {{
            background: var(--bg-color);
            color: var(--text-color);
            font-weight: 600;
            border-bottom: 2px solid var(--primary-color);
            white-space: nowrap;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        th:first-child {{
            width: 120px;
            border-top-left-radius: 8px;
        }}

        th:last-child {{
            border-top-right-radius: 8px;
        }}

        tr:hover td {{
            background: rgba(74, 137, 220, 0.05);
        }}

        tr:hover td:first-child {{
            background: rgba(74, 137, 220, 0.1);
        }}

        @media (max-width: 1200px) {{
            .list-container {{
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }}
        }}

        @media (max-width: 768px) {{
            :root {{
                --spacing: 15px;
                --header-height: 60px;
            }}

            h1 {{
                font-size: 1.8em;
            }}

            .modal-content {{
                padding: 25px;
                margin: 20px;
            }}

            .card {{
                padding: 20px;
            }}

            .card h3 {{
                font-size: 1.2em;
            }}
        }}

        .footer {{
            text-align: center;
            padding: var(--spacing);
            background: var(--card-bg);
            color: var(--text-light);
            font-size: 0.9em;
            border-top: 1px solid var(--border-color);
        }}

        a {{
            color: var(--primary-color);
            text-decoration: none;
            transition: var(--transition);
        }}

        a:hover {{
            color: var(--primary-dark);
            text-decoration: underline;
        }}

        .header-content {{
            width: 100%;
            max-width: var(--max-width);
            margin: 0 auto;
            padding: 0 var(--spacing);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            position: relative;
        }}

        .title-container {{
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            padding: 0 100px;
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}

        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            border-radius: 20px;
            background: var(--card-bg);
            color: var(--text-color);
            cursor: pointer;
            font-size: 0.9em;
            transition: var(--transition);
            outline: none;
        }}

        .filter-btn:hover {{
            background: var(--primary-light);
            color: white;
            border-color: var(--primary-light);
        }}

        .filter-btn.active {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }}

        @media (max-width: 768px) {{
            .filter-buttons {{
                flex-wrap: wrap;
                justify-content: center;
            }}
            .title-container {{
                padding: 0;
                flex-direction: column;
                gap: 10px;
            }}
            .back-btn {{
                position: static;
                transform: none;
            }}
        }}

        .back-btn {{
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            border-radius: 20px;
            background: var(--card-bg);
            color: var(--text-color);
            cursor: pointer;
            font-size: 0.9em;
            transition: var(--transition);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 5px;
            box-shadow: var(--shadow-sm);
        }}

        .back-btn:hover {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
            box-shadow: var(--shadow-md);
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="title-container">
                <h1><span class="emoji">🛡️</span>{title}</h1>
                <a href="https://blog.897010.xyz/" class="back-btn" target="_blank">
                    <span>🏠</span>
                    <span>返回主页</span>
                </a>
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" data-risk="ALL">全部</button>
                <button class="filter-btn" data-risk="CRITICAL">严重</button>
                <button class="filter-btn" data-risk="HIGH">高危</button>
                <button class="filter-btn" data-risk="MEDIUM">中危</button>
                <button class="filter-btn" data-risk="LOW">低危</button>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="list-container">
            {content}
        </div>
    </div>
    <footer class="footer">
        <p>本文内容由 AI 自动生成，仅供参考和学习交流。使用本文信息需自行承担风险和责任。</p>
    </footer>

<script>
// 监听滚动事件，添加header动画
window.addEventListener('scroll', function() {{
    const header = document.querySelector('.header');
    if (window.scrollY > 50) {{
        header.classList.add('scrolled');
    }} else {{
        header.classList.remove('scrolled');
    }}
}});

function showModal(id) {{
    const modal = document.getElementById(id);
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    setTimeout(() => modal.style.opacity = '1', 10);
}}

function closeModal(id) {{
    const modal = document.getElementById(id);
    modal.style.opacity = '0';
    setTimeout(() => {{
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }}, 300);
}}

window.onclick = function(event) {{
    if (event.target.classList.contains('modal')) {{
        const modal = event.target;
        modal.style.opacity = '0';
        setTimeout(() => {{
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }}, 300);
    }}
}}

// 添加卡片动画
document.addEventListener('DOMContentLoaded', function() {{
    const items = document.querySelectorAll('.cve-item');
    items.forEach((item, index) => {{
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        setTimeout(() => {{
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }}, index * 100);
    }});
}});

// 添加筛选和排序功能
document.addEventListener('DOMContentLoaded', function() {{
    const filterButtons = document.querySelectorAll('.filter-btn');
    const items = document.querySelectorAll('.cve-item');

    // 风险等级权重映射
    const riskWeight = {{
        'CRITICAL': 5,
        'HIGH': 4,
        'MEDIUM': 3,
        'LOW': 2,
        'INFO': 1
    }};

    // 获取元素的风险等级
    function getRiskLevel(item) {{
        const riskSpan = item.querySelector('.cve-meta span:first-child');
        return riskSpan.textContent.trim();
    }}

    // 排序函数
    function sortItems() {{
        const container = document.querySelector('.list-container');
        const itemsArray = Array.from(items);
        
        itemsArray.sort((a, b) => {{
            const riskA = getRiskLevel(a);
            const riskB = getRiskLevel(b);
            return (riskWeight[riskB] || 0) - (riskWeight[riskA] || 0);
        }});

        itemsArray.forEach(item => container.appendChild(item));
    }}

    // 初始排序
    sortItems();

    // 筛选功能
    filterButtons.forEach(button => {{
        button.addEventListener('click', () => {{
            // 更新按钮状态
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const selectedRisk = button.getAttribute('data-risk');
            
            items.forEach(item => {{
                const itemRisk = getRiskLevel(item);
                if (selectedRisk === 'ALL' || itemRisk === selectedRisk) {{
                    item.style.display = 'flex';
                    // 添加动画效果
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(20px)';
                    setTimeout(() => {{
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }}, 50);
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }});
    }});
}});
</script>
</body>
</html>
'''

    def parse_markdown(self, md_content):
        # 解析文档标题和日期
        title_match = re.search(r'^## (.+?)\n\((.*?)\)', md_content)
        if title_match:
            title = title_match.group(1)
            date = title_match.group(2)
        else:
            title = "安全分析报告"
            date = datetime.now().strftime("%Y-%m-%d")

        # 分割每个CVE条目
        cve_sections = re.split(r'\n### ', md_content)[1:]

        return title, date, cve_sections

    def convert_table_to_html(self, table_lines):
        html = '<div class="table-container"><table>'

        # 添加表头行
        html += '''<tr>
            <th>属性</th>
            <th>详情</th>
        </tr>'''

        for line in table_lines:
            if '|' not in line:
                continue
            if '----' in line:
                continue
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells and len(cells) == 2:
                processed_cells = []
                for cell in cells:
                    # 如果单元格已经包含链接，直接使用
                    if '<a href=' in cell:
                        processed_cells.append(f"<td>{cell}</td>")
                        continue

                    # 先处理Markdown链接
                    cell = markdown.markdown(cell)
                    # 移除markdown生成的<p>标签
                    cell = cell.replace('<p>', '').replace('</p>', '')
                    # 确保链接在新标签页打开
                    cell = cell.replace(
                        '<a href="', '<a target="_blank" rel="noopener noreferrer" href="')
                    # 移除多余的引号
                    cell = cell.replace('`', '')
                    processed_cells.append(f"<td>{cell}</td>")
                html += f'<tr>{"".join(processed_cells)}</tr>'
        html += '</table></div>'
        return html

    def convert_to_html(self, md_content):
        title, date, cve_sections = self.parse_markdown(md_content)

        html_content = ""
        modals_content = ""

        for i, section in enumerate(cve_sections):
            lines = section.strip().split('\n')
            cve_title = lines[0]

            # 提取基本信息用于预览
            basic_info = {}
            repo_link = None
            cve_id = None

            # 先查找仓库链接
            for j, line in enumerate(lines):
                if '#### 📦 相关仓库' in line and j + 2 < len(lines):
                    # 在仓库信息部分寻找链接
                    repo_match = re.search(r'\[(.*?)\]\((.*?)\)', lines[j + 2])
                    if repo_match:
                        repo_link = repo_match.group(2)
                        break

            # 提取其他基本信息
            table_lines = []
            in_basic_info = False
            for line in lines:
                if line.startswith('#### 📌'):
                    in_basic_info = True
                    continue
                elif line.startswith('####'):
                    in_basic_info = False
                    continue

                if in_basic_info and '|' in line:
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if len(cells) == 2:
                        key = cells[0].strip()
                        # 跳过序号和发现内容的行
                        if key.isdigit() or key == '序号' or key == '发现内容':
                            continue
                        value = cells[1].strip('` ')
                        if key == 'CVE编号':
                            cve_id = value
                            if repo_link:
                                value = f'<a href="{repo_link}" target="_blank" rel="noopener noreferrer">{value}</a>'
                        basic_info[key] = value
                        # 重建表格行，保留链接
                        table_lines.append(f"| {key} | {value} |")

            # 确定风险等级样式
            risk_level = basic_info.get("风险等级", "").strip('`')
            risk_class = {
                "CRITICAL": "risk-critical",
                "HIGH": "risk-high",
                "MEDIUM": "risk-medium",
                "LOW": "risk-low",
                "INFO": "risk-info"
            }.get(risk_level, "risk-info")

            # 选择图标
            if cve_title.strip().startswith('CVE-') or 'CVE-' in cve_title:
                icon = '🔥'
            else:
                icon = random.choice(
                    ['⚡', '🔍', '🚨', '💻', '🌐', '🔐', '📡', '🎯', '🛡️', '⚠️'])

            # 生成列表项
            item_html = f'''
            <div class="cve-item" onclick="showModal('modal-{i}')">
                <div class="cve-icon">{icon}</div>
                <div class="cve-info">
                    <h3 class="cve-title">{cve_title}</h3>
                    <div class="cve-meta">
                        <span class="{risk_class}">{risk_level}</span>
                        <span>{basic_info.get("最后更新", "N/A")}</span>
                    </div>
                </div>
            </div>'''

            # 生成详细信息模态框
            modal_html = f'''
            <div id="modal-{i}" class="modal">
                <div class="modal-content">
                    <span class="close-btn" onclick="closeModal('modal-{i}')">&times;</span>
                    <h2>{cve_title}</h2>
                    {self.process_section_details(lines[1:], table_lines)}
                </div>
            </div>'''

            html_content += item_html
            modals_content += modal_html

        return self.html_template.format(
            title=f"{title} ({date})",
            content=f"{html_content}{modals_content}"
        )

    def process_section_details(self, lines, table_lines):
        html = ""
        current_section = None
        section_content = []

        for line in lines:
            if line.startswith('#### 📌'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '基本信息'
                section_content = []
            elif line.startswith('#### 仓库信息'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '仓库信息'
                section_content = []
            elif line.startswith('#### 💡'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '分析概述'
                section_content = []
            elif line.startswith('#### 🔍'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '关键发现'
                section_content = []
            elif line.startswith('#### 🛠️'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '技术细节'
                section_content = []
            elif line.startswith('#### 🎯'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '受影响组件'
                section_content = []
            elif line.startswith('#### ⚡'):
                if section_content:
                    html += self.process_section(current_section,
                                                 section_content, table_lines)
                current_section = '价值评估'
                section_content = []
            elif current_section:
                section_content.append(line)

        if section_content:
            html += self.process_section(current_section,
                                         section_content, table_lines)

        return html

    def process_section(self, section_type, content, table_lines):
        content_text = '\n'.join(content)

        if '基本信息' in section_type:
            # 特殊处理基本信息中的仓库名称链接
            table_html = self.convert_table_to_html(table_lines)
            return f'''
            <div class="card">
                <h3><span class="emoji-title">📌</span>基本信息</h3>
                {table_html}
            </div>'''
        elif '仓库信息' in section_type:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">📦</span>仓库信息</h3>
                {markdown.markdown(content_text)}
            </div>'''
        elif '分析概述' in section_type:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">💡</span>分析概述</h3>
                <p>{content_text.strip()}</p>
            </div>'''
        elif '关键发现' in section_type:
            # 只保留发现内容的列表
            findings = []
            for line in content:
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if len(cells) == 2 and cells[0].isdigit():
                        findings.append(cells[1])

            findings_html = '<ol class="findings-list">'
            for finding in findings:
                findings_html += f'<li>{finding}</li>'
            findings_html += '</ol>'

            return f'''
            <div class="card">
                <h3><span class="emoji-title">📋</span>发现内容</h3>
                <style>
                    .findings-list {{
                        padding-left: 20px;
                        margin: 0;
                    }}
                    .findings-list li {{
                        margin: 10px 0;
                        line-height: 1.6;
                        color: var(--text-color);
                    }}
                </style>
                {findings_html}
            </div>'''
        elif '技术细节' in section_type:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">🛠️</span>技术细节</h3>
                {markdown.markdown(content_text)}
            </div>'''
        elif '受影响组件' in section_type:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">🎯</span>受影响组件</h3>
                {markdown.markdown(content_text)}
            </div>'''
        elif '价值评估' in section_type:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">⚡</span>价值评估</h3>
                {markdown.markdown(content_text)}
            </div>'''
        else:
            return f'''
            <div class="card">
                <h3><span class="emoji-title">📌</span>{section_type}</h3>
                {markdown.markdown(content_text)}
            </div>'''

    def convert_file(self, input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = self.convert_to_html(md_content)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def generate_html_index(md_files):
    index_html = "<html><body><h1>选择日期</h1><ul>"
    for md_file in md_files:
        date = os.path.splitext(md_file)[0]  # 获取文件名作为日期
        index_html += f'<li><a href="{date}.html">{date}</a></li>'
    index_html += "</ul></body></html>"
    return index_html


def convert_md_to_html(md_file):
    """将 Markdown 文件转换为 HTML"""
    logger.info(f"开始转换文件: {md_file}")

    try:
        # 创建转换器实例
        converter = VulnerabilityReportConverter()

        # 生成输出 HTML 文件名
        output_file = md_file.replace(
            'ai_analysis', 'ai_html').replace('.md', '.html')

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)

        # 调用转换器的 convert_file 方法
        html_content = converter.convert_file(md_file, output_file)

        logger.info(f"成功转换文件: {md_file} 到 {output_file}")
        return html_content  # 返回 HTML 内容
    except Exception as e:
        logger.error(f"转换文件时出错: {str(e)}")
        return None


def main():
    md_files = [f for f in os.listdir() if f.endswith('.md')]

    # 生成索引 HTML
    index_html = generate_html_index(md_files)
    with open("index.html", "w", encoding="utf-8") as index_file:
        index_file.write(index_html)

    for md_file in md_files:
        convert_md_to_html(md_file)


if __name__ == "__main__":
    main()
