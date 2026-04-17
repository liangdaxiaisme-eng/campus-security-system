import os
import uuid
from flask import Flask, render_template, request, Response, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import base64

app = Flask(__name__)

# ================= 配置 =================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 上传限制

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

MODEL_PATH = 'weights/best.pt'
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    print("模型加载成功！YOLOv11 双引擎摄像头实时流已就绪。")
else:
    model = None
    print(f"警告: 未找到模型文件 {MODEL_PATH}")

# ================= 全局常量 =================
CLASS_MAP_CN = {
    'stranger': '外来人员/行人',
    'no_helmet': '⚠️违规：未戴安全帽',
    'helmet': '正常戴安全帽',
    'fire_hydrant': '消防栓',
    'stranger_vehicle': '外来车辆',
    'abnormal_behavior': '⚠️警报：异常行为(打架)',
    'missing_extinguisher': '灭火器'
}

# 区域规则：不同区域关注不同的检测类别
# 0:stranger, 1:no_helmet, 2:helmet, 3:fire_hydrant, 4:stranger_vehicle, 5:abnormal_behavior, 6:missing_extinguisher
AREA_RULES = {
    'lab':       [0, 1, 2, 3, 5, 6],   # 实验室：人员、安全帽、消防栓、异常、灭火器
    'gate':      [0, 4, 5],             # 校门/停车场：人员、车辆、异常
    'dorm':      [0, 5, 6],             # 宿舍：人员、异常、灭火器
    'corridor':  [0, 3, 5, 6],          # 走廊/消防通道：人员、消防栓、异常、灭火器
    'playground': [0, 1, 2, 5],         # 操场：人员、安全帽、异常
}

ALL_CLASSES = [0, 1, 2, 3, 4, 5, 6]


def get_allowed_classes(area_name):
    """根据区域名称获取允许的检测类别，未匹配则返回全部类别"""
    return AREA_RULES.get(area_name, ALL_CLASSES)


def safe_filename(original_name):
    """生成安全的唯一文件名，防止路径遍历和重名冲突"""
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return unique_name, ext


# ================= 页面路由 =================
@app.route('/')
def index():
    return render_template('index.html')


# ================= 图片/视频检测 =================
@app.route('/detect', methods=['POST'])
def detect():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "未选择文件", 400

    file = request.files['file']
    if not model:
        return "系统错误或模型未加载", 500

    filename, ext = safe_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    selected_area = request.form.get('area', 'playground')
    allowed_classes = get_allowed_classes(selected_area)

    if ext in ['jpg', 'jpeg', 'png']:
        results = model.predict(source=filepath, save=False, classes=allowed_classes)
        res_img = results[0].plot(labels=True, conf=True)
        res_path = os.path.join(app.config['RESULT_FOLDER'], filename)
        cv2.imwrite(res_path, res_img)

        detected_items = []
        names_dict = model.names
        for box in results[0].boxes:
            cls_name_cn = CLASS_MAP_CN.get(names_dict[int(box.cls[0])], names_dict[int(box.cls[0])])
            detected_items.append({'type': cls_name_cn, 'confidence': f"{round(float(box.conf[0]) * 100, 2)}%"})

        return render_template('index.html', uploaded_file=filename, result_file=filename,
                               detected_items=detected_items, file_type='image')

    elif ext in ['mp4', 'avi', 'mov']:
        out_filename = filename.rsplit('.', 1)[0] + '_result.mp4'
        res_path = os.path.join(app.config['RESULT_FOLDER'], out_filename)

        cap = cv2.VideoCapture(filepath)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(res_path, fourcc, fps, (width, height))

        detected_types = set()
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
            annotated_frame = results[0].plot(labels=True, conf=True)
            out.write(annotated_frame)

            for box in results[0].boxes:
                cls_name_cn = CLASS_MAP_CN.get(model.names[int(box.cls[0])], model.names[int(box.cls[0])])
                detected_types.add(cls_name_cn)

        cap.release()
        out.release()
        detected_items = [{'type': t, 'confidence': '动态捕获'} for t in detected_types]
        return render_template('index.html', uploaded_file=filename, result_file=out_filename,
                               detected_items=detected_items, file_type='video')

    else:
        return "不支持的文件格式", 400


# ================= 引擎1：本地摄像头 MJPEG 流 =================
def gen_camera_frames(allowed_classes):
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            if model:
                results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
                frame = results[0].plot(labels=True, conf=True)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()


@app.route('/live_camera', methods=['POST'])
def live_camera():
    selected_area = request.form.get('area', 'playground')
    return render_template('index.html', live_mode=True, areas_str=selected_area, engine='local')


@app.route('/video_feed')
def video_feed():
    area_str = request.args.get('areas', 'playground')
    allowed_classes = get_allowed_classes(area_str)
    return Response(gen_camera_frames(allowed_classes),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ================= 引擎2：前端 WebRTC 推流 =================
@app.route('/web_camera_ui', methods=['POST'])
def web_camera_ui():
    selected_area = request.form.get('area', 'playground')
    return render_template('index.html', live_mode=True, areas_str=selected_area, engine='web')


@app.route('/detect_web_frame', methods=['POST'])
def detect_web_frame():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'error': '无图像数据'}), 400

    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    selected_area = data.get('areas', 'playground')
    allowed_classes = get_allowed_classes(selected_area)

    if model:
        results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
        annotated_frame = results[0].plot(labels=True, conf=True)

        detected_items = []
        for box in results[0].boxes:
            cls_name_cn = CLASS_MAP_CN.get(model.names[int(box.cls[0])], model.names[int(box.cls[0])])
            detected_items.append({'type': cls_name_cn})

        unique_items = list({v['type']: v for v in detected_items}.values())

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        encoded_img = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'image': 'data:image/jpeg;base64,' + encoded_img,
            'items': unique_items
        })
    return jsonify({'error': '模型未加载'}), 500


# ================= 启动 =================
if __name__ == '__main__':
    # 检测是否存在本地 SSL 证书，有则启用 HTTPS，否则 HTTP
    ssl_cert, ssl_key = 'cert.pem', 'key.pem'
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print("检测到 SSL 证书，启用 HTTPS")
        app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert, ssl_key))
    else:
        print("未检测到 SSL 证书，使用 HTTP（摄像头推流功能需 HTTPS）")
        app.run(host='0.0.0.0', port=5000)
