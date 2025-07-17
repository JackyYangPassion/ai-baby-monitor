#!/usr/bin/env python3
"""
AI Baby Monitor - 简单功能测试

验证标注系统的核心功能是否正常工作
"""

import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_core_functionality():
    """测试核心功能"""
    print("🧪 测试标注系统核心功能...")
    
    try:
        from src.ai_baby_monitor.annotation.video_scanner import VideoScanner
        from src.ai_baby_monitor.annotation.annotation_manager import AnnotationManager
        from src.ai_baby_monitor.annotation.frame_extractor import FrameExtractor
        
        print("✅ 成功导入所有模块")
        
        # 测试AnnotationManager
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AnnotationManager(temp_dir)
            
            # 测试保存和加载标注
            test_data = {
                "test_video": {
                    "label": "safe",
                    "confidence": 0.9,
                    "notes": "测试"
                }
            }
            
            manager.save_annotations(test_data)
            loaded = manager.load_annotations()
            
            assert loaded["test_video"]["label"] == "safe"
            print("✅ 标注管理器功能正常")
            
            # 测试统计信息
            stats = manager.get_statistics()
            print(f"✅ 统计信息: {stats}")
            
        # 测试VideoScanner的静态方法
        scanner = VideoScanner("./nonexistent")
        label = scanner._extract_label_from_filename("baby_safe_001")
        assert label == "safe"
        print("✅ 标签解析功能正常")
        
        # 测试FrameExtractor
        extractor = FrameExtractor()
        print("✅ 帧抽取器初始化正常")
        
        print("\n🎉 所有核心功能测试通过！")
        print("系统已就绪，可以开始使用")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_core_functionality()