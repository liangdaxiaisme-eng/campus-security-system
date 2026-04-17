import os
import shutil
import yaml

def main():
    print("==========================================")
    print("启动多数据集一键清洗与缝合程序...")
    print("==========================================")

    # 1. 创建终极数据集大仓库目录
    MASTER_DIR = 'campus_security_master'
    splits = ['train', 'valid', 'test']
    for split in splits:
        os.makedirs(os.path.join(MASTER_DIR, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(MASTER_DIR, split, 'labels'), exist_ok=True)

    # 2. 建立“绝对法则”（字典映射：不管原来的类别叫什么，遇到这些关键词统一归类到你的专属新ID）
    CLASS_MAP_RULES = {
        0: ['person', 'pedestrian', 'people', 'worker'],      # 0: 外来人员
        1: ['head', 'no_helmet', 'none'],                     # 1: 未戴安全帽
        2: ['helmet', 'hard_hat', 'hardhat'],                 # 2: 戴安全帽(正常)
        3: ['fire-hydrant', 'fire_hydrant', 'hydrant'],       # 3: 消防栓
        4: ['car', 'truck', 'bus', 'vehicle', 'motorcycle'],  # 4: 外来车辆
        5: ['fight', 'fighting', 'violence'],                 # 5: 异常行为(打架)
        6: ['fire-extinguisher', 'extinguisher', 'fire_extinguisher'] # 6: 灭火器
    }

    # 生成倒排索引以便快速查找
    keyword_to_new_id = {}
    for new_id, keywords in CLASS_MAP_RULES.items():
        for kw in keywords:
            keyword_to_new_id[kw.lower()] = new_id

    # 找出当前目录下所有包含 data.yaml 的下载文件夹
    dataset_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, 'data.yaml'))]

    if not dataset_dirs:
        print("未找到任何包含 data.yaml 的数据集文件夹，请确保你在正确的目录下运行此脚本。")
        return

    for d_name in dataset_dirs:
        print(f"\n>>> 正在处理数据集: {d_name}...")
        yaml_path = os.path.join(d_name, 'data.yaml')
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data_info = yaml.safe_load(f)
        
        # 构建当前数据集的 局部ID -> 全局ID 的转换字典
        local_to_global = {}
        original_names = data_info.get('names', [])
        
        if isinstance(original_names, dict):
            items = original_names.items()
        else:
            items = enumerate(original_names)
            
        for local_id, class_name in items:
            c_name_lower = str(class_name).lower()
            mapped = False
            for kw, new_id in keyword_to_new_id.items():
                if kw in c_name_lower:
                    local_to_global[int(local_id)] = new_id
                    print(f"  [+] 映射成功: 原类别 '{class_name}' (旧ID:{local_id}) -> 新类别 ID:{new_id}")
                    mapped = True
                    break
            if not mapped:
                print(f"  [-] 忽略: 原类别 '{class_name}' (旧ID:{local_id}) 未匹配到全局规则。")
                
        # 3. 开始搬运并修改标签
        for split in splits:
            img_dir = os.path.join(d_name, split, 'images')
            lbl_dir = os.path.join(d_name, split, 'labels')
            
            if not os.path.exists(img_dir) or not os.path.exists(lbl_dir):
                continue
                
            for filename in os.listdir(lbl_dir):
                if not filename.endswith('.txt'):
                    continue
                    
                old_lbl_path = os.path.join(lbl_dir, filename)
                base_name = os.path.splitext(filename)[0]
                img_found = False
                old_img_path = ""
                
                # 兼容不同的图片后缀
                for ext in ['.jpg', '.png', '.jpeg', '.JPG']:
                    temp_path = os.path.join(img_dir, base_name + ext)
                    if os.path.exists(temp_path):
                        old_img_path = temp_path
                        img_found = True
                        break
                        
                if not img_found:
                    continue

                # 为防止不同数据集图片同名，加上文件夹前缀
                new_base_name = f"{d_name}_{base_name}"
                new_lbl_path = os.path.join(MASTER_DIR, split, 'labels', new_base_name + '.txt')
                new_img_path = os.path.join(MASTER_DIR, split, 'images', new_base_name + os.path.splitext(old_img_path)[1])
                
                # 重写标签里的序号
                valid_lines = []
                with open(old_lbl_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            local_id = int(parts[0])
                            if local_id in local_to_global:
                                global_id = local_to_global[local_id]
                                parts[0] = str(global_id)
                                valid_lines.append(" ".join(parts) + "\n")
                                
                # 只有当这张图包含我们需要的标签时，才搬运图片和写入新标签
                if valid_lines:
                    with open(new_lbl_path, 'w') as f:
                        f.writelines(valid_lines)
                    shutil.copy(old_img_path, new_img_path)

    print("\n==========================================")
    print("数据缝合全部完成！所有文件已完美汇总至 'campus_security_master' 文件夹。")
    print("==========================================")

if __name__ == '__main__':
    main()