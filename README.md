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

All model files are already present in the repository (or must be downloaded for a fresh checkout):

| Component | File | Origin |
|---|---|---|
| Person detector | `processor/detectracker/yolov3.cfg` + `processor/detectracker/model_data/yolov3.weights` | [YOLOv3 (pjreddie.com)](https://pjreddie.com/media/files/yolov3.weights) |
| Detection classes | `processor/detectracker/model_data/coco_classes.txt` | COCO 80 classes |
| Re-ID encoder (MARS) | `processor/detectracker/model_data/mars-small128-opencv.pb` | converted from the Keras `mars-small128.pb` (Deep Sort) so it runs on `cv2.dnn`; the original `mars-small128.pb` is kept for reference |
| Face detector | `processor/agender/opencv_face_detector_uint8.pb` + `.pbtxt` | OpenCV Zoo |
| Age / gender classifier | `processor/agender/model/age_net.caffemodel`, `gender_net.caffemodel` + `deploy_*2.prototxt` | [GilLevi/AgeGenderDeepLearning](https://github.com/GilLevi/AgeGenderDeepLearning) |

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
