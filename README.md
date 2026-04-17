# 🛡️ Campus Guard AI — 智能校园安全管理系统

<p align="center">
  <b>基于 YOLOv11 + CBAM 注意力机制的实时校园安全监测平台</b><br>
  <sub>图片检测 · 视频检测 · 摄像头实时流 · Web 端可视化</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/YOLOv11-Latest-green?logo=yolo&logoColor=white" alt="YOLO">
  <img src="https://img.shields.io/badge/Flask-2.0+-orange?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/OpenCV-4.x-red?logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</p>

---

## 📋 项目简介

Campus Guard AI 是一套面向校园场景的智能安全监测系统，基于 Ultralytics YOLOv11 目标检测框架，结合 CBAM（Convolutional Block Attention Module）注意力机制，实现对校园关键区域的 **7 类安全隐患** 实时识别与告警。

系统以 Flask 为后端、HTML/CSS/JS 为前端，提供开箱即用的 Web 检测平台，支持 **单张图片检测、视频逐帧分析、本地摄像头实时监控、远程浏览器摄像头推流** 四种使用模式。

### 🎯 检测能力

| 类别 ID | 类别名称 | 中文说明 | 告警级别 |
|:-------:|----------|----------|:--------:|
| 0 | `stranger` | 外来人员/行人入侵 | ⚠️ 警告 |
| 1 | `no_helmet` | 未佩戴安全帽 | 🚨 违规 |
| 2 | `helmet` | 正常佩戴安全帽 | ✅ 正常 |
| 3 | `fire_hydrant` | 消防栓状态 | ℹ️ 监测 |
| 4 | `stranger_vehicle` | 外来车辆 | ⚠️ 警告 |
| 5 | `abnormal_behavior` | 异常行为（打架等） | 🚨 报警 |
| 6 | `missing_extinguisher` | 灭火器状态 | ℹ️ 监测 |

### 🏗️ 区域化检测策略

不同校园区域关注的安全重点不同，系统内置了区域过滤规则，只对当前区域相关的类别进行检测，减少误报、提升效率：

| 部署区域 | 关注类别 |
|----------|----------|
| 🔬 工程实验室 | 人员、安全帽、消防栓、异常行为、灭火器 |
| 🚪 校门进出口 / 停车场 | 人员、车辆、异常行为 |
| 🏠 宿舍区域 | 人员、异常行为、灭火器 |
| 🏫 教学楼走廊 / 消防通道 | 人员、消防栓、异常行为、灭火器 |
| 🏟️ 操场 / 公共区域 | 人员、安全帽、异常行为 |

---

## 🖥️ 系统功能

### 检测模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 📷 图片检测 | 上传 JPG/PNG 图片，返回标注结果 | 单帧分析、历史照片审查 |
| 🎬 视频检测 | 上传 MP4/AVI 视频，逐帧分析并输出结果视频 | 录像回放分析 |
| 📹 本地摄像头 | 服务器直连摄像头，MJPEG 流实时推送 | 固定监控点位 |
| 📱 远程推流 | 浏览器调用摄像头，WebRTC 推流至后端检测 | 手机/平板移动巡检 |

### 界面特性

- 🌑 暗色主题，长时间监控不伤眼
- 📊 实时统计面板（检测总数、正常区域、预警事件、模型精度）
- 📋 右侧检测报告面板，自动区分正常/异常并高亮
- 🎬 LIVE 标识 + 扫描线动画，实时感拉满
- 📱 响应式布局，手机/平板/桌面均可使用

---

## 🚀 快速开始

### 环境要求

| 项目 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.8 | 3.10+ |
| pip | 20.0 | 最新版 |
| 操作系统 | Windows 10 / Ubuntu 18.04 / macOS 10.15 | — |
| GPU（可选） | CUDA 11.0 | CUDA 12.0 + cuDNN 8 |

### 步骤 1：安装 Python

