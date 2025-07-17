#!/usr/bin/env python3
"""
AI Baby Monitor - 视频标注系统主程序

运行命令:
    python scripts/annotation_system.py --video-dir ./videos
    python scripts/annotation_system.py --web  # 启动Web界面

功能:
1. 扫描视频文件并解析标签
2. 抽取关键帧用于验证
3. 提供Web界面进行标注验证和纠正
4. 导出标注结果
"""

import argparse
import logging
import sys
from pathlib import Path
import streamlit as st

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_baby_monitor.annotation.video_scanner import VideoScanner
from src.ai_baby_monitor.annotation.annotation_manager import AnnotationManager
from src.ai_baby_monitor.annotation.frame_extractor import FrameExtractor

def setup_logging(level=logging.INFO):
    """设置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('annotation_system.log', encoding='utf-8')
        ]
    )

def scan_videos(video_dir: str):
    """扫描视频文件"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"开始扫描视频目录: {video_dir}")
    
    scanner = VideoScanner(video_dir)
    videos = scanner.scan_videos()
    videos = scanner.validate_video_files(videos)
    
    if not videos:
        logger.error("未找到有效的视频文件")
        return
    
    print(f"\n📹 找到 {len(videos)} 个有效视频文件:")
    print("-" * 80)
    
    for video in videos:
        print(f"文件名: {video['filename']}")
        print(f"路径: {video['filepath']}")
        print(f"原始标签: {video['label']}")
        print(f"时长: {video.get('duration', 0):.1f}s")
        print(f"帧数: {video.get('frame_count', 0)}")
        print(f"分辨率: {video.get('width', 0)}x{video.get('height', 0)}")
        print("-" * 80)

def extract_frames(video_dir: str, output_dir: str, num_frames: int = 5, 
                  method: str = "uniform"):
    """抽取所有视频的关键帧"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"开始抽取关键帧，目录: {video_dir}")
    
    scanner = VideoScanner(video_dir)
    extractor = FrameExtractor()
    
    videos = scanner.scan_videos()
    videos = scanner.validate_video_files(videos)
    
    if not videos:
        logger.error("未找到有效的视频文件")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for video in videos:
        logger.info(f"处理视频: {video['filename']}")
        
        keyframes = extractor.extract_keyframes(
            video['filepath'], 
            num_frames, 
            method
        )
        
        if keyframes:
            video_output_dir = output_path / video['filename']
            video_output_dir.mkdir(exist_ok=True)
            
            saved_files = extractor.save_frames(
                keyframes, 
                str(video_output_dir),
                prefix=video['filename']
            )
            
            logger.info(f"保存了 {len(saved_files)} 个关键帧到 {video_output_dir}")

def export_annotations(output_file: str, format: str = "json"):
    """导出标注数据"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    manager = AnnotationManager()
    success = manager.export_annotations(output_file, format)
    
    if success:
        logger.info(f"标注数据已导出到: {output_file}")
    else:
        logger.error("导出失败")

def launch_web_interface():
    """启动Web界面"""
    setup_logging()
    
    # 使用streamlit运行Web界面
    import subprocess
    
    web_script = project_root / "src" / "ai_baby_monitor" / "annotation" / "annotation_ui.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(web_script)
        ])
    except KeyboardInterrupt:
        print("\n🛑 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI Baby Monitor - 视频标注系统")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 扫描命令
    scan_parser = subparsers.add_parser('scan', help='扫描视频文件')
    scan_parser.add_argument('--video-dir', required=True, 
                           help='视频文件目录')
    
    # 抽取帧命令
    extract_parser = subparsers.add_parser('extract', help='抽取关键帧')
    extract_parser.add_argument('--video-dir', required=True, 
                              help='视频文件目录')
    extract_parser.add_argument('--output-dir', default='extracted_frames',
                              help='输出目录 (默认: extracted_frames)')
    extract_parser.add_argument('--num-frames', type=int, default=5,
                              help='每视频抽取帧数 (默认: 5)')
    extract_parser.add_argument('--method', choices=['uniform', 'scene_change', 'middle'],
                              default='uniform', help='帧抽取方法 (默认: uniform)')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出标注数据')
    export_parser.add_argument('--output', required=True, help='输出文件路径')
    export_parser.add_argument('--format', choices=['json', 'csv'], 
                             default='json', help='输出格式 (默认: json)')
    
    # Web界面命令
    web_parser = subparsers.add_parser('web', help='启动Web界面')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        scan_videos(args.video_dir)
    elif args.command == 'extract':
        extract_frames(
            args.video_dir, 
            args.output_dir, 
            args.num_frames, 
            args.method
        )
    elif args.command == 'export':
        export_annotations(args.output, args.format)
    elif args.command == 'web':
        launch_web_interface()
    else:
        # 如果没有指定命令，启动Web界面
        print("🚀 启动视频标注Web界面...")
        print("💡 使用 --help 查看所有可用命令")
        launch_web_interface()

if __name__ == "__main__":
    main()