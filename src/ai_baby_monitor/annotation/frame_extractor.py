"""
帧抽取器
从视频中抽取关键帧用于标注验证
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FrameExtractor:
    """从视频中抽取关键帧"""
    
    def __init__(self):
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv'}
    
    def extract_keyframes(self, video_path: str, num_frames: int = 5, 
                         method: str = "uniform") -> List[Dict[str, any]]:
        """
        从视频中抽取关键帧
        
        Args:
            video_path: 视频文件路径
            num_frames: 抽取的帧数量
            method: 抽取方法 ("uniform", "scene_change", "middle")
            
        Returns:
            List[Dict]: 关键帧信息列表，每个包含:
                - frame: 帧数据 (numpy数组)
                - frame_number: 帧号
                - timestamp: 时间戳
                - filename: 保存的文件名
        """
        if not Path(video_path).exists():
            logger.error(f"视频文件不存在: {video_path}")
            return []
            
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return []
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames == 0:
                logger.error(f"视频文件为空: {video_path}")
                return []
            
            # 根据方法选择帧位置
            if method == "uniform":
                frame_positions = self._get_uniform_frames(total_frames, num_frames)
            elif method == "scene_change":
                frame_positions = self._get_scene_change_frames(cap, total_frames, num_frames)
            elif method == "middle":
                frame_positions = self._get_middle_frames(total_frames, num_frames)
            else:
                frame_positions = self._get_uniform_frames(total_frames, num_frames)
            
            keyframes = []
            for frame_num in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    timestamp = frame_num / fps if fps > 0 else 0
                    
                    keyframes.append({
                        'frame': frame,
                        'frame_number': int(frame_num),
                        'timestamp': timestamp,
                        'filename': f"frame_{int(frame_num):06d}.jpg"
                    })
            
            cap.release()
            return keyframes
            
        except Exception as e:
            logger.error(f"抽取关键帧失败 {video_path}: {e}")
            return []
    
    def _get_uniform_frames(self, total_frames: int, num_frames: int) -> List[int]:
        """均匀抽取帧"""
        if total_frames <= num_frames:
            return list(range(total_frames))
        
        step = total_frames // num_frames
        frames = [i * step for i in range(num_frames)]
        
        # 确保包含最后一帧
        if frames[-1] != total_frames - 1:
            frames[-1] = total_frames - 1
            
        return frames
    
    def _get_scene_change_frames(self, cap: cv2.VideoCapture, total_frames: int, 
                               num_frames: int) -> List[int]:
        """基于场景变化抽取帧"""
        # 简化的场景变化检测：计算相邻帧的差异
        frames = []
        prev_frame = None
        scene_changes = []
        
        for i in range(0, total_frames, max(1, total_frames // 100)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if ret and prev_frame is not None:
                # 计算帧间差异
                diff = cv2.absdiff(prev_frame, frame)
                diff_score = np.mean(diff)
                
                if diff_score > 30:  # 阈值可以根据需要调整
                    scene_changes.append(i)
            
            prev_frame = frame
        
        # 如果没有检测到场景变化，使用均匀抽样
        if not scene_changes:
            return self._get_uniform_frames(total_frames, num_frames)
        
        # 选择场景变化中的代表性帧
        if len(scene_changes) <= num_frames:
            return scene_changes
        else:
            step = len(scene_changes) // num_frames
            return [scene_changes[i * step] for i in range(num_frames)]
    
    def _get_middle_frames(self, total_frames: int, num_frames: int) -> List[int]:
        """从中间部分抽取帧"""
        start_frame = max(0, total_frames // 3)
        end_frame = min(total_frames, total_frames * 2 // 3)
        
        if end_frame - start_frame <= num_frames:
            return list(range(start_frame, end_frame))
        
        step = (end_frame - start_frame) // num_frames
        frames = [start_frame + i * step for i in range(num_frames)]
        
        return frames
    
    def save_frames(self, keyframes: List[Dict[str, any]], 
                   output_dir: str, prefix: str = "") -> List[str]:
        """
        保存关键帧到文件
        
        Args:
            keyframes: 关键帧列表
            output_dir: 输出目录
            prefix: 文件名前缀
            
        Returns:
            List[str]: 保存的文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for i, keyframe in enumerate(keyframes):
            frame = keyframe['frame']
            frame_num = keyframe['frame_number']
            
            if prefix:
                filename = f"{prefix}_frame_{frame_num:06d}.jpg"
            else:
                filename = keyframe['filename']
                
            filepath = output_path / filename
            
            try:
                cv2.imwrite(str(filepath), frame)
                saved_files.append(str(filepath))
                logger.info(f"保存帧: {filepath}")
            except Exception as e:
                logger.error(f"保存帧失败 {filepath}: {e}")
        
        return saved_files
    
    def create_thumbnail(self, video_path: str, output_path: str, 
                        size: Tuple[int, int] = (320, 240)) -> bool:
        """
        创建视频缩略图
        
        Args:
            video_path: 视频文件路径
            output_path: 缩略图输出路径
            size: 缩略图尺寸
            
        Returns:
            bool: 是否创建成功
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            
            # 获取中间帧作为缩略图
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame = total_frames // 2
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # 调整尺寸
                thumbnail = cv2.resize(frame, size)
                cv2.imwrite(output_path, thumbnail)
                cap.release()
                return True
            
            cap.release()
            return False
            
        except Exception as e:
            logger.error(f"创建缩略图失败 {video_path}: {e}")
            return False
    
    def get_video_preview(self, video_path: str, max_width: int = 800) -> Optional[np.ndarray]:
        """
        获取视频预览帧（调整大小后的中间帧）
        
        Args:
            video_path: 视频文件路径
            max_width: 最大宽度
            
        Returns:
            np.ndarray: 预览帧数据
        """
        try:
            keyframes = self.extract_keyframes(video_path, num_frames=1, method="middle")
            if not keyframes:
                return None
            
            frame = keyframes[0]['frame']
            
            # 调整大小以保持宽高比
            height, width = frame.shape[:2]
            if width > max_width:
                scale = max_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            return frame
            
        except Exception as e:
            logger.error(f"获取视频预览失败 {video_path}: {e}")
            return None