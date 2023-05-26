#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 15:20:30 2023
"""
__author__ = "Manuel"
__date__ = "Fri Apr 28 15:20:30 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, base64, exifread, datetime, cv2, requests
import pickle as pk
import pandas as pd
from dateutil import parser

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    p = os.path.join(dir_main, "dat", *args)
    return p

def read_exif(path):
    with open(path, "rb") as f:
        EXIF = exifread.process_file(f)
    
    return EXIF

def get_coords(path):
    EXIF = read_exif(path)
    
    try:
        LAT = [v.num / v.den for v in EXIF["GPS GPSLatitude"].values]
        LON = [v.num / v.den for v in EXIF["GPS GPSLongitude"].values]
    except:
        LAT, LON = None, None
        
        mssg = "Failed to read coordinates from EXIF for {0}.".format(path)
        
        raise Warning(mssg)
    
    return {"lat" : LAT,
            "lon" : LON}

def dms_to_dec(dms):
    [d, m, s] = dms
    dec = d + m / 60 + s / 3600
    return dec

def get_creation_time(path):
    try:
        EXIF = read_exif(path)
        DT = EXIF["EXIF DateTimeOriginal"]
        DATETIME = parser.parse(DT.values)
    except:
        DATETIME = datetime.datetime.fromtimestamp(os.path.getctime(path))
        
        mssg = "No creation date found in image EXIF for {0}. Path " + \
            "creation time is used instead."
        
        raise Warning(mssg.format(path))
    
    return DATETIME

def image_file_to_b64(path):
    with open(path, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    
    code = encoded_string.decode("utf8")
    return code

def image_to_b64(path, max_size):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    
    if w * h > max_size:
        SCALE = max_size / (w * h)
        WIDTH, HEIGHT = w * SCALE ** 0.5, h * SCALE ** 0.5
        WIDTH, HEIGHT = int(WIDTH), int(HEIGHT)
        
        img_resized = cv2.resize(img,
                                 (WIDTH, HEIGHT),
                                 interpolation = cv2.INTER_CUBIC
                                 )
        
        rv, img = cv2.imencode(".jpg", img_resized)
    
    encoded_string = base64.b64encode(img)
    
    code = encoded_string.decode("utf8")
    return code

def load_meta(meta_file):
    try:
        with open(meta_file, "rb") as f:
            metadata = pk.load(f)
    except:
        raise Warning("Unable to read from file {0}.".format(meta_file))
    
    return metadata

def remove_empty(root):
    subdirs = list(os.walk(root))[1:]
    for f in subdirs:
        if not f[2]:
            os.rmdir(f[0])

#-----------------------------------------------------------------------------|
# Classes
class SpeciesDecoder():
    def __init__(self, taxon_bb):
        self.backbone_dict = {
            "comeco_local" : {
                "file" : "Taxonomic_backbone_wHier_2022.csv",
                "id" : "ID",
                "name" : "Name"
                }
            }
        
        self.taxonomic_backbone = data_dir(
            self.backbone_dict[taxon_bb]["file"]
            )
        
        self._id_col = self.backbone_dict[taxon_bb]["id"]
        self._name_col = self.backbone_dict[taxon_bb]["name"]
        
        self.taxa_df = pd.read_table(self.taxonomic_backbone, sep = ",")
    
    def decode(self, taxon_id):
        taxon_name = self.taxa_df[ \
            self.taxa_df[self._id_col] == taxon_id \
            ][self._name_col]
        
        return taxon_name
    
    def check_wfo(self, name):
        WFOURL = "https://list.worldfloraonline.org/matching_rest.php?"
        response = requests.get(WFOURL, params = {
            "input_string" : name.replace(" ", "+")
            })
        
        return response.json()