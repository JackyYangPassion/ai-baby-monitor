"""
标注管理器
负责标签文件的读写和管理
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnnotationManager:
    """管理视频标签的读写和更新"""
    
    def __init__(self, annotation_dir: str = "annotations"):
        self.annotation_dir = Path(annotation_dir)
        self.annotation_dir.mkdir(exist_ok=True)
        self.annotations_file = self.annotation_dir / "labels.json"
        self.history_file = self.annotation_dir / "history.json"
        
    def load_annotations(self) -> Dict[str, Dict[str, any]]:
        """
        加载所有标注信息
        
        Returns:
            Dict: 标注信息，键为文件名，值为标注详情
        """
        if not self.annotations_file.exists():
            return {}
            
        try:
            with open(self.annotations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载标注文件失败: {e}")
            return {}
    
    def save_annotations(self, annotations: Dict[str, Dict[str, any]]) -> bool:
        """
        保存标注信息到文件
        
        Args:
            annotations: 标注信息字典
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.annotations_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存标注文件失败: {e}")
            return False
    
    def get_annotation(self, filename: str) -> Optional[Dict[str, any]]:
        """
        获取指定文件的标注信息
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 标注信息，如果不存在返回None
        """
        annotations = self.load_annotations()
        return annotations.get(filename)
    
    def update_annotation(self, filename: str, label: str, confidence: float = 1.0, 
                         notes: str = "", reviewer: str = "") -> bool:
        """
        更新标注信息
        
        Args:
            filename: 文件名
            label: 新标签
            confidence: 置信度 (0-1)
            notes: 备注信息
            reviewer: 标注人员
            
        Returns:
            bool: 是否更新成功
        """
        annotations = self.load_annotations()
        
        old_label = annotations.get(filename, {}).get('label', '')
        
        annotations[filename] = {
            'label': label,
            'confidence': confidence,
            'notes': notes,
            'reviewer': reviewer,
            'updated_at': datetime.now().isoformat(),
            'original_label': old_label if old_label else label
        }
        
        success = self.save_annotations(annotations)
        
        if success and old_label and old_label != label:
            self._record_change(filename, old_label, label, reviewer, notes)
            
        return success
    
    def _record_change(self, filename: str, old_label: str, new_label: str, 
                      reviewer: str, notes: str):
        """
        记录标签变更历史
        
        Args:
            filename: 文件名
            old_label: 原标签
            new_label: 新标签
            reviewer: 标注人员
            notes: 备注
        """
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append({
                'filename': filename,
                'old_label': old_label,
                'new_label': new_label,
                'reviewer': reviewer,
                'notes': notes,
                'timestamp': datetime.now().isoformat()
            })
            
            # 限制历史记录数量，保留最近1000条
            history = history[-1000:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"记录变更历史失败: {e}")
    
    def get_change_history(self, filename: str = None) -> List[Dict[str, any]]:
        """
        获取标签变更历史
        
        Args:
            filename: 指定文件名，None表示获取所有历史
            
        Returns:
            List: 变更历史列表
        """
        if not self.history_file.exists():
            return []
            
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            if filename:
                history = [h for h in history if h['filename'] == filename]
                
            return history
            
        except Exception as e:
            logger.error(f"获取变更历史失败: {e}")
            return []
    
    def export_annotations(self, output_file: str, format: str = "csv") -> bool:
        """
        导出标注信息
        
        Args:
            output_file: 输出文件路径
            format: 输出格式 (csv, json)
            
        Returns:
            bool: 是否导出成功
        """
        annotations = self.load_annotations()
        
        if format.lower() == "csv":
            return self._export_csv(annotations, output_file)
        elif format.lower() == "json":
            return self._export_json(annotations, output_file)
        else:
            logger.error(f"不支持的导出格式: {format}")
            return False
    
    def _export_csv(self, annotations: Dict[str, Dict[str, any]], 
                   output_file: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['filename', 'label', 'confidence', 'notes', 
                               'reviewer', 'updated_at'])
                
                for filename, info in annotations.items():
                    writer.writerow([
                        filename,
                        info.get('label', ''),
                        info.get('confidence', ''),
                        info.get('notes', ''),
                        info.get('reviewer', ''),
                        info.get('updated_at', '')
                    ])
                    
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False
    
    def _export_json(self, annotations: Dict[str, Dict[str, any]], 
                    output_file: str) -> bool:
        """导出为JSON格式"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """
        获取标注统计信息
        
        Returns:
            Dict: 统计信息
        """
        annotations = self.load_annotations()
        history = self.get_change_history()
        
        label_counts = {}
        for info in annotations.values():
            label = info.get('label', 'unknown')
            label_counts[label] = label_counts.get(label, 0) + 1
            
        return {
            'total_files': len(annotations),
            'label_distribution': label_counts,
            'total_changes': len(history),
            'last_update': max(
                [info.get('updated_at', '') for info in annotations.values()],
                default=''
            )
        }