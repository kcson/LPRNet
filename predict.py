#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from argparse import Namespace
import warnings

import unicodedata
import yaml
import torch
import cv2
from rich import print
from imutils import paths
from rich.progress import track
from sklearn.metrics import accuracy_score

from lprnet import LPRNet, numpy2tensor, decode

warnings.filterwarnings("ignore")

if __name__ == "__main__":
    with open("config/kor_config.yaml") as f:
        args = Namespace(**yaml.load(f, Loader=yaml.FullLoader))

    load_model_start = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lprnet = LPRNet(args).to(device).eval()
    # pretrained = torch.load(args.pretrained)
    lprnet.load_state_dict(torch.load(args.pretrained)["state_dict"])
    print(f"Successful to build network in {time.time() - load_model_start}sec")

    imgs = [el for el in paths.list_images(args.test_dir)]
    labels = [
        # os.path.basename(n).split(".")[0].split("-")[0].split("_")[0]
        unicodedata.normalize('NFC', os.path.basename(n).split(".")[0].split("-")[0])
        for n in track(imgs, description="Making labels... ")
    ]

    # Warm Up
    im = numpy2tensor(cv2.imread(imgs[0]), args.img_size).unsqueeze(0).to(device)
    lprnet(im)

    times = []
    preds = []
    acc = []
    for i, img in track(
            enumerate(imgs),
            description="Inferencing... ",
            total=len(imgs),
    ):
        im = numpy2tensor(cv2.imread(img), args.img_size).unsqueeze(0).to(device)

        t0 = time.time()
        logit = lprnet(im).detach().to("cpu")
        pred, _ = decode(logit, args.chars)
        t1 = time.time()
        print(labels[i], ' : ', pred[0])

        acc.append(pred[0] == labels[i])
        times.append((t1 - t0) * 1000)
        preds.append(pred)

    print("\n-----Accuracy-----")
    print(
        f"correct: {sum(acc)}/{len(acc)}, "
        + f"incorrect: {len(acc) - sum(acc)}/{len(acc)}"
    )
    print(f"accuracy: {sum(acc) / len(acc) * 100:.2f} %")
    print("\n-----inference time-----")
    print(f"mean: {sum(times) / len(times):.4f} ms")
    print(f"max: {max(times):.4f} ms")
    print(f"min: {min(times):.4f} ms")
