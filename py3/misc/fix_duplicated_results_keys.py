#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 17:56:01 2023
"""
__author__ = "Manuel"
__date__ = "Thu Oct 12 17:56:01 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Fix BR Batch_0000000005 (duplicate keys)
for k1 in BR.results.keys():
    for k2 in BR.results[k1].keys():
        lvl3keys = list(BR.results[k1][k2].keys())
        
        for k3 in lvl3keys:
            if "\\" in k3 and k3.replace("\\", "/") in lvl3keys:
                del BR.results[k1][k2][k3]
BR.save()
BR.load_checkpoint("Batch_0000000009")
BR.name
BR.results.keys()

l = [
     "2976550",
     "2976545",
     "2976549",
     "2976544",
     "2976686",
     "2976685",
     "2976684",
     "2976683"
     ]

p_single = "D:/switchdrive/PlantApp/out/FloraIncognita/Batch_0000000009/_results_single.json"
f_single = open(p_single, "rb")
results = json.load(f_single)
f_single.close()
res = {k : results[k] for k in results.keys() if k.split("/")[2].split("_")[0] in l}

res.keys()
with open(f_single, "wb") as f:
    json.dumps(res, f)