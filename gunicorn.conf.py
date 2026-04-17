"""Gunicorn 生产配置"""
import multiprocessing

# 绑定地址和端口
bind = "0.0.0.0:5000"

# Worker 数量：CPU核心数 * 2 + 1，但 YOLO 模型较重，用 2 个就够了
workers = 2

# Worker 类型：sync 适合 CPU 密集型推理任务
worker_class = "sync"

# 每个 worker 的线程数（YOLO 推理释放 GIL，多线程有用）
threads = 2

# 超时设置（视频处理可能较慢）
timeout = 300
graceful_timeout = 60
keepalive = 5

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程名
proc_name = "campus_guard_ai"

# 预加载应用（减少内存占用）
preload_app = True

# 最大请求大小（与 Flask MAX_CONTENT_LENGTH 对应）
limit_request_body = 104857600  # 100MB
