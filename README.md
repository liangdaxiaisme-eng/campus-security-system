# 🌐 智能校园安全管理系统

基于 YOLOv8 的实时校园安全监测系统，支持图片检测、视频检测和摄像头实时检测。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![YOLO](https://img.shields.io/badge/YOLOv8-Latest-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-orange)

## 📋 项目简介

本项目是一个基于深度学习的智能校园安全管理系统的 Web 部署版本，采用 YOLOv8 作为目标检测框架，能够实时检测校园内的安全隐患，包括：

- 🔥 火焰识别
- 🧑 陌生人入侵检测
- ⛑️ 未佩戴安全帽检测
- 🚒 消防栓状态监测
- 🚗 异常车辆检测
- 📦 物品丢失检测

## 🖥️ 系统功能

| 功能 | 说明 |
|------|------|
| 📷 图片检测 | 上传单张图片进行目标检测 |
| 🎬 视频检测 | 上传视频文件进行分析 |
| 📹 摄像头检测 | 连接实时摄像头进行监控 |

## 🚀 快速开始（小白教程）

### 步骤 1：安装 Python 环境

**Windows 系统：**
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本
3. 运行安装程序，**记得勾选"Add Python to PATH"**

**Ubuntu/Debian 系统：**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**macOS 系统：**
```bash
# 方式1：使用 Homebrew（推荐）
brew install python3

# 方式2：官网下载
# https://www.python.org/downloads/macos/
```

### 步骤 2：下载项目

```bash
# 方式1：克隆仓库
git clone https://github.com/liangdaxiaisme-eng/campus-security-system.git
cd campus-security-system

# 方式2：直接下载 Zip
# 访问 https://github.com/liangdaxiaisme-eng/campus-security-system
# 点击绿色的 "Code" 按钮 -> "Download ZIP"
```

### 步骤 3：安装依赖

```bash
# 如果有虚拟环境，先激活（可选）
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

**注意**：如果遇到安装错误，尝试：
```bash
pip install --upgrade pip
pip install ultralytics flask opencv-python
```

### 步骤 4：下载模型权重

模型权重文件 `best.pt` 已在项目的 `weights/` 文件夹中。

如果需要重新训练，请参考训练代码。

### 步骤 5：运行系统

```bash
# 启动 Web 服务
python app.py
```

启动成功后，会显示类似以下信息：
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

### 步骤 6：访问系统

打开浏览器，访问：
- 本地：http://127.0.0.1:5000
- 局域网其他设备：http://[你的IP地址]:5000

## 📖 使用教程

### 🖼️ 图片检测
1. 打开网页后，点击"图片检测"标签
2. 点击"选择文件"按钮
3. 选择要检测的图片（支持 jpg、png、jpeg）
4. 点击"开始检测"
5. 等待几秒钟，查看检测结果

### 🎬 视频检测
1. 切换到"视频检测"标签
2. 选择视频文件（支持 mp4、avi）
3. 点击"开始检测"
4. 系统会逐帧分析并保存结果

### 📹 摄像头检测
1. 切换到"摄像头检测"标签
2. 确保电脑已连接摄像头
3. 点击"开启摄像头"
4. 实时画面将显示检测结果

## ⚙️ 配置说明

### 修改监听地址

在 `app.py` 中找到：
```python
app.run(host='0.0.0.0', port=5000)
```

- `host='0.0.0.0'` - 允许局域网访问
- `host='127.0.0.1'` - 仅本地访问

### 修改端口

```python
app.run(port=5000)  # 改成你想要的端口
```

### 修改检测模型

如果有自己的模型：
1. 将模型文件放入 `weights/` 文件夹
2. 修改 `app.py` 中的模型路径：
```python
model_path = 'weights/你的模型.pt'
```

## 🛠️ 常见问题

### ❓ Q1: 运行报错 "ModuleNotFoundError: No module named 'xxx'"

**解决**：安装缺少的模块
```bash
pip install xxx
```

### ❓ Q2: 摄像头无法打开

**解决**：
1. 检查摄像头是否被其他程序占用
2. 尝试使用外部摄像头（需要修改代码中的摄像头编号）

### ❓ Q3: 检测速度很慢

**解决**：
1. 使用 GPU 版本的 PyTorch
2. 减小输入图片/视频的分辨率
3. 使用更小的模型（如 yolov8n.pt）

### ❓ Q4: 模型权重下载失败

**解决**：
1. 检查网络连接
2. 尝试使用代理
3. 手动下载：https://github.com/liangdaxiaisme-eng/campus-security-system/raw/main/weights/best.pt

### ❓ Q5: 局域网无法访问

**解决**：
1. 确保防火墙允许对应端口
2. 确认 `app.run(host='0.0.0.0')` 设置正确

### Windows 防火墙设置：
```bash
# 以管理员身份运行 CMD
netsh firewall add portopening TCP 5000 webserver
```

### Ubuntu 防火墙设置：
```bash
sudo ufw allow 5000/tcp
```

## 📁 项目结构

```
campus_security_deploy/
├── app.py                    # Flask Web 应用主程序
├── detect_video.py           # 视频检测脚本
├── requirements.txt          # Python 依赖列表
│
├── weights/                  # 模型权重
│   └── best.pt              # 训练好的 YOLO 模型
│
├── templates/                # HTML 模板
│   └── index.html           # 前端页面
│
└── static/                   # 静态资源（运行时自动生成）
    ├── uploads/             # 上传的图片/视频
    └── results/             # 检测结果图片
```

## 🔧 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 编程语言 |
| YOLOv8 | 目标检测模型 |
| Flask | Web 框架 |
| OpenCV | 图像/视频处理 |
| HTML/CSS/JS | 前端界面 |

## 📊 模型性能

- 模型：YOLOv8n（轻量化版本）
- mAP@0.5：97.8%
- mAP@0.5:0.95：73.2%
- Precision：94.6%
- Recall：91.5%

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

- 南宁理工学院
- 大数据与人工智能学院
- 指导教师：曾德真
- 学生：覃兴鹏

## 📞 联系我们

如有问题，请提交 GitHub Issue。

---

*如果觉得有帮助，请点赞 ⭐ 并分享给需要的人！*