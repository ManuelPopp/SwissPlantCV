#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 08:46:09 2023
"""
__author__ = "Manuel"
__date__ = "Tue Jun  6 08:46:09 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os
import pandas as pd
import pickle as pk

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

IMGDIR = "N:/prj/COMECO/img"
MULTIIMG = ["florid", "floraincognita", "plantnet"]
MODELLIST = ["florid", "floraincognita", "inaturalist", "plantnet"]
OUT = os.path.join(dir_main, "out")

#-----------------------------------------------------------------------------|
# Functions
def out_file(name, *subdirs):
    '''
    Generate file location within the selected output directory.

    Parameters
    ----------
    name : str
        Filename.
    *subdirs : str or list of str, optional
        Additional subdirectories inbetween the main output directory and the
        file.

    Returns
    -------
    path : str
        File path.
    '''
    path = os.path.join(OUT, *subdirs, name)
    
    return path

def load_checkpoint(name):
    '''
    Load pickled checkpoint of the last Batchrequest instance that has been
    running.
    
    Parameters
    ----------
    from_error : str/bool
        Restart from last error. (Alternative: Restart from last finished
        observation.) Default: "assert"; i.e., use the most recent checkpoint
        irrespective of checkpoint type.
    
    Returns
    -------
    br_cpt : Batchrequest
        Instance of type Batchrequest.
    
    Note
    ----
    Consider that you probably want to exclude previously finished releves from
    the releve_name_list when running a batch request using a checkpoint.
    '''
    with open(out_file(name, "log"), "rb") as f:
        br_cpt = pk.load(f)
    
    return br_cpt

BR = load_checkpoint("cpt.save")
#res = BR.results

def to_df():
    df = pd.DataFrame(BR.results)
    
    colnames = ["first", "second", "third", "forth", "fifth"]
    taxa = pd.DataFrame(df["taxon_suggestions"].to_list(),
                        columns = colnames)
    
    main = df[["question_index", "question_type", "releve_index",
               "releve_name", "releve_id", "observation_index",
               "observation_id", "true_taxon_id", "plant_organ",
               "image_files", "cv_model"]]
    
    out = pd.concat([main, taxa], axis = 1)
    
    return out

#df = to_df()
meta = base.load_meta("N:/prj/COMECO/img/META.pickle")
x = [m for m in meta if m["obs_id"] == 14485134]
observation = x[0]
base.add_coords("N:/prj/COMECO/img/2966245/14485134/img_1_v.jpg", (observation["y"], observation["x"]), replace = True)

path = "N:/prj/COMECO/img/2966245/14485134/img_3_s.jpg"
import exif
with open(path, "rb") as f:
    
    img = exif.Image(f)

lat = None

if img.has_exif:
    if "gps_latitude" in img.list_all():
        lat = img.gps_latitude
        lon = img.gps_longitude

if lat is None or replace:
    lat = tuple(dec_to_dms(coordinates[0]))
    lon = tuple(dec_to_dms(coordinates[1]))
    
    try:
        img.gps_latitude = lat
        img.gps_longitude = lon
    
    except:
        ###---------------------------------------------------------------|
        ### This is a quick and dirty workaround for current shortcomings
        ### of the exif package
        from PIL import Image
        EXPLIMG = "D:/switchdrive/PlantApp/img/Species/EXAMPLE_ANDROID.jpg"
        example_image = Image.open(EXPLIMG)
        example_exif = example_image.getexif()
        example_image.close()
        
        print(path)
        
        with Image.open(path) as current_image:
            current_image.save(path, exif = example_exif)
        
        with open(path, "rb") as f:
            img = exif.Image(f)
        
        img.gps_latitude = lat
        img.gps_longitude = lon
        ###---------------------------------------------------------------|
    
    with open(path, "wb") as f:
        
        f.write(img.get_file())