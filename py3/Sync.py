#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 14:36:04 2023
"""
__author__ = "Manuel"
__date__ = "Tue Apr 25 14:36:04 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"
#>----------------------------------------------------------------------------|
import os
from dirsync import sync
dir_home = "H:/PlantApp"
dir_shared = "L:/poppman/PlantApp"

sync_folders = [
    "dat", "fig", "out", "py3", "rsc", "tex"
    ]

for f in sync_folders:
    source_path = os.path.join(dir_home, f)
    target_path = os.path.join(dir_shared, f)
    os.makedirs(target_path, exist_ok = True)
    sync(source_path, target_path, "sync")