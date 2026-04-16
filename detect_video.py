"""
校园智能安全管理系统 - 视频检测脚本
用法：python3 detect_video.py 输入视频.mp4 输出结果.mp4
"""
from ultralytics import YOLO
import cv2
import sys
import os

# 类别名称和颜色
CLASS_NAMES = {
    0: 'stranger',           # 外来人员
    1: 'no_helmet',          # 未戴安全帽
    2: 'helmet',             # 戴安全帽
    3: 'fire_hydrant',       # 消防栓
    4: 'stranger_vehicle',   # 外来车辆
    5: 'abnormal_behavior',  # 异常行为
    6: 'missing_extinguisher' # 灭火器
}

# BGR颜色
COLORS = {
    0: (0, 0, 255),    # 红色 - 外来人员
    1: (0, 165, 255),  # 橙色 - 未戴安全帽
    2: (0, 255, 0),    # 绿色 - 戴安全帽
    3: (255, 0, 0),    # 蓝色 - 消防栓
    4: (255, 255, 0),  # 青色 - 外来车辆
    5: (0, 0, 128),    # 深红 - 异常行为
    6: (128, 0, 128),  # 紫色 - 灭火器
}

def detect_video(input_path, output_path, model_path='weights/best.pt', conf=0.5):
    """对视频进行逐帧检测"""
    
    # 加载模型
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    model = YOLO(model_path)
    print(f"✅ 模型加载成功: {model_path}")
    
    # 打开视频
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ 无法打开视频: {input_path}")
        return
    
    # 获取视频信息
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📹 视频信息: {width}x{height}, {fps}fps, {total_frames}帧")
    
    # 创建输出视频
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # YOLO推理
        results = model.predict(source=frame, conf=conf, verbose=False)
        
        # 画检测框
        annotated_frame = frame.copy()
        detections = results[0].boxes
        
        if detections is not None and len(detections) > 0:
            for box in detections:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                conf_val = float(box.conf[0])
                
                color = COLORS.get(cls, (255, 255, 255))
                label = f"{CLASS_NAMES.get(cls, 'unknown')} {conf_val:.2f}"
                
                # 画框和标签
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 写入输出视频
        out.write(annotated_frame)
        
        # 显示进度
        if frame_count % 30 == 0:
            progress = frame_count / total_frames * 100
            print(f"  处理进度: {frame_count}/{total_frames} ({progress:.1f}%)")
    
    cap.release()
    out.release()
    print(f"\n✅ 检测完成！输出视频: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 detect_video.py 输入视频.mp4 输出结果.mp4")
        print("可选参数: --model weights/best.pt --conf 0.5")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    model_path = 'weights/best.pt'
    conf = 0.5
    
    # 解析可选参数
    if '--model' in sys.argv:
        idx = sys.argv.index('--model')
        model_path = sys.argv[idx + 1]
    if '--conf' in sys.argv:
        idx = sys.argv.index('--conf')
        conf = float(sys.argv[idx + 1])
    
    detect_video(input_video, output_video, model_path, conf)
