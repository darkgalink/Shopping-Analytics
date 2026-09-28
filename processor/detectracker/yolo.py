"""
Run a YOLO_v3 style detection model on test images (OpenCV DNN backend).
"""

import os
import warnings

import cv2
import numpy as np
from PIL import Image

from processor.detectracker.yolo3.utils import letterbox_image
from paths import resource_path

warnings.filterwarnings('ignore')


class YOLO(object):

    _defaults = {
        "gpu_num": 1,
    }

    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"

    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)  # set up default values
        self.__dict__.update(kwargs)  # and update with user overrides
        self.cfg_path = resource_path('processor', 'detectracker', 'yolov3.cfg')
        self.weights_path = resource_path('processor', 'detectracker', 'model_data', 'yolov3.weights')
        self.classes_path = resource_path('processor', 'detectracker', 'model_data', 'coco_classes.txt')
        self.score = 0.5
        self.iou = 0.5
        self.class_names = self._get_class()
        self.model_image_size = (416, 416)  # fixed size or (None, None)
        self.is_fixed_size = self.model_image_size != (None, None)
        self._load_model()

    def _get_class(self):
        classes_path = os.path.expanduser(self.classes_path)
        with open(classes_path) as f:
            class_names = f.readlines()
        class_names = [c.strip() for c in class_names]
        return class_names

    def _load_model(self):
        cfg = os.path.expanduser(self.cfg_path)
        weights = os.path.expanduser(self.weights_path)
        if not os.path.isfile(weights):
            raise FileNotFoundError(
                "YOLO weights not found: %s" % weights)
        self.net = cv2.dnn.readNetFromDarknet(cfg, weights)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.output_names = self.net.getUnconnectedOutLayersNames()
        self.person_class_id = (self.class_names.index('person')
                                if 'person' in self.class_names else 0)

    def _load_outputs(self, outs, im_height, im_width):
        """Decode raw layer outputs into filtered boxes in image coordinates."""
        boxes, confidences = [], []
        for out in outs:
            for row in out:
                scores = row[5:]
                class_id = int(np.argmax(scores))
                if class_id != self.person_class_id:
                    continue
                confidence = float(row[4]) * float(scores[class_id])
                if confidence < self.score:
                    continue
                cx, cy = row[0] * im_width, row[1] * im_height
                w, h = row[2] * im_width, row[3] * im_height
                boxes.append([int(cx - w / 2), int(cy - h / 2),
                              int(w), int(h)])
                confidences.append(confidence)

        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.score, self.iou)
        return boxes, confidences, indices

    def detect_image(self, image):
        if self.is_fixed_size:
            assert self.model_image_size[0] % 32 == 0, 'Multiples of 32 required'
            assert self.model_image_size[1] % 32 == 0, 'Multiples of 32 required'
            boxed_image = letterbox_image(image, tuple(reversed(self.model_image_size)))
        else:
            new_image_size = (image.width - (image.width % 32),
                              image.height - (image.height % 32))
            boxed_image = letterbox_image(image, new_image_size)
        image_data = np.array(boxed_image, dtype='float32')

        # letterboxed RGB input, network expects RGB
        blob = cv2.dnn.blobFromImage(
            image_data, 1 / 255., image_data.shape[:2][::-1],
            swapRB=False, crop=False)
        self.net.setInput(blob)
        outs = [self.net.forward(name) for name in self.output_names]

        # Undo the letterbox padding/scaling to recover original coordinates.
        orig_w, orig_h = image.size
        model_w, model_h = image_data.shape[1], image_data.shape[0]
        scale = min(model_w / float(orig_w), model_h / float(orig_h))
        pad_x = int((model_w - int(orig_w * scale)) / 2)
        pad_y = int((model_h - int(orig_h * scale)) / 2)

        boxes, confidences, indices = self._load_outputs(
            outs, model_h, model_w)

        return_boxs = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                x = int((x - pad_x) / scale)
                y = int((y - pad_y) / scale)
                w = int(w / scale)
                h = int(h / scale)
                if x < 0:
                    w = w + x
                    x = 0
                if y < 0:
                    h = h + y
                    y = 0
                return_boxs.append([x, y, w, h])

        return return_boxs

    def close_session(self):
        pass
