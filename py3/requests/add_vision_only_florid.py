#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 14:32:27 2024

[Description]
"""
__author__ = "Manuel"
__date__ = "Tue Jan  9 14:32:27 2024"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "2.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Production"

#-----------------------------------------------------------------------------|
# Imports
import os
import glob
import copy
import base
import pandas as pd
from batchrequest_v201 import Batchrequest

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)
dir_log = os.path.join(dir_main, "out", "log")

#-----------------------------------------------------------------------------|
# Load Batchrequests and extract image only responses
SD = base.SpeciesDecoder("comeco_local")

logfiles = glob.glob(os.path.join(dir_log, "Batch*"), recursive = False)

for LOADFILE in logfiles:
    BR = Batchrequest()
    BR.load_checkpoint(file = os.path.basename(LOADFILE))
    
    for k0 in BR.results.keys():
        print(k0)
        for k1 in BR.results[k0].keys():
            print(k1)
            for k2 in BR.results[k0][k1].keys():
                print(k2)
                current_dict = BR.results[k0][k1][k2]
                new_dict = copy.deepcopy(current_dict)

                new_dict["florvision"] = copy.deepcopy(current_dict["florid"])
                new_dict["florvision"]["cv_model"] = "florvision"

                print("BR:")
                print(LOADFILE)
                image_results = new_dict["florvision"]["full_json"]["top_n"][
                    "by_image"
                    ]["name"]
                
                new_dict["florvision"]["taxon_suggestions"] = image_results
                BR.results[k0][k1][k2].update(new_dict)
                print("New keys:")
                print(BR.results[k0][k1][k2].keys())
    
    df = BR.to_df()
    df["true_taxon_name"] = [SD.decode(tid) for tid in df["true_taxon_id"]]
    df = df.drop_duplicates(subset = ["releve_name", "observation_id",
                                        "true_taxon_id", "plant_organ",
                                        "image_files", "cv_model"],
                              keep = "last")
    
    with pd.ExcelWriter(BR.path_out("Responses.xlsx"), mode = "a",
                    if_sheet_exists = "replace") as writer:
        df.to_excel(writer, sheet_name = BR.name, index = False)