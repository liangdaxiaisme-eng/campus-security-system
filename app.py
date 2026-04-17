import os
import uuid
import json
import sqlite3
import hashlib
import time
import threading
from functools import wraps
from datetime import datetime

from flask import (Flask, render_template, request, Response, jsonify,
                   session, redirect, url_for)
from ultralytics import YOLO
import cv2
import numpy as np
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', uuid.uuid4().hex)

# ================= 配置 =================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 上传限制

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

MODEL_PATH = os.environ.get('MODEL_PATH', 'weights/best.pt')
DB_PATH = os.environ.get('DB_PATH', 'campus_security.db')

# ================= 数据库 =================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            area TEXT NOT NULL,
            file_type TEXT NOT NULL,
            original_file TEXT,
            result_file TEXT,
            detected_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    # 创建默认管理员账户
    admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not admin:
        pw = hashlib.sha256('admin123'.encode()).hexdigest()
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', pw))
        print("默认管理员账户已创建: admin / admin123")
    conn.commit()
    conn.close()

init_db()

# ================= 模型加载 =================
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    print(f"模型加载成功: {MODEL_PATH}")
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

AREA_RULES = {
    'lab':       [0, 1, 2, 3, 5, 6],
    'gate':      [0, 4, 5],
    'dorm':      [0, 5, 6],
    'corridor':  [0, 3, 5, 6],
    'playground': [0, 1, 2, 5],
}
ALL_CLASSES = [0, 1, 2, 3, 4, 5, 6]

# 视频处理任务队列
video_tasks = {}  # task_id -> {status, progress, result_file, detected_items, error}


def get_allowed_classes(area_name):
    return AREA_RULES.get(area_name, ALL_CLASSES)


def safe_filename(original_name):
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return unique_name, ext


def save_detection_record(area, file_type, original_file, result_file, detected_items):
    user_id = session.get('user_id')
    conn = get_db()
    conn.execute(
        "INSERT INTO detections (user_id, area, file_type, original_file, result_file, detected_items) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, area, file_type, original_file, result_file, json.dumps(detected_items, ensure_ascii=False))
    )
    conn.commit()
    conn.close()


# ================= 认证 =================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        pw_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        user = conn.execute("SELECT id, username FROM users WHERE username=? AND password_hash=?",
                            (username, pw_hash)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        return render_template('login.html', error='用户名或密码错误')

    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ================= 页面路由 =================
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))


# ================= 检测历史 =================
@app.route('/history')
@login_required
def history():
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM detections WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (session['user_id'], per_page, offset)
    ).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) FROM detections WHERE user_id=?", (session['user_id'],)
    ).fetchone()[0]
    conn.close()

    records = []
    for r in rows:
        records.append({
            'id': r['id'],
            'area': r['area'],
            'file_type': r['file_type'],
            'result_file': r['result_file'],
            'detected_items': json.loads(r['detected_items']) if r['detected_items'] else [],
            'created_at': r['created_at']
        })

    return render_template('history.html', records=records, page=page,
                           total_pages=(total + per_page - 1) // per_page, total=total)


# ================= 图片/视频检测 =================
@app.route('/detect', methods=['POST'])
@login_required
def detect():
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if not model:
        return jsonify({'error': '模型未加载'}), 500

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

        save_detection_record(selected_area, 'image', filename, filename, detected_items)

        return jsonify({
            'success': True,
            'file_type': 'image',
            'result_file': filename,
            'detected_items': detected_items
        })

    elif ext in ['mp4', 'avi', 'mov']:
        # 异步视频处理
        task_id = uuid.uuid4().hex[:12]
        video_tasks[task_id] = {'status': 'processing', 'progress': 0, 'error': None}

        def process_video():
            try:
                out_filename = filename.rsplit('.', 1)[0] + '_result.mp4'
                res_path = os.path.join(app.config['RESULT_FOLDER'], out_filename)

                cap = cv2.VideoCapture(filepath)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(res_path, fourcc, fps, (width, height))

                detected_types = set()
                frame_count = 0

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

                    frame_count += 1
                    video_tasks[task_id]['progress'] = int(frame_count / total_frames * 100)

                cap.release()
                out.release()

                detected_items = [{'type': t, 'confidence': '动态捕获'} for t in detected_types]
                save_detection_record(selected_area, 'video', filename, out_filename, detected_items)

                video_tasks[task_id] = {
                    'status': 'done',
                    'progress': 100,
                    'file_type': 'video',
                    'result_file': out_filename,
                    'detected_items': detected_items,
                    'error': None
                }
            except Exception as e:
                video_tasks[task_id] = {'status': 'error', 'error': str(e)}

        threading.Thread(target=process_video, daemon=True).start()
        return jsonify({'success': True, 'task_id': task_id, 'file_type': 'video'})

    else:
        return jsonify({'error': '不支持的文件格式'}), 400


@app.route('/task_status/<task_id>')
@login_required
def task_status(task_id):
    task = video_tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task)


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
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()


@app.route('/live_camera', methods=['POST'])
@login_required
def live_camera():
    selected_area = request.form.get('area', 'playground')
    return render_template('index.html', live_mode=True, areas_str=selected_area, engine='local',
                           username=session.get('username'))


@app.route('/video_feed')
@login_required
def video_feed():
    area_str = request.args.get('areas', 'playground')
    allowed_classes = get_allowed_classes(area_str)
    return Response(gen_camera_frames(allowed_classes),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ================= 引擎2：前端 WebRTC 推流 =================
@app.route('/web_camera_ui', methods=['POST'])
@login_required
def web_camera_ui():
    selected_area = request.form.get('area', 'playground')
    return render_template('index.html', live_mode=True, areas_str=selected_area, engine='web',
                           username=session.get('username'))


@app.route('/detect_web_frame', methods=['POST'])
@login_required
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
        # 缩小帧以加速推理
        h, w = frame.shape[:2]
        if max(h, w) > 640:
            scale = 640 / max(h, w)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

        results = model.predict(source=frame, save=False, classes=allowed_classes, verbose=False)
        annotated_frame = results[0].plot(labels=True, conf=True)

        detected_items = []
        for box in results[0].boxes:
            cls_name_cn = CLASS_MAP_CN.get(model.names[int(box.cls[0])], model.names[int(box.cls[0])])
            detected_items.append({'type': cls_name_cn})

        unique_items = list({v['type']: v for v in detected_items}.values())

        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
        encoded_img = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'image': 'data:image/jpeg;base64,' + encoded_img,
            'items': unique_items
        })
    return jsonify({'error': '模型未加载'}), 500


# ================= 启动 =================
if __name__ == '__main__':
    ssl_cert, ssl_key = 'cert.pem', 'key.pem'
    use_ssl = os.path.exists(ssl_cert) and os.path.exists(ssl_key)

    # 没有证书时自动生成自签名证书
    if not use_ssl:
        try:
            import subprocess
            print("未找到 SSL 证书，正在自动生成自签名证书...")
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
                '-out', ssl_cert, '-keyout', ssl_key, '-days', '365',
                '-subj', '/CN=localhost'
            ], check=True, capture_output=True)
            use_ssl = True
            print("✅ SSL 证书生成成功，已启用 HTTPS")
        except Exception as e:
            print(f"⚠️ 无法生成 SSL 证书: {e}")
            print("摄像头功能需要 HTTPS 访问")

    if use_ssl:
        app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert, ssl_key))
    else:
        print("使用 HTTP 模式（摄像头推流功能不可用）")
        app.run(host='0.0.0.0', port=5000)
