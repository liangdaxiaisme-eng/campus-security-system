from ultralytics import YOLO
import shutil
import os

# 目标目录
target_dir = '/home/asd/论文资料/开题报告/项目 1_覃兴鹏_校园安全管理/代码/yolov8_eca_mega_10k/'

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)

# 切换到训练目录
os.chdir('/home/asd/论文资料/开题报告/项目 1_覃兴鹏_校园安全管理/campus_security_deploy/runs/detect/campus_security_model/')

# 加载训练好的模型
print("====== 开始验证模型 ======")
model = YOLO('weights/best.pt')

# 运行验证
metrics = model.val()

# 打印结果
print("\n====== 验证结果 ======")
print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
print(f"Precision: {metrics.box.mp:.4f}")
print(f"Recall: {metrics.box.mr:.4f}")

# 复制所有训练结果文件到目标目录
source_dir = '.'
files_to_copy = [
    'weights/best.pt',
    'weights/last.pt',
    'results.csv',
    'results.png',
    'BoxF1_curve.png',
    'BoxP_curve.png',
    'BoxPR_curve.png',
    'BoxR_curve.png',
    'confusion_matrix.png',
    'confusion_matrix_normalized.png',
    'labels.jpg',
    'args.yaml'
]

print("\n====== 开始下载文件 ======")
for file in files_to_copy:
    src_path = os.path.join(source_dir, file)
    dst_path = os.path.join(target_dir, os.path.basename(file))
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"✓ 已复制：{file}")
    else:
        print(f"✗ 文件不存在：{file}")

# 复制验证批次图片
val_images = [f for f in os.listdir(source_dir) if f.startswith('val_batch')]
for img in val_images:
    src_path = os.path.join(source_dir, img)
    dst_path = os.path.join(target_dir, img)
    shutil.copy2(src_path, dst_path)
    print(f"✓ 已复制：{img}")

print(f"\n✅ 所有文件已下载到：{target_dir}")
print(f"📊 验证完成！mAP50: {metrics.box.map50:.4f}")
