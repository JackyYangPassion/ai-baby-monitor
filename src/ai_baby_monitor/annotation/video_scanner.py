"""
视频文件扫描器
扫描指定目录中的MP4文件并解析标签
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class VideoScanner:
    """扫描视频文件并解析标签信息"""
    
    def __init__(self, video_dir: str):
        self.video_dir = Path(video_dir)
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv'}
        
    def scan_videos(self) -> List[Dict[str, str]]:
        """
        扫描目录中的所有视频文件
        
        Returns:
            List[Dict]: 包含视频文件信息的列表，每个元素包含:
                - filepath: 完整文件路径
                - filename: 文件名（不含扩展名）
                - label: 从文件名解析的标签
                - extension: 文件扩展名
        """
        videos = []
        
        if not self.video_dir.exists():
            logger.error(f"视频目录不存在: {self.video_dir}")
            return videos
            
        for file_path in self.video_dir.rglob('*'):
            if file_path.suffix.lower() in self.supported_formats:
                label = self._extract_label_from_filename(file_path.stem)
                videos.append({
                    'filepath': str(file_path),
                    'filename': file_path.stem,
                    'label': label,
                    'extension': file_path.suffix.lower()
                })
                
        logger.info(f"找到 {len(videos)} 个视频文件")
        return sorted(videos, key=lambda x: x['filename'])
    
    def _extract_label_from_filename(self, filename: str) -> str:
        """
        从文件名中提取标签
        
        支持的命名格式:
        - baby_safe_001.mp4 -> "safe"
        - dangerous_climbing_002.mp4 -> "dangerous"
        - normal_playing_003.mp4 -> "normal"
        - alert_crying_004.mp4 -> "alert"
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            str: 解析出的标签
        """
        # 定义标签映射
        label_mapping = {
            'safe': ['safe', 'normal', 'good', 'ok'],
            'dangerous': ['dangerous', 'risky', 'unsafe', 'alert', 'warning'],
            'crying': ['crying', 'cry', 'tears'],
            'playing': ['playing', 'play', 'happy'],
            'sleeping': ['sleeping', 'sleep', 'asleep'],
            'eating': ['eating', 'eat', 'food'],
            'climbing': ['climbing', 'climb', 'climber']
        }
        
        filename_lower = filename.lower()
        
        # 直接匹配标签
        for standard_label, variants in label_mapping.items():
            for variant in variants:
                if variant in filename_lower:
                    return standard_label
        
        # 如果没有匹配到，使用第一个下划线前的部分作为标签
        parts = filename.split('_')
        if parts:
            return parts[0].lower()
            
        return 'unknown'
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, any]]:
        """
        获取视频文件的基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict: 视频信息，包含duration, fps, frame_count等
        """
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            return {
                'duration': duration,
                'fps': fps,
                'frame_count': frame_count,
                'width': width,
                'height': height
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败 {video_path}: {e}")
            return None
    
    def validate_video_files(self, videos: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        验证视频文件的有效性
        
        Args:
            videos: 视频文件列表
            
        Returns:
            List[Dict]: 有效的视频文件列表
        """
        valid_videos = []
        
        for video in videos:
            video_path = video['filepath']
            info = self.get_video_info(video_path)
            
            if info and info['frame_count'] > 0:
                video.update(info)
                valid_videos.append(video)
            else:
                logger.warning(f"无效的视频文件: {video_path}")
                
        return valid_videos