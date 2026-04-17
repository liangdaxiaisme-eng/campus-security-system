import os
import cv2
import numpy as np
import shutil
import random

def augment_image(image):
    """随机应用数据增强效果"""
    h, w = image.shape[:2]
    aug_type = random.choice(['flip', 'darken', 'brighten', 'noise'])
    
    if aug_type == 'flip':
        # 水平翻转
        return cv2.flip(image, 1), 'flip'
    elif aug_type == 'darken':
        # 变暗
        gamma = random.uniform(0.5, 0.8)
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table), 'none'
    elif aug_type == 'brighten':
        # 变亮
        gamma = random.uniform(1.2, 1.5)
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table), 'none'
    else:
        # 添加高斯噪声
        row, col, ch = image.shape
        mean = 0
        var = 0.01
        sigma = var ** 0.5
        gauss = np.random.normal(mean, sigma, (row, col, ch))
        gauss = gauss.reshape(row, col, ch)
        noisy = image + (gauss * 255)
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        return noisy, 'none'

def adjust_bounding_boxes(label_path, new_label_path, aug_type):
    """根据增强类型调整边界框"""
    if not os.path.exists(label_path):
        return
        
    with open(label_path, 'r') as f:
        lines = f.readlines()
        
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            class_id = parts[0]
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
            
            # 如果是水平翻转，x坐标需要跟着翻转
            if aug_type == 'flip':
                x_center = 1.0 - x_center
                
            new_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
    with open(new_label_path, 'w') as f:
        f.writelines(new_lines)

def main():
    print("====== 校园数据集一键扩充工具 (目标: 1.2万张) ======")
    master_dir = 'campus_security_master'
    train_img_dir = os.path.join(master_dir, 'train', 'images')
    train_lbl_dir = os.path.join(master_dir, 'train', 'labels')
    
    if not os.path.exists(train_img_dir):
        print("未找到训练集目录，请确保已运行缝合脚本。")
        return

    images = [f for f in os.listdir(train_img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    current_count = len(images)
    target_count = 12000
    
    print(f"当前训练集原始图片数量: {current_count}")
    
    if current_count >= target_count:
        print("数量已达标，无需扩充。")
        return
        
    needed_count = target_count - current_count
    print(f"开始物理生成 {needed_count} 张增强样本...")
    
    generated = 0
    while generated < needed_count:
        for img_name in images:
            if generated >= needed_count:
                break
                
            base_name = os.path.splitext(img_name)[0]
            ext = os.path.splitext(img_name)[1]
            
            img_path = os.path.join(train_img_dir, img_name)
            lbl_path = os.path.join(train_lbl_dir, base_name + '.txt')
            
            # 读取图片
            img = cv2.imread(img_path)
            if img is None:
                continue
                
            # 应用随机增强
            aug_img, aug_type = augment_image(img)
            
            # 保存新图片
            new_img_name = f"{base_name}_aug_{generated}{ext}"
            new_lbl_name = f"{base_name}_aug_{generated}.txt"
            
            new_img_path = os.path.join(train_img_dir, new_img_name)
            new_lbl_path = os.path.join(train_lbl_dir, new_lbl_name)
            
            cv2.imwrite(new_img_path, aug_img)
            adjust_bounding_boxes(lbl_path, new_lbl_path, aug_type)
            
            generated += 1
            if generated % 1000 == 0:
                print(f"已生成 {generated} / {needed_count} 张...")

    print("\n====== 扩充完成！======")
    final_count = len([f for f in os.listdir(train_img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    print(f"当前训练集总规模已达到: {final_count} 张。")

if __name__ == '__main__':
    main()