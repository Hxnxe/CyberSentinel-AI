import csv
import os
from datetime import datetime
import hashlib

class SecurityResultWriter:
    def __init__(self, output_dir='results'):
        self.output_dir = output_dir
        self.ensure_output_dir()
        self.written_hashes = set()  # 用于存储已写入记录的哈希值
        
    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def generate_record_hash(self, data):
        """生成记录的唯一哈希值"""
        # 使用关键字段组合生成哈希
        key_fields = [
            str(data.get('type', '')),
            str(data.get('id', '')),
            str(data.get('url', '')),
            str(data.get('summary', '')),
            str(data.get('risk_level', '')),
        ]
        hash_string = '|'.join(key_fields)
        return hashlib.md5(hash_string.encode()).hexdigest()
            
    def load_existing_hashes(self, filename):
        """加载已存在文件中的记录哈希值"""
        if not os.path.exists(filename):
            return
            
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hash_value = self.generate_record_hash(row)
                self.written_hashes.add(hash_value)
            
    def write_to_csv(self, result, source_type):
        """将分析结果写入CSV"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.join(self.output_dir, f'security_analysis_{current_date}.csv')
        
        # 统一的字段列表
        fields = [
            'timestamp',
            'type',              # 'CVE' 或 'Repository'
            'id',               # CVE ID 或仓库名称
            'url',              # 仓库URL或CVE URL
            'summary',          # 概述
            'risk_level',       # 风险等级
            'status',           # CVE的exploit_status或仓库的security_type
            'key_points',       # 关键点
            'recommendation',    # AI建议
            'value_reason',     # 价值原因
            'description',      # 详细描述
            'is_valuable',      # 是否高价值
            'technical_details', # 技术细节
            'affected_components', # 受影响组件
            'exploit_status',    # 利用状态
            'security_type',     # 安全类型
            'update_type',       # 更新类型
            'commits_analyzed',  # 分析的提交数
            'files_changed',     # 变更文件数
            'analysis_confidence', # AI分析置信度
            'mitigation_steps',   # 缓解步骤
            'impact_scope',       # 影响范围
            'detection_methods',  # 检测方法
            'references',         # 相关引用
            'tags',              # 标签
            'last_updated'       # 最后更新时间
        ]
        
        # 准备数据
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'CVE' if source_type == 'cve' else 'Repository',
            'id': result.get('cve_id') if source_type == 'cve' else result.get('repository_name'),
            'url': result.get('repository_url', ''),
            'summary': result.get('summary', ''),
            'risk_level': result.get('severity') if source_type == 'cve' else result.get('risk_level', ''),
            'status': result.get('exploit_status') if source_type == 'cve' else result.get('security_type', ''),
            'key_points': ' | '.join(result.get('key_points', [])),
            'recommendation': result.get('recommendation', ''),
            'value_reason': result.get('value_reason', ''),
            'description': result.get('description', ''),
            'is_valuable': str(result.get('is_valuable', False)),
            'technical_details': ' | '.join(result.get('technical_details', [])),
            'affected_components': ' | '.join(result.get('affected_components', [])),
            'exploit_status': result.get('exploit_status', ''),
            'security_type': result.get('security_type', ''),
            'update_type': result.get('update_type', ''),
            'commits_analyzed': result.get('commits_analyzed', 0),
            'files_changed': result.get('files_changed', 0),
            'analysis_confidence': result.get('analysis_confidence', ''),
            'mitigation_steps': ' | '.join(result.get('mitigation_steps', [])),
            'impact_scope': result.get('impact_scope', ''),
            'detection_methods': ' | '.join(result.get('detection_methods', [])),
            'references': ' | '.join(result.get('references', [])),
            'tags': ' | '.join(result.get('tags', [])),
            'last_updated': result.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        # 生成记录哈希
        record_hash = self.generate_record_hash(data)
        
        # 如果是新文件，加载已存在的哈希值
        if not self.written_hashes:
            self.load_existing_hashes(filename)
        
        # 检查是否重复
        if record_hash in self.written_hashes:
            return False
            
        # 写入CSV
        file_exists = os.path.exists(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
            
        # 添加新记录的哈希值
        self.written_hashes.add(record_hash)
        return True 