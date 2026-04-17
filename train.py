from ultralytics import YOLO
import os

def main():
    print("====== 校园智能安全管理系统 - 极限性能训练 ======")
    print("开始加载 YOLO 基础模型...")
    model = YOLO('yolo11n.pt')

    print("开始训练...")
    results = model.train(
        data='campus_data.yaml',
        epochs=100,
        imgsz=640,
        batch=64,
        name='campus_security_model',
        device='0',
        workers=12,
        optimizer='auto',
        patience=50,
        cache='ram'
    )

    print("训练完成！最优模型权重保存在: runs/detect/campus_security_model/weights/best.pt")

if __name__ == '__main__':
    main()
