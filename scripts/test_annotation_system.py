#!/usr/bin/env python3
"""
AI Baby Monitor - 视频标注系统测试脚本

用于测试标注系统的各项功能
"""

import os
import tempfile
import shutil
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_baby_monitor.annotation.video_scanner import VideoScanner
from src.ai_baby_monitor.annotation.annotation_manager import AnnotationManager
from src.ai_baby_monitor.annotation.frame_extractor import FrameExtractor

def create_test_videos(test_dir: str):
    """创建测试视频文件"""
    import cv2
    import numpy as np
    
    test_dir = Path(test_dir)
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试视频文件名和对应的标签
    test_videos = [
        ("baby_safe_001.mp4", "safe"),
        ("dangerous_climbing_002.mp4", "dangerous"),
        ("baby_crying_003.mp4", "crying"),
        ("normal_playing_004.mp4", "playing"),
        ("baby_sleeping_005.mp4", "sleeping"),
    ]
    
    for filename, expected_label in test_videos:
        filepath = test_dir / filename
        
        # 创建简单的测试视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(filepath), fourcc, 1.0, (320, 240))
        
        # 创建5帧的测试视频
        for i in range(5):
            # 创建不同颜色的帧来模拟不同场景
            if expected_label == "safe":
                frame = np.full((240, 320, 3), (0, 255, 0), dtype=np.uint8)  # 绿色
            elif expected_label == "dangerous":
                frame = np.full((240, 320, 3), (0, 0, 255), dtype=np.uint8)  # 红色
            elif expected_label == "crying":
                frame = np.full((240, 320, 3), (255, 0, 0), dtype=np.uint8)  # 蓝色
            else:
                frame = np.full((240, 320, 3), (255, 255, 255), dtype=np.uint8)  # 白色
            
            # 添加文字
            cv2.putText(frame, expected_label, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            out.write(frame)
        
        out.release()
        print(f"创建测试视频: {filepath}")

def test_video_scanner():
    """测试视频扫描器"""
    print("\n" + "="*50)
    print("测试视频扫描器...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_videos(temp_dir)
        
        scanner = VideoScanner(temp_dir)
        videos = scanner.scan_videos()
        videos = scanner.validate_video_files(videos)
        
        print(f"找到 {len(videos)} 个视频文件")
        
        for video in videos:
            print(f"文件: {video['filename']}")
            print(f"原始标签: {video['label']}")
            print(f"时长: {video.get('duration', 0):.1f}s")
            print("-" * 30)
        
        assert len(videos) == 5, f"期望找到5个视频，实际找到{len(videos)}个"
        print("✅ 视频扫描器测试通过")

def test_annotation_manager():
    """测试标注管理器"""
    print("\n" + "="*50)
    print("测试标注管理器...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AnnotationManager(temp_dir)
        
        # 测试保存和加载
        test_annotations = {
            "test_video_001": {
                "label": "safe",
                "confidence": 0.9,
                "notes": "测试标注",
                "reviewer": "测试员"
            }
        }
        
        success = manager.save_annotations(test_annotations)
        assert success, "保存标注失败"
        
        loaded_annotations = manager.load_annotations()
        assert loaded_annotations == test_annotations, "加载标注数据不匹配"
        
        # 测试更新标注
        manager.update_annotation(
            "test_video_001", 
            "dangerous", 
            0.8, 
            "标签更新测试", 
            "测试员"
        )
        
        updated = manager.load_annotations()
        assert updated["test_video_001"]["label"] == "dangerous", "标签更新失败"
        
        # 测试历史记录
        history = manager.get_change_history("test_video_001")
        assert len(history) > 0, "历史记录为空"
        
        print("✅ 标注管理器测试通过")

def test_frame_extractor():
    """测试帧抽取器"""
    print("\n" + "="*50)
    print("测试帧抽取器...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_videos(temp_dir)
        
        extractor = FrameExtractor()
        
        # 测试帧抽取
        test_video = Path(temp_dir) / "baby_safe_001.mp4"
        keyframes = extractor.extract_keyframes(str(test_video), num_frames=3)
        
        print(f"抽取到 {len(keyframes)} 个关键帧")
        
        # 测试保存帧
        output_dir = Path(temp_dir) / "frames"
        saved_files = extractor.save_frames(keyframes, str(output_dir))
        
        print(f"保存了 {len(saved_files)} 个帧文件")
        assert len(saved_files) == len(keyframes), "保存帧数量不匹配"
        
        # 测试缩略图创建
        thumbnail_path = Path(temp_dir) / "thumbnail.jpg"
        success = extractor.create_thumbnail(str(test_video), str(thumbnail_path))
        assert success and thumbnail_path.exists(), "缩略图创建失败"
        
        print("✅ 帧抽取器测试通过")

def test_integration():
    """测试系统集成"""
    print("\n" + "="*50)
    print("测试系统集成...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试环境
        video_dir = Path(temp_dir) / "videos"
        annotation_dir = Path(temp_dir) / "annotations"
        
        video_dir.mkdir()
        create_test_videos(str(video_dir))
        
        # 测试完整流程
        scanner = VideoScanner(str(video_dir))
        manager = AnnotationManager(str(annotation_dir))
        extractor = FrameExtractor()
        
        # 扫描视频
        videos = scanner.scan_videos()
        videos = scanner.validate_video_files(videos)
        
        # 标注一些视频
        for video in videos[:2]:
            manager.update_annotation(
                video['filename'],
                "verified_safe" if video['label'] == "safe" else "verified_dangerous",
                0.95,
                "人工验证",
                "测试员"
            )
        
        # 抽取关键帧
        for video in videos[:1]:
            keyframes = extractor.extract_keyframes(video['filepath'], 2)
            assert len(keyframes) > 0, "关键帧抽取失败"
        
        # 验证标注
        annotations = manager.load_annotations()
        assert len(annotations) == 2, "标注数量不正确"
        
        # 导出数据
        export_file = Path(temp_dir) / "test_export.json"
        success = manager.export_annotations(str(export_file), "json")
        assert success and export_file.exists(), "数据导出失败"
        
        print("✅ 系统集成测试通过")

def main():
    """运行所有测试"""
    print("🧪 AI Baby Monitor - 视频标注系统测试")
    print("="*60)
    
    try:
        test_video_scanner()
        test_annotation_manager()
        test_frame_extractor()
        test_integration()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("✅ 视频标注系统运行正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()