"""Train the monster detector from the recorded dataset.

    python -m srbot.train [--epochs 60] [--imgsz 640]

Needs the optional training dependencies (`pip install ultralytics onnx`).
They are only used here: the finished model is exported to ONNX and runs
in the bot through onnxruntime alone, so the exe stays small.
"""

import argparse
import json
import os
import random
import shutil
import sys

from .paths import data_path
from . import yolo

BASE_WEIGHTS = "yolov8n.pt"  # downloaded automatically on first use (~6 MB)


def build_split(dataset_dir, val_fraction=0.15, seed=7):
    images_dir = os.path.join(dataset_dir, "images")
    images = sorted(os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.endswith(".jpg"))
    if len(images) < 2:
        raise SystemExit(f"Yeterli veri yok ({len(images)} kare). Önce 'Veri toplamayı başlat' ile kare topla.")
    random.Random(seed).shuffle(images)
    n_val = max(1, int(len(images) * val_fraction))
    val, train = images[:n_val], images[n_val:]
    train_txt, val_txt = (os.path.join(dataset_dir, n) for n in ("train.txt", "val.txt"))
    for path, items in ((train_txt, train), (val_txt, val)):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(items) + "\n")
    return train_txt, val_txt, len(train), len(val)


def write_yaml(dataset_dir, train_txt, val_txt, classes):
    path = os.path.join(dataset_dir, "data.yaml")
    names = "\n".join(f"  {i}: {json.dumps(n, ensure_ascii=False)}" for i, n in enumerate(classes))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"path: {dataset_dir.replace(os.sep, '/')}\n"
                f"train: {train_txt.replace(os.sep, '/')}\n"
                f"val: {val_txt.replace(os.sep, '/')}\n"
                f"names:\n{names}\n")
    return path


def train(dataset_dir, model_dir, epochs=60, imgsz=640, device=None):
    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("Eğitim için gerekli: pip install ultralytics onnx")

    with open(os.path.join(dataset_dir, "classes.txt"), encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]
    train_txt, val_txt, n_train, n_val = build_split(dataset_dir)
    data_yaml = write_yaml(dataset_dir, train_txt, val_txt, classes)
    print(f"Veri: {n_train} eğitim, {n_val} doğrulama karesi, sınıflar: {classes}", flush=True)

    runs = os.path.join(dataset_dir, "runs")
    # Cache the pretrained weights in the model dir instead of the working dir.
    cached = os.path.join(model_dir, BASE_WEIGHTS)
    model = YOLO(cached if os.path.isfile(cached) else BASE_WEIGHTS)
    model.train(data=data_yaml, epochs=epochs, imgsz=imgsz, batch=8, device=device or "cpu",
                workers=0, project=runs, name="train", exist_ok=True, plots=False,
                patience=20, verbose=False)

    os.makedirs(model_dir, exist_ok=True)
    if not os.path.isfile(cached) and os.path.isfile(BASE_WEIGHTS):
        shutil.move(BASE_WEIGHTS, cached)

    best = os.path.join(runs, "train", "weights", "best.pt")
    onnx_path = YOLO(best).export(format="onnx", imgsz=imgsz, opset=12, simplify=False, dynamic=False)

    os.makedirs(model_dir, exist_ok=True)
    shutil.copyfile(onnx_path, os.path.join(model_dir, "monsters.onnx"))
    with open(os.path.join(model_dir, "monsters.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "imgsz": imgsz}, f, ensure_ascii=False)
    print(f"Model hazır: {os.path.join(model_dir, 'monsters.onnx')}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dataset", default=data_path("dataset"))
    ap.add_argument("--out", default=yolo.MODEL_DIR)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--device", default=None, help="cpu, 0 (GPU), ...")
    args = ap.parse_args()
    train(args.dataset, args.out, args.epochs, args.imgsz, args.device)


if __name__ == "__main__":
    sys.exit(main())
