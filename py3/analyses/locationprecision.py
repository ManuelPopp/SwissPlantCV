#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:54:07 2023
"""
__author__ = "Manuel"
__date__ = "Thu Aug 17 16:54:07 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
import pickle as pk
import numpy as np

with open("N:/prj/COMECO/img/META.pickle", "rb") as f:
    d = pk.load(f)

precision = []

for v in d.values():
    precision.append(v["xy_precision"])

precision = np.array(precision)
np.mean(precision)
np.std(precision, ddof = 1) / np.sqrt(np.size(precision))
