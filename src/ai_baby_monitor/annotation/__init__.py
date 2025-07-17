"""
AI Baby Monitor - Video Annotation System

视频标注系统，用于验证和纠正婴儿监控视频的标签
"""

from .video_scanner import VideoScanner
from .annotation_manager import AnnotationManager
from .frame_extractor import FrameExtractor

# 延迟导入AnnotationUI以避免Streamlit依赖问题
try:
    from .annotation_ui import AnnotationUI
    __all__ = ['VideoScanner', 'AnnotationManager', 'FrameExtractor', 'AnnotationUI']
except ImportError:
    __all__ = ['VideoScanner', 'AnnotationManager', 'FrameExtractor']