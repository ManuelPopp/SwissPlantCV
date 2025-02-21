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
import os, io, base64, datetime, cv2, requests, exif, piexif
import pickle as pk
import numpy as np
import pandas as pd
from PIL import Image
from dateutil import parser
from fractions import Fraction
from warnings import warn

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    '''
    Generate directory path to subdirectories using list of intermediate
    folders.
    
    Parameters
    ----------
    *args : str, list
        Intermediate folder names/file name.
    
    Returns
    -------
    p : str
        Full path.
    '''
    p = os.path.join(dir_main, "dat", *args)
    
    return p

def dms_to_dec(dms):
    '''
    Convert degree-minute-second format to decimal degrees.
    
    Parameters
    ----------
    dms : list or array
        Input coordinate in degrees-minutes-seconds.
    
    Returns
    -------
    dec : float
        Value in decimal degrees.
    '''
    [d, m, s] = dms
    dec = d + m / 60 + s / 3600
    
    return dec

def dec_to_dms(dec):
    '''
    Convert decimal degrees to degrees-minutes-seconds
    
    Parameters
    ----------
    dec : float
        Input coordinate in decimal degrees.
    
    Returns
    -------
    tuple
        Coordinate in degrees-minutes-seconds.
    '''
    degree = abs(np.floor(dec))
    minutes = dec % 1.0 * 60
    seconds = round(minutes % 1.0 * 60, 5)
    minutes = np.floor(minutes)
    
    return (int(degree), int(minutes), seconds)

def read_exif(path):
    '''
    Read image Exif.
    
    Parameters
    ----------
    path : str
        Full path to image file.
    
    Returns
    -------
    EXIF : exif._image.Image
        Image metadata.
    '''
    with open(path, "rb") as f:
        EXIF = exif.Image(f)
    
    return EXIF

def get_coords(path):
    '''
    Read coordinates from image Exif.
    
    Parameters
    ----------
    path : str
        Full path to image file.
    
    Returns
    -------
    dict
        Dictionary containing latitude and longitude.
    '''
    with open(path, "rb") as f:
        
        img = exif.Image(f)
    
    if img.has_exif:
        lat = img.gps_latitude
        lon = img.gps_longitude
    
    else:
        lat = lon = None
        
        mssg = "Failed to read coordinates from Exif for {0}.".format(path)
        Warning(mssg)
    
    if isinstance(lat, tuple):
        lat = dms_to_dec(lat)
        lon = dms_to_dec(lon)
    
    return {"lat" : lat,
            "lon" : lon}

def add_coords(path, coordinates, replace = False):
    '''
    Add coordinates to the Exif data of a .jpg file.

    Parameters
    ----------
    path : str
        Full path to the image file.
    coordinates : list or tuple of float
        Latitude and longitude that shall be added to the image file.
    replace : bool
        Replace existing coordinates if the image alread contains values for
        the repective Exif tags.

    Returns
    -------
    None.
    '''
    try:
        exif_dict = piexif.load(path)
    
    except:
        o = io.BytesIO()
        thumb_im = Image.open(path)
        
        try:
            thumb_im.thumbnail((25, 25), Image.LANCZOS)
        
        except:
            thumb_im.thumbnail((25, 25), Image.ANTIALIAS)
        
        thumb_im.save(o, "jpeg")
        thumbnail = o.getvalue()
        
        exif_dict = {
            "0th" : {},
            "Exif" : {},
            "GPS" : {},
            "1st" : {},
            "thumbnail" : thumbnail
            }
    
    if exif_dict["GPS"] == {} or replace:
        exif_dict["GPS"] = {}
        exif_dict["GPS"][piexif.GPSIFD.GPSVersionID] = (2, 0, 0, 0)
        
        lat_deg, lat_min, lat_sec = dec_to_dms(coordinates[0])
        lon_deg, lon_min, lon_sec = dec_to_dms(coordinates[1])
        
        lat_deg, lat_min, lat_sec = [
            (
                Fraction(str(i)).numerator,
                Fraction(str(i)).denominator
                ) for i in [lat_deg, lat_min, lat_sec]
            ]
        
        lon_deg, lon_min, lon_sec = [
            (
                Fraction(str(i)).numerator,
                Fraction(str(i)).denominator
                ) for i in [lon_deg, lon_min, lon_sec]
            ]
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = "N" \
            if coordinates[0] >= 0 else "S"
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = (lat_deg, lat_min,
                                                       lat_sec)
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" \
            if coordinates[1] >= 0 else "W"
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = (lon_deg, lon_min,
                                                        lon_sec)
        
        try:
            exif_bytes = piexif.dump(exif_dict)
        
        except:
            o = io.BytesIO()
            thumb_im = Image.open(path)
            
            try:
                thumb_im.thumbnail((25, 25), Image.LANCZOS)
            
            except:
                thumb_im.thumbnail((25, 25), Image.ANTIALIAS)
            
            thumb_im.save(o, "jpeg")
            thumbnail = o.getvalue()
            
            exif_dict["thumbnail"] = thumbnail
            
            try:
                exif_bytes = piexif.dump(exif_dict)
            
            except:
                Warning("Failed to write entire exif.")
                
                try:
                    exif = {
                        piexif.ExifIFD.DateTimeOriginal : exif_dict["Exif"][
                            piexif.ExifIFD.DateTimeOriginal]
                        }
                
                except:
                    Warning("Original creation time not found.")
                    
                    exif = {}
                
                exif_dict["Exif"] = exif
                
                exif_bytes = piexif.dump(exif_dict)
        
        piexif.insert(exif_bytes, path)
    
    return

