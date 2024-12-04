#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 11 20:59:29 2023

@author: brunp
"""
# =============================================================================
### Load necessary packages
# =============================================================================

# Import modules
import time
start = time.time()

import os
import sys
import torch
import urllib.request
import tempfile
import base64
from urllib.parse import urlparse
from dotenv import load_dotenv
from torchvision import transforms
import torch.nn.functional as F
from PIL import Image, ImageFile
import pandas as pd
import rasterio
from rasterio import warp
from rasterio.crs import CRS
from datetime import datetime
import math
import json
import imghdr
from torch.utils.mobile_optimizer import optimize_for_mobile

os.chdir("/media/filbe/Data-NTFS/version2")

# Custom modules
import models

# Set number of threads
torch.set_num_threads(1)

# =============================================================================
### Load image
# =============================================================================

# transform image to tensor
trans_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

rd = Image.open("/media/filbe/Data-NTFS/switchdrive/PlantApp/img/EXAMPLE_IMG.jpg")   

# Rescale image if bigger than necessary

rd = rd.resize(size=(384,384)) 

mgi = trans_test(rd)
img = mgi.view(1, mgi.size(0), mgi.size(1), mgi.size(2))

# =============================================================================
### Load model
# =============================================================================

# Set torch device to cpu
map_location = torch.device('cpu')

model = models.DieTH(3076)
model.load_state_dict(torch.load("/media/filbe/Data-NTFS/version2/state_dicts/Comeco_Deit1_sd.pth", map_location))
model.eval()

# =============================================================================
### Go!
# =============================================================================

backend = "fbgemm"
model.qconfig = torch.quantization.get_default_qconfig(backend)
torch.backends.quantized.engine = backend
quantized_model = torch.quantization.quantize_dynamic(model, qconfig_spec={torch.nn.Linear}, dtype=torch.qint8)
scripted_quantized_model = torch.jit.script(quantized_model)
scripted_quantized_model.save("/media/filbe/Data-NTFS/version2/Data/scripted_quantized/Comeco_Deit1_sq.pt")

optimized_scripted_quantized_model = optimize_for_mobile(scripted_quantized_model)
optimized_scripted_quantized_model.save("/media/filbe/Data-NTFS/version2/Data/scripted_quantized/Comeco_Deit1_osq.pt")

optimized_scripted_quantized_model._save_for_lite_interpreter("/media/filbe/Data-NTFS/version2/Data/Comeco_Deit3_l.ptl")
ptl = torch.jit.load("/media/filbe/Data-NTFS/version2/Data/Comeco_Deit3_l.ptl")

with torch.autograd.profiler.profile(use_cuda=False) as prof1:
    out = model(img)
with torch.autograd.profiler.profile(use_cuda=False) as prof3:
    out = scripted_quantized_model(img)
with torch.autograd.profiler.profile(use_cuda=False) as prof4:
    out = optimized_scripted_quantized_model(img)
with torch.autograd.profiler.profile(use_cuda=False) as prof5:
    out = ptl(img)

print("original model: {:.2f}ms".format(prof1.self_cpu_time_total/1000))
print("scripted & quantized model: {:.2f}ms".format(prof3.self_cpu_time_total/1000))
print("scripted & quantized & optimized model: {:.2f}ms".format(prof4.self_cpu_time_total/1000))
print("lite model: {:.2f}ms".format(prof5.self_cpu_time_total/1000))