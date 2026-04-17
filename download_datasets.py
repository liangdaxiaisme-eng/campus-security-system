from roboflow import Roboflow
import os

rf = Roboflow(api_key="RdaVG5lgWq4cyacPW97e")

DATASETS = [
    ("roboflow-ngkro", "polygon-fire-hydrant", 1),
    ("joseph-nelson", "hard-hat-workers", 14),
    ("keerthana-a-e9czj", "vehicle-detection-1", 1),
    ("leonid-kngrd", "pedestrian-detector", 1),
    ("intelliwatch-xarxw", "fighting-jlc8z", 1),
    ("eric-nuertey-coleman", "fire-extinguisher-v00vy", 3),
]

os.chdir("/hy-tmp/Campus_Security_System")

for workspace, project, version in DATASETS:
    try:
        print(f"下载: {workspace}/{project} v{version}...")
        proj = rf.workspace(workspace).project(project)
        ver = proj.version(version)
        dataset = ver.download("yolov8")
        print(f"  ✅ 完成: {dataset.location}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

print("\n所有数据集下载完成！")
