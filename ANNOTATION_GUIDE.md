# 🎥 AI婴儿监控 - 视频标注系统使用指南

## 📋 功能概述

这个标注系统专门用于验证和纠正婴儿监控视频的标签，支持以下功能：

- 📁 批量扫描视频文件并解析标签
- 🖼️ 自动抽取关键帧用于验证
- 🌐 Web界面进行可视化标注
- 🏷️ 标签验证和纠正
- 📊 标注统计和历史记录
- 📤 数据导出（JSON/CSV格式）

## 🚀 快速开始

### 1. 安装依赖

确保已安装项目依赖：

```bash
pip install streamlit opencv-python numpy
```

### 2. 准备视频文件

将需要标注的MP4视频文件放在指定目录中，建议使用以下命名格式：

```
videos/
├── baby_safe_001.mp4          # 自动识别为 "safe"
├── dangerous_climbing_002.mp4  # 自动识别为 "dangerous"
├── baby_crying_003.mp4        # 自动识别为 "crying"
├── normal_playing_004.mp4     # 自动识别为 "playing"
└── baby_sleeping_005.mp4      # 自动识别为 "sleeping"
```

### 3. 启动Web界面

```bash
# 启动Web界面
python scripts/annotation_system.py

# 或指定视频目录
python scripts/annotation_system.py --video-dir ./my_videos

# 或使用命令行方式
python scripts/annotation_system.py web
```

### 4. 使用Web界面

1. 在浏览器中打开 `http://localhost:8501`
2. 在左侧配置面板中设置视频目录
3. 点击"扫描视频文件"按钮
4. 从视频列表中选择要标注的视频
5. 查看关键帧预览
6. 选择正确的标签并添加备注
7. 保存标注结果

## 🎯 支持的标签类型

| 标签 | 描述 | 示例场景 |
|------|------|----------|
| `safe` | 安全状态 | 婴儿正常玩耍、睡觉 |
| `dangerous` | 危险行为 | 攀爬、接近危险物品 |
| `crying` | 哭泣 | 婴儿在哭 |
| `playing` | 玩耍 | 开心玩耍 |
| `sleeping` | 睡觉 | 安静睡眠 |
| `eating` | 进食 | 吃饭或喝奶 |
| `climbing` | 攀爬 | 试图爬出婴儿床 |
| `unknown` | 未知状态 | 无法确定 |

## 🛠️ 命令行使用

### 扫描视频文件
```bash
python scripts/annotation_system.py scan --video-dir ./videos
```

### 抽取关键帧
```bash
python scripts/annotation_system.py extract \
  --video-dir ./videos \
  --output-dir ./frames \
  --num-frames 5 \
  --method uniform
```

### 导出标注数据
```bash
python scripts/annotation_system.py export \
  --output annotations.json \
  --format json
```

## 📊 文件结构

```
annotations/
├── labels.json       # 标注结果
└── history.json      # 变更历史

extracted_frames/     # 抽取的关键帧（可选）
├── video_001/
│   ├── video_001_frame_000000.jpg
│   └── video_001_frame_000010.jpg
└── video_002/
    └── ...

temp/thumbnails/      # 缩略图缓存
└── *.jpg
```

## 🔧 高级配置

### Web界面参数

在Web界面左侧可以配置：
- **视频目录**: 包含MP4文件的文件夹路径
- **每视频抽取帧数**: 1-10帧
- **帧抽取方法**: 
  - 均匀分布：在整个视频中均匀抽取
  - 场景变化：基于画面变化抽取
  - 中间部分：从视频中间部分抽取
- **标注人员**: 记录谁进行了标注

### 自定义标签

如需添加新的标签类型，可以修改 `annotation_ui.py` 中的 `label_options` 列表：

```python
self.label_options = [
    "safe", "dangerous", "crying", "playing", 
    "sleeping", "eating", "climbing", "unknown",
    "your_custom_label"  # 添加自定义标签
]
```

## 🧪 测试系统

运行测试确保系统正常工作：

```bash
python scripts/test_annotation_system.py
```

## 📈 使用技巧

1. **批量处理**: 一次处理多个视频文件，提高工作效率
2. **关键词搜索**: 在Web界面中使用搜索功能快速定位特定视频
3. **标签筛选**: 可以按标签类型筛选视频，便于分类审核
4. **变更历史**: 查看每个视频的标签修改记录，便于追踪
5. **置信度标注**: 为不确定的标签设置较低的置信度
6. **团队协作**: 多人标注时使用标注人员字段区分

## ⚠️ 注意事项

1. **数据备份**: 定期备份 `annotations/` 目录下的标注文件
2. **文件命名**: 使用有意义的文件名便于标签自动识别
3. **视频格式**: 系统支持MP4、AVI、MOV、MKV格式
4. **分辨率**: 建议在标注前确认视频可以正常播放
5. **权限**: 确保有读写视频目录和标注文件的权限

## 🤝 故障排除

### 常见问题

**Q: 找不到视频文件**
- 检查视频目录路径是否正确
- 确认文件扩展名为支持的格式
- 检查文件是否损坏

**Q: Web界面无法启动**
- 确认已安装Streamlit: `pip install streamlit`
- 检查端口8501是否被占用
- 查看日志文件 `annotation_system.log`

**Q: 标注数据丢失**
- 检查 `annotations/` 目录权限
- 查看是否有备份文件
- 检查日志中的错误信息

### 获取帮助

如有问题，请查看：
- 日志文件：`annotation_system.log`
- 项目文档：README.md
- 测试脚本：`scripts/test_annotation_system.py`

## 📞 技术支持

系统维护：AI Baby Monitor团队
更新时间：2024年7月