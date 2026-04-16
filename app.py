import os
from flask import Flask, render_template, request, Response, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import base64

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

MODEL_PATH = 'weights/best.pt'
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    print("模型加载成功！全平台双引擎摄像头实时流已就绪。")
else:
    model = None
    print(f"警告: 未找到模型文件 {MODEL_PATH}")

CLASS_MAP_CN = {
    'stranger': '外来人员/行人',
    'no_helmet': '⚠️违规：未戴安全帽',
    'helmet': '正常戴安全帽',
    'fire_hydrant': '消防栓',
    'stranger_vehicle': '外来车辆',
    'abnormal_behavior': '⚠️警报：异常行为(打架)',
    'missing_extinguisher': '灭火器'
}

AREA_RULES = {
    'lab': [0, 1, 2, 3, 5, 6], 
    'gate': [0, 4, 5], 
    'public': [0, 3, 5, 6] 
}

def get_allowed_classes(areas_list):
    allowed = set()
    for area in areas_list:
        if area in AREA_RULES:
            allowed.update(AREA_RULES[area])
    return list(allowed) if allowed else list(set(AREA_RULES['public']))

@app.route('/')
def index():
    return render_template('index.html')

# ================= 静态文件与视频处理逻辑 =================
@app.route('/detect', methods=['POST'])
def detect():
    if 'file' not in request.files or request.files['file'].filename == '':
        return "未选择文件", 400

    file = request.files['file']
    if file and model:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        selected_areas = request.form.getlist('areas')
        allowed_classes = get_allowed_classes(selected_areas)

        if ext in ['jpg', 'jpeg', 'png']:
            results = model.predict(source=filepath, save=False, classes=allowed_classes)
            res_img = results[0].plot(labels=True, conf=True)
            res_path = os.path.join(app.config['RESULT_FOLDER'], file.filename)
            cv2.imwrite(res_path, res_img)

            detected_items = []
            names_dict = model.names
            for box in results[0].boxes:
                cls_name_cn = CLASS_MAP_CN.get(names_dict[int(box.cls[0])], names_dict[int(box.cls[0])])
                detected_items.append({'type': cls_name_cn, 'confidence': f"{round(float(box.conf[0]) * 100, 2)}%"})

            return render_template('index.html', uploaded_file=file.filename, result_file=file.filename, detected_items=detected_items, file_type='image')

        elif ext in ['mp4', 'avi', 'mov']:
            out_filename = file.filename.rsplit('.', 1)[0] + '_result.mp4'
            res_path = os.path.join(app.config['RESULT_FOLDER'], out_filename)

            cap = cv2.VideoCapture(filepath)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25

            fourcc = cv2.VideoWriter_fourcc(*'avc1')
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
            return render_template('index.html', uploaded_file=file.filename, result_file=out_filename, detected_items=detected_items, file_type='video')

        else:
            return "不支持的文件格式", 400
    return "系统错误或模型未加载", 500

# ================= 引擎1：本地后台硬件直调逻辑 =================
def gen_camera_frames(allowed_classes):
    cap = cv2.VideoCapture(0) 
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            if model:
                results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
                frame = results[0].plot(labels=True, conf=True)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/live_camera', methods=['POST'])
def live_camera():
    selected_areas = request.form.getlist('areas')
    areas_str = ",".join(selected_areas) if selected_areas else "public"
    return render_template('index.html', live_mode=True, areas_str=areas_str, engine='local')

@app.route('/video_feed')
def video_feed():
    areas_str = request.args.get('areas', 'public')
    selected_areas = areas_str.split(',')
    allowed_classes = get_allowed_classes(selected_areas)
    return Response(gen_camera_frames(allowed_classes), mimetype='multipart/x-mixed-replace; boundary=frame')

# ================= 引擎2：跨设备前端推流接口 =================
@app.route('/web_camera_ui', methods=['POST'])
def web_camera_ui():
    selected_areas = request.form.getlist('areas')
    areas_str = ",".join(selected_areas) if selected_areas else "public"
    return render_template('index.html', live_mode=True, areas_str=areas_str, engine='web')

@app.route('/detect_web_frame', methods=['POST'])
def detect_web_frame():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'error': '无图像数据'}), 400

    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    selected_areas = data.get('areas', 'public').split(',')
    allowed_classes = get_allowed_classes(selected_areas)

    if model:
        results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
        annotated_frame = results[0].plot(labels=True, conf=True)

        detected_items = []
        for box in results[0].boxes:
            cls_name_cn = CLASS_MAP_CN.get(model.names[int(box.cls[0])], model.names[int(box.cls[0])])
            detected_items.append({'type': cls_name_cn})

        unique_items = list({v['type']:v for v in detected_items}.values())

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        encoded_img = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'image': 'data:image/jpeg;base64,' + encoded_img,
            'items': unique_items
        })
    return jsonify({'error': '模型未加载'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