def get_creation_time(path):
    '''
    Read time of image creation from metadata.
    
    Parameters
    ----------
    path : str
        Full path to image file.
    
    Returns
    -------
    DATETIME : datetime
        Datetime object.
    '''
    try:
        EXIF = read_exif(path)
        DT = EXIF.datetime_original
        DATETIME = parser.parse(DT.values)
    
    except:
        DATETIME = datetime.datetime.fromtimestamp(os.path.getctime(path))
        
        mssg = "No creation date found in image Exif for {0}. Path " + \
            "creation time is used instead."
        
        Warning(mssg.format(path))
    
    return DATETIME

def add_creation_time(path, date_time, replace = False):
    '''
    Add or replace image creation timestamp.

    Parameters
    ----------
    path : str
        Full path to image file.
    date_time : str/datetime
        Datetime object or string that can be parsed to a datetime object.
    replace : bool, optional
        Whether or not to replace creation time if a reapective tag exists
        already. The default is False.

    Returns
    -------
    None.
    '''
    date_time = parser.parse(date_time)
    
    try:
        exif_dict = piexif.load(path)
    
    except:
        o = io.BytesIO()
        thumb_im = Image.open(path)
        
        try:
            thumb_im.thumbnail((25, 25), Image.LANCZOS)
        
        except:
            thumb_im.thumbnail((25, 25), Image.ANTIALIAS)
        
        thumb_im.save(o, "jpeg")
        thumbnail = o.getvalue()
        
        exif_dict = {"0th" : {},
                     "Exif" : {},
                     "GPS" : {},
                     "1st" : {},
                     "thumbnail" : thumbnail
                     }
    
    try:
        t_original = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal]
    
    except:
        t_original = None
    
    if t_original is None or replace:
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = u"{0}" \
            .format(date_time)
    
    try:
        exif_bytes = piexif.dump(exif_dict)
    
    except:
        o = io.BytesIO()
        thumb_im = Image.open(path)
        
        try:
            thumb_im.thumbnail((25, 25), Image.LANCZOS)
        
        except:
            thumb_im.thumbnail((25, 25), Image.ANTIALIAS)
        
        thumb_im.save(o, "jpeg")
        thumbnail = o.getvalue()
        
        exif_dict["thumbnail"] = thumbnail
        exif_bytes = piexif.dump(exif_dict)
    
    piexif.insert(exif_bytes, path)
    
    return

def load_image_pil(path):
    try:
        img = Image.open(path).convert("RGB")
        img = np.array(img, dtype = np.uint8)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    except Exception as e:
        warn(f"Error loading image {path}: {e}")
        return None

def image_file_to_b64(path):
    '''
    Convert image to base64 encoded string.
    
    Parameters
    ----------
    path : str
        Full path to image file.
    
    Returns
    -------
    code : str
        Encoded string.
    '''
    with open(path, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    
    code = encoded_string.decode("utf8")
    
    return code

def image_crop_to_b64(path, max_size):
    '''
    Convert image to base64 encoded string and crop it to a maximum size in
    case this size is exceeded.
    
    Parameters
    ----------
    path : 
        Full path to image file.
    
    max_size :
        Maximum image size in pixels.
    
    Returns
    -------
    str
        Encoded string.
    '''
    img = load_image_pil(path)
    h, w = img.shape[:2]
    
    if w * h > max_size:
        SCALE = (max_size / (w * h)) ** 0.5
        WIDTH, HEIGHT = int(w * SCALE), int(h * SCALE)
        
        img = cv2.resize(
            img, (WIDTH, HEIGHT), interpolation = cv2.INTER_CUBIC
            )
        
    rv, img = cv2.imencode(".jpg", img)
    
    if not rv:
        raise ValueError(f"Encoding failed for image: {path}")
    
    return base64.b64encode(img).decode("utf8")

def load_meta(meta_file):
    '''
    Load image data base metadata.
    
    Parameters
    ----------
    meta_file : str
        Path to image data base metadata file.
    
    Returns
    -------
    metadata : dict
        Imagemetadata.
    '''
    try:
        with open(meta_file, "rb") as f:
            metadata = pk.load(f)
    except:
        raise Warning("Unable to read from file {0}.".format(meta_file))
    
    return metadata

def remove_empty(root):
    '''
    Remove empty subdirectories.
    
    Parameters
    ----------
    root : str
        Main directory.
    
    Returns
    -------
    None.
    '''
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
        
        return taxon_name.to_string(index = False)
    
    def check_wfo(self, name):
        WFOURL = "https://list.worldfloraonline.org/matching_rest.php?"
        response = requests.get(WFOURL, params = {
            "input_string" : name.replace(" ", "+")
            })
        
        return response.json()