"""
标注验证和纠正的Web界面
使用Streamlit创建交互式标注界面
"""

import streamlit as st
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
import cv2
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ai_baby_monitor.annotation.video_scanner import VideoScanner
from src.ai_baby_monitor.annotation.annotation_manager import AnnotationManager
from src.ai_baby_monitor.annotation.frame_extractor import FrameExtractor

logger = logging.getLogger(__name__)

class AnnotationUI:
    """标注验证和纠正的Web界面"""
    
    def __init__(self):
        self.video_scanner = None
        self.annotation_manager = AnnotationManager()
        self.frame_extractor = FrameExtractor()
        
        # 标签选项
        self.label_options = [
            "safe", "dangerous", "crying", "playing", 
            "sleeping", "eating", "climbing", "unknown"
        ]
        
    def run(self):
        """运行Streamlit应用"""
        st.set_page_config(
            page_title="AI Baby Monitor - 视频标注系统",
            page_icon="👶",
            layout="wide"
        )
        
        st.title("🎥 婴儿监控视频标注系统")
        st.markdown("---")
        
        # 侧边栏配置
        with st.sidebar:
            st.header("📁 配置")
            
            # 视频目录选择
            default_dir = "./videos"
            video_dir = st.text_input("视频文件目录", value=default_dir)
            
            # 帧抽取配置
            num_frames = st.slider("每视频抽取帧数", 1, 10, 5)
            frame_method = st.selectbox(
                "帧抽取方法", 
                ["uniform", "scene_change", "middle"],
                format_func=lambda x: {
                    "uniform": "均匀分布",
                    "scene_change": "场景变化",
                    "middle": "中间部分"
                }[x]
            )
            
            # 标注人员
            reviewer = st.text_input("标注人员名称", value="标注员")
            
            if st.button("🔄 扫描视频文件", type="primary"):
                st.session_state.video_dir = video_dir
                st.session_state.num_frames = num_frames
                st.session_state.frame_method = frame_method
                st.session_state.reviewer = reviewer
                st.rerun()
        
        # 主界面
        if not hasattr(st.session_state, 'video_dir'):
            st.info("👈 请在左侧配置视频目录和参数")
            return
        
        # 扫描视频文件
        if not self.video_scanner or self.video_scanner.video_dir != Path(st.session_state.video_dir):
            self.video_scanner = VideoScanner(st.session_state.video_dir)
        
        videos = self.video_scanner.scan_videos()
        videos = self.video_scanner.validate_video_files(videos)
        
        if not videos:
            st.error("❌ 未找到有效的视频文件")
            st.info("请确保目录中包含MP4等格式的视频文件")
            return
        
        # 显示统计信息
        self._show_statistics(videos)
        
        # 视频列表和标注界面
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_video = self._show_video_list(videos)
        
        with col2:
            if selected_video:
                self._show_annotation_interface(selected_video)
    
    def _show_statistics(self, videos: List[Dict[str, any]]):
        """显示统计信息"""
        stats = self.annotation_manager.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总视频数", len(videos))
        
        with col2:
            st.metric("已标注数", stats.get('total_files', 0))
        
        with col3:
            st.metric("总修改次数", stats.get('total_changes', 0))
        
        with col4:
            label_dist = stats.get('label_distribution', {})
            if label_dist:
                most_common = max(label_dist.items(), key=lambda x: x[1])
                st.metric("最常见标签", f"{most_common[0]} ({most_common[1]})")
    
    def _show_video_list(self, videos: List[Dict[str, any]]) -> Optional[Dict[str, any]]:
        """显示视频列表"""
        st.header("📹 视频列表")
        
        # 搜索和筛选
        search_term = st.text_input("搜索文件名", placeholder="输入关键词...")
        
        # 标签筛选
        all_labels = set()
        annotations = self.annotation_manager.load_annotations()
        
        for video in videos:
            annotation = annotations.get(video['filename'])
            if annotation:
                all_labels.add(annotation.get('label', ''))
            else:
                all_labels.add(video['label'])
        
        selected_labels = st.multiselect(
            "按标签筛选", 
            sorted(all_labels),
            default=[]
        )
        
        # 过滤视频
        filtered_videos = videos
        if search_term:
            filtered_videos = [v for v in filtered_videos 
                             if search_term.lower() in v['filename'].lower()]
        
        if selected_labels:
            filtered_videos = []
            for video in videos:
                annotation = annotations.get(video['filename'])
                current_label = annotation.get('label', '') if annotation else video['label']
                if current_label in selected_labels:
                    filtered_videos.append(video)
        
        # 显示视频列表
        selected_video = None
        
        for video in filtered_videos:
            filename = video['filename']
            filepath = video['filepath']
            
            # 获取当前标签
            annotation = annotations.get(filename)
            if annotation:
                current_label = annotation.get('label', '')
                is_modified = annotation.get('label', '') != video['label']
                status_icon = "✅" if not is_modified else "⚠️"
            else:
                current_label = video['label']
                is_modified = False
                status_icon = "⏳"
            
            # 创建缩略图
            thumbnail_path = f"temp/thumbnails/{filename}.jpg"
            Path("temp/thumbnails").mkdir(parents=True, exist_ok=True)
            
            if not os.path.exists(thumbnail_path):
                self.frame_extractor.create_thumbnail(filepath, thumbnail_path)
            
            # 显示视频信息
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if os.path.exists(thumbnail_path):
                    st.image(thumbnail_path, width=80)
                else:
                    st.image("🎥", width=80)
            
            with col2:
                if st.button(f"{status_icon} {filename}", key=f"btn_{filename}"):
                    selected_video = video
            
            st.caption(f"标签: {current_label} | 原始: {video['label']}")
            
            if is_modified:
                st.caption(f"修改原因: {annotation.get('notes', '无')}")
            
            st.markdown("---")
        
        return selected_video
    
    def _show_annotation_interface(self, video: Dict[str, any]):
        """显示标注界面"""
        st.header(f"🎬 {video['filename']}")
        
        # 获取当前标注
        annotations = self.annotation_manager.load_annotations()
        current_annotation = annotations.get(video['filename'])
        
        if current_annotation:
            current_label = current_annotation.get('label', '')
            current_notes = current_annotation.get('notes', '')
            current_confidence = current_annotation.get('confidence', 1.0)
        else:
            current_label = video['label']
            current_notes = ""
            current_confidence = 1.0
        
        # 视频信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("时长", f"{video.get('duration', 0):.1f}s")
        with col2:
            st.metric("帧数", video.get('frame_count', 0))
        with col3:
            st.metric("FPS", f"{video.get('fps', 0):.1f}")
        
        # 关键帧展示
        st.subheader("📸 关键帧预览")
        
        keyframes = self.frame_extractor.extract_keyframes(
            video['filepath'], 
            st.session_state.num_frames,
            st.session_state.frame_method
        )
        
        if keyframes:
            cols = st.columns(min(len(keyframes), 4))
            
            for i, (col, keyframe) in enumerate(zip(cols, keyframes)):
                with col:
                    # 转换颜色空间用于显示
                    frame_rgb = cv2.cvtColor(keyframe['frame'], cv2.COLOR_BGR2RGB)
                    st.image(frame_rgb, caption=f"帧 {keyframe['frame_number']}")
        
        # 标注表单
        st.subheader("🏷️ 标签标注")
        
        with st.form("annotation_form"):
            # 标签选择
            new_label = st.selectbox(
                "选择正确的标签",
                self.label_options,
                index=self.label_options.index(current_label) if current_label in self.label_options else 0
            )
            
            # 置信度
            confidence = st.slider("标注置信度", 0.0, 1.0, current_confidence)
            
            # 备注
            notes = st.text_area(
                "标注备注",
                value=current_notes,
                placeholder="请描述为什么要修改这个标签..."
            )
            
            # 提交按钮
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.form_submit_button("💾 保存标注", type="primary"):
                    success = self.annotation_manager.update_annotation(
                        video['filename'],
                        new_label,
                        confidence,
                        notes,
                        st.session_state.reviewer
                    )
                    
                    if success:
                        st.success("✅ 标注已保存")
                        st.rerun()
                    else:
                        st.error("❌ 保存失败")
            
            with col2:
                if st.form_submit_button("🔙 重置为原始标签"):
                    success = self.annotation_manager.update_annotation(
                        video['filename'],
                        video['label'],
                        1.0,
                        "重置为原始标签",
                        st.session_state.reviewer
                    )
                    
                    if success:
                        st.success("✅ 已重置为原始标签")
                        st.rerun()
                    else:
                        st.error("❌ 重置失败")
            
            with col3:
                if st.form_submit_button("📊 查看变更历史"):
                    st.session_state.show_history = True
        
        # 变更历史
        if st.session_state.get('show_history', False):
            self._show_change_history(video['filename'])
    
    def _show_change_history(self, filename: str):
        """显示变更历史"""
        st.subheader("📝 变更历史")
        
        history = self.annotation_manager.get_change_history(filename)
        
        if not history:
            st.info("暂无变更历史")
            return
        
        for change in reversed(history):
            st.markdown(f"""
            **{change['timestamp']}**
            - **修改人**: {change['reviewer']}
            - **旧标签**: `{change['old_label']}`
            - **新标签**: `{change['new_label']}`
            - **备注**: {change['notes']}
            """)
            st.markdown("---")
        
        if st.button("关闭历史记录"):
            st.session_state.show_history = False
            st.rerun()
    
    def export_data(self):
        """导出标注数据"""
        st.sidebar.markdown("---")
        st.sidebar.header("📊 数据导出")
        
        export_format = st.sidebar.selectbox("导出格式", ["JSON", "CSV"])
        
        if st.sidebar.button("导出标注数据"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"annotations_{timestamp}.{export_format.lower()}"
            
            success = self.annotation_manager.export_annotations(
                filename, 
                export_format.lower()
            )
            
            if success:
                st.sidebar.success(f"✅ 导出成功: {filename}")
            else:
                st.sidebar.error("❌ 导出失败")


def main():
    """主函数"""
    ui = AnnotationUI()
    ui.run()


if __name__ == "__main__":
    main()