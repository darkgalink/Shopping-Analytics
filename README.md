# Footfall-Analysis-in-Retail-Stores

### Real-time footfall analysis in retail stores

- Footfall analysis in real-time (supporting multiple video streams e.g., IP cameras, webcam) with a desktop app.
- Calculate demographics such as dwell times/heat maps at a particular location e.g., near shelfs.
- Customize the layout e.g., shelf control.
- People detection (using YOLO) along with age/gender detection if applicable.
- Track the path of customers in the stores.
- Analysis data is also stored in the logs.

**Example test run showcasing multiple video streams with customer detection/tracking, dwell times/heat maps:**

<div align="center">
    <img src="data/images/running.jpg" alt="Running" width=""/>
</div>

**Example test run showcasing shelf control:**

<div align="center">
    <img src="data/images/overview.jpg" alt="Overview" width=""/>
</div>

> NOTE: This project is experimental and not maintained actively. If any bugs/problems are encountered, please open an issue.

---

## Table of Contents

* [Running the app](#running-the-app)
    - [Install the dependencies](#install-the-dependencies)
    - [Download the models](#download-the-models)
    - [Run the desktop app](#run-the-desktop-app)
* [Build a standalone desktop app (PyInstaller)](#build-a-standalone-desktop-app-pyinstaller)
* [Model files](#model-files)
* [Tech stack](#tech-stack)
* [References](#references)

---

## Running the app

### Install the dependencies

Requires **Python 3.11** (tested on Windows 10/11). Create a virtual environment and install the dependencies: ```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The runtime dependencies are small: PyQt5, OpenCV (`opencv-python<5`), NumPy, SciPy, Pillow and QDarkStyle.
**TensorFlow/Keras/scikit-learn are not used any more** — YOLO inference and the MARS re-ID encoder
run on OpenCV's DNN module, and the detection-to-track assignment uses SciPy's Hungarian solver.

> NOTE: `opencv-python` must stay below 5.x — OpenCV 5 removed `cv2.dnn.readNetFromDarknet`.

### Download the models

The big model files (~342 MB) are **not stored in git**; they are listed in `models.txt`
(sha256 + size + URL) and downloaded on demand: ```
python scripts/download_models.py          # download what is missing (verifies sha256)
python scripts/download_models.py --check  # only verify (exit 1 if something is missing)
python scripts/download_models.py --force  # re-download everything
```
Running the app from source (`python footfall.py`) does this automatically on first launch,
so a fresh clone only needs `pip install -r requirements.txt` + internet access.
The packaged exe does not download anything — the models are bundled at build time, so run
the download script once before `pyinstaller`.

### Run the desktop app

The desktop application is powered by PyQt, run it with: ```
.venv\Scripts\python footfall.py
```

Pick a video file (samples in `data/tests/`), a webcam or an IP camera URL in the device dialog, then press OK.
Logs (CSV) are written to `data/logs/` under the current working directory.

---

## Build a standalone desktop app (PyInstaller)

End users do not need Python — the app can be packaged into a self-contained folder with:
```
python -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name ShoppingAnalytics ^
  --add-data "ui;ui" ^
  --add-data "processor\detectracker\yolov3.cfg;processor\detectracker" ^
  --add-data "processor\detectracker\model_data\yolov3.weights;processor\detectracker\model_data" ^
  --add-data "processor\detectracker\model_data\mars-small128-opencv.pb;processor\detectracker\model_data" ^
  --add-data "processor\detectracker\model_data\coco_classes.txt;processor\detectracker\model_data" ^
  --add-data "processor\agender\opencv_face_detector.pbtxt;processor\agender" ^
  --add-data "processor\agender\opencv_face_detector_uint8.pb;processor\agender" ^
  --add-data "processor\agender\model;processor\agender\model" ^
  footfall.py
```
(On Linux/macOS use `:` instead of `;` in `--add-data`.)

Result: `dist\ShoppingAnalytics\ShoppingAnalytics.exe`. Distribute the whole `ShoppingAnalytics`
folder (the executable needs the `_internal\` resources next to it).

Resource paths are resolved through `paths.py`:
- `resource_path()` — read-only model/UI files, bundled into the exe.
- `output_path()` / `ensure_output_dirs()` — writable `data/logs/` under the current working directory.

---

## Model files

Small files (configs, class lists, the converted MARS encoder) are versioned in the repo;
the heavy ones are downloaded from `models.txt` by `scripts/download_models.py` and
verified with sha256:

| Component | File | Versioned | Origin |
|---|---|---|---|
| Person detector | `processor/detectracker/yolov3.cfg` + `model_data/yolov3.weights` (248 MB) | cfg yes / weights **downloaded** | [YOLOv3 (pjreddie.com)](https://pjreddie.com/media/files/yolov3.weights) |
| Detection classes | `processor/detectracker/model_data/coco_classes.txt` | yes | COCO 80 classes |
| Re-ID encoder (MARS) | `model_data/mars-small128-opencv.pb` (11 MB) | yes | converted from the Keras `mars-small128.pb` so it runs on `cv2.dnn`; the original [mars-small128.pb](https://raw.githubusercontent.com/saimj7/Shopping-Analytics/master/processor/detectracker/model_data/mars-small128.pb) (**downloaded**, reference only) comes from the upstream project |
| Face detector | `processor/agender/opencv_face_detector_uint8.pb` (2.7 MB) + `.pbtxt` | pbtxt yes / pb **downloaded** | [OpenCV Zoo face detector](https://github.com/opencv/opencv_zoo) mirrored in [smahesh29/Gender-and-Age-Detection](https://github.com/smahesh29/Gender-and-Age-Detection) |
| Age / gender classifier | `model/age_net.caffemodel` + `gender_net.caffemodel` (45 MB each) + `deploy_*2.prototxt` | prototxt yes / caffemodel **downloaded** | [GilLevi/AgeGenderDeepLearning](https://github.com/GilLevi/AgeGenderDeepLearning) mirrored in [smahesh29/Gender-and-Age-Detection](https://github.com/smahesh29/Gender-and-Age-Detection) |
| Sample videos | `data/tests/*.mp4` (41 MB) | yes | test footage of this project |

To add a new asset: append a line to `models.txt` (`sha256  size_bytes  destino  url`).

---

## Tech stack

- **UI:** PyQt5 + QDarkStyle (`footfall.py`, `windows/`, `ui/*.ui`)
- **Detection / tracking:** YOLOv3 via `cv2.dnn` + DeepSORT (`processor/detectracker/`)
- **Age & gender:** OpenCV DNN Caffe models (`processor/agender/`)
- **Assignment:** SciPy `linear_sum_assignment` (`processor/detectracker/deep_sort/linear_assignment.py`)
- **Analytics:** heatmap, dwell time, gender distribution (`analyser/`)

---

## References

- [YOLOv3](https://pjreddie.com/darknet/yolov3/)
- [DeepSORT (nwojke/deep_sort)](https://github.com/nwojke/deep_sort)
- [AgeGenderDeepLearning (GilLevi)](https://github.com/GilLevi/AgeGenderDeepLearning)

---

*saimj7/ 14-06-2020 - ✎ <a href="http://saimj7.github.io" target="_blank">Sai_Mj</a>.*
