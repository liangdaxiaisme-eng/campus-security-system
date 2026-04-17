from ultralytics import YOLO

# 加载训练好的模型
model = YOLO('../campus_security_deploy/weights/best.pt')

# 运行验证
print("====== 开始验证模型 ======")
metrics = model.val()

# 打印结果
print("\n====== 验证结果 ======")
print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
print(f"Precision: {metrics.box.mp:.4f}")
print(f"Recall: {metrics.box.mr:.4f}")