**Windows：**
1. 访问 [python.org/downloads](https://www.python.org/downloads/)
2. 下载 Python 3.8+ 安装包
3. 运行安装，**务必勾选 ☑️ "Add Python to PATH"**

**Ubuntu / Debian：**
```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

**macOS：**
```bash
brew install python3
```

### 步骤 2：获取项目

```bash
git clone https://github.com/liangdaxiaisme-eng/campus-security-system.git
cd campus-security-system
```

或直接下载 ZIP 解压。

### 步骤 3：创建虚拟环境（推荐）

```bash
python3 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 步骤 4：安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

如果下载慢，可使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 5：确认模型权重

模型文件 `weights/best.pt` 已包含在仓库中，无需额外下载。

如需用自己的数据重新训练：
```bash
# 使用 Ultralytics CLI 训练
yolo detect train data=your_dataset.yaml model=yolo11n.pt epochs=100 imgsz=640
# 训练完成后将 runs/detect/train/weights/best.pt 复制到 weights/ 目录
```

### 步骤 6：启动系统

```bash
python app.py
```

启动成功后终端会显示：
```
模型加载成功！YOLOv11 双引擎摄像头实时流已就绪。
未检测到 SSL 证书，使用 HTTP（摄像头推流功能需 HTTPS）
 * Running on http://0.0.0.0:5000
```

### 步骤 7：访问

| 访问方式 | 地址 |
|----------|------|
| 本机 | http://127.0.0.1:5000 |
| 局域网 | http://[你的IP]:5000 |

---

## 📖 详细使用指南

### 🖼️ 图片检测

1. 打开网页，确认左上角「部署区域」选择正确
2. 在上传区拖拽或点击上传图片（支持 JPG / PNG / JPEG）
3. 点击 **「AI 智能检测」** 按钮
4. 等待 2-5 秒，左侧显示标注结果图，右侧显示检测报告
5. 异常项（违规/警报）会以红色高亮显示

### 🎬 视频检测

1. 选择视频文件（支持 MP4 / AVI / MOV，最大 100MB）
2. 点击「AI 智能检测」
3. 系统逐帧分析，完成后自动播放结果视频
4. 右侧报告汇总视频中出现过的所有检测类别

### 📹 本地摄像头（服务器直连）

> ⚠️ 仅在服务器本机有摄像头时可用

1. 点击 **「本地摄像头」** 按钮
2. 系统通过 MJPEG 流实时推送检测画面
3. 点击「停止监控」返回主页

### 📱 远程推流（手机/平板巡检）

> ⚠️ 需要 HTTPS 访问（浏览器安全策略限制）

1. 点击 **「实时监控」** 按钮
2. 浏览器请求摄像头权限，允许后开始推流
3. 每一帧发送至后端进行检测，结果实时回传显示
4. 可切换前后摄像头

**启用 HTTPS：**
将 SSL 证书 `cert.pem` 和 `key.pem` 放在项目根目录，系统自动启用 HTTPS。

快速生成自签名证书（仅开发测试用）：
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

---

## ⚙️ 配置说明

### 修改监听地址与端口

编辑 `app.py` 末尾：
```python
app.run(host='0.0.0.0', port=5000)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `host` | `'0.0.0.0'` | 允许局域网访问 |
| `host` | `'127.0.0.1'` | 仅本机访问 |
| `port` | `8080` | 修改为任意可用端口 |

### 上传大小限制

默认 100MB，修改 `app.py` 中：
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 改为你需要的值
```

### 更换检测模型

1. 将新的 `.pt` 模型文件放入 `weights/` 目录
2. 修改 `app.py` 顶部的模型路径：
```python
MODEL_PATH = 'weights/你的模型.pt'
```

### 添加新的检测区域

在 `app.py` 的 `AREA_RULES` 字典中添加：
```python
AREA_RULES = {
    # 现有区域...
    '仓库': [0, 3, 5, 6],  # 自定义区域和对应的类别ID
}
```
然后在 `templates/index.html` 的 `<select>` 中添加对应的 `<option>`。

---

## 🛠️ 常见问题

<details>
<summary><b>Q1: ModuleNotFoundError: No module named 'xxx'</b></summary>

依赖未安装完整，执行：
```bash
pip install ultralytics flask opencv-python numpy
```
</details>

<details>
<summary><b>Q2: 摄像头无法打开 / 黑屏</b></summary>

1. 确认摄像头未被其他程序占用（Zoom、微信视频等）
2. 本地摄像头模式下，检查设备号（默认 0），可在代码中修改 `cv2.VideoCapture(0)` 的参数
3. 远程推流模式下，必须使用 HTTPS 访问
</details>

<details>
<summary><b>Q3: 检测速度慢 / 卡顿</b></summary>

1. 安装 GPU 版 PyTorch：`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`
2. 使用更小的模型（如 `yolo11n.pt`）
3. 降低输入分辨率
4. 远程推流帧率受限于网络，局域网内体验最佳
</details>

<details>
<summary><b>Q4: 局域网其他设备无法访问</b></summary>

1. 确认 `app.run(host='0.0.0.0')` 已设置
2. 检查防火墙：
   - **Windows**：以管理员运行 CMD → `netsh firewall add portopening TCP 5000 webserver`
   - **Ubuntu**：`sudo ufw allow 5000/tcp`
3. 确认设备在同一局域网
</details>

<details>
<summary><b>Q5: 远程推流提示"浏览器不支持"或"摄像头权限被拒绝"</b></summary>

1. 必须通过 HTTPS 访问（见上方「启用 HTTPS」章节）
2. 浏览器需支持 `getUserMedia` API（Chrome / Safari / Edge 均支持）
3. 首次使用时浏览器会弹出权限请求，点击「允许」
4. 如果之前拒绝过，需在浏览器设置中重置摄像头权限
</details>

<details>
<summary><b>Q6: 视频检测结果没有声音</b></summary>

当前版本输出视频不保留原始音轨，这是 OpenCV VideoWriter 的已知限制。如需保留音频，可使用 ffmpeg 后处理：
```bash
ffmpeg -i result.mp4 -i original.mp4 -c copy -map 0:v:0 -map 1:a:0 output_with_audio.mp4
```
</details>

---

## 📁 项目结构

```
campus-security-system/
├── app.py                        # Flask 主程序（路由 + 检测逻辑）
├── detect_video.py               # 独立视频检测脚本（命令行用）
├── requirements.txt              # Python 依赖清单
│
├── weights/
│   └── best.pt                   # 训练好的 YOLOv11 模型权重
│
├── templates/
│   └── index.html                # 前端页面模板（暗色主题 UI）
│
├── static/                       # 运行时自动生成
│   ├── uploads/                  # 用户上传的原始文件
│   └── results/                  # 检测结果图片/视频
│
├── cert.pem                      # SSL 证书（可选，启用 HTTPS 用）
├── key.pem                       # SSL 私钥（可选，启用 HTTPS 用）
└── README.md                     # 本文件
```

### 核心文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | 主程序，包含所有路由：首页、图片/视频检测、MJPEG 流、WebRTC 推流检测 |
| `detect_video.py` | 独立脚本，用于命令行批量处理视频：`python detect_video.py input.mp4 output.mp4` |
| `templates/index.html` | 前端页面，包含完整的 CSS 样式和 JavaScript 逻辑（区域选择、上传、实时监控、报告面板） |
| `weights/best.pt` | 自定义训练的 YOLOv11 模型，覆盖 7 类校园安全目标 |

---

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 主编程语言 |
| YOLOv11 + CBAM | Latest | 目标检测核心模型 |
| Ultralytics | ≥ 8.3.0 | YOLO 训练/推理框架 |
| Flask | 2.0+ | Web 后端框架 |
| OpenCV (cv2) | 4.x | 图像/视频处理 |
| NumPy | Latest | 数组运算 |
| HTML / CSS / JS | — | 前端界面 |
| WebRTC | — | 浏览器摄像头推流 |

---

## 📊 模型性能

| 指标 | 值 |
|------|-----|
| 模型架构 | YOLOv11n（Nano 轻量版）+ CBAM |
| mAP@0.5 | 97.8% |
| mAP@0.5:0.95 | 73.2% |
| Precision | 94.6% |
| Recall | 91.5% |
| 推理速度（GPU） | ~15ms / 帧 |
| 推理速度（CPU） | ~80ms / 帧 |

> 以上数据基于自定义校园数据集测试，实际表现因硬件和场景而异。

---

## 🗺️ 后续规划

- [ ] 接入邮件/钉钉/企业微信告警推送
- [ ] 历史检测记录存储与查询
- [ ] 多摄像头画面同屏对比
- [ ] 检测结果自动生成日报/周报
- [ ] 支持 RTSP/ONVIF 协议接入专业监控摄像头
- [ ] 模型在线热更新

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -m 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

---

## 📄 许可证

[MIT License](LICENSE)

---

## 👨‍💻 作者

**老梁**

---

<p align="center">
  <sub>如果觉得有帮助，请给个 ⭐ Star 支持一下！</sub>
</p>
