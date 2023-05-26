#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 11:56:59 2023
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 11:56:59 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Sources
#Test version: https://comeco-api.bitpilots.ch/openapi/#/
#V1: https://florid.infoflora.ch/api/v1/openapi

#-----------------------------------------------------------------------------|
# Imports
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import base
import requests

#-----------------------------------------------------------------------------|
# General settings/variables
IMG_MAXSIZE = 369800

#-----------------------------------------------------------------------------|
# Functions
def post_image(image_files,
               coords = None,
               date = None,
               n_suggestions = 3):
    '''
    Post image to COMECO for identification.
    
    Parameters
    ----------
    file : str
        Path to an image file.
    coords : list of float, optional
        List of length 2 containing geographic coordinates of the observation.
        The default is None.
    date : str, optional
        Date of the observation. The default is None.
    n_suggestions : int, optional
        Number of species suggestions to return. The default is 3.

    Returns
    -------
    response : requests.response
        Response type opject.
    '''
    files = image_files if isinstance(image_files, list) else [image_files]
    
    file = files[0]
    
    if coords is None:
        coords = base.get_coords(file)
        lat, lon = coords["lat"], coords["lon"]
    else:
        [lat, lon] = coords
    
    lat = base.dms_to_dec(lat) if len(lat) == 3 else lat
    lon = base.dms_to_dec(lon) if len(lon) == 3 else lon
    
    date_time = base.get_creation_time(file) if date is None else date
    
    
    img = {
      "images": [base.image_to_b64(f, max_size = IMG_MAXSIZE) for f in files],
      "lat" : lat,
      "lon" : lon,
      "date" : str(date_time.date()),
      "num_taxon_ids" : n_suggestions,
      "req_taxon_ids" : [0]
    }
    
    POSTURL = "https://florid.infoflora.ch/api/v1/openapi/identify/images"
    
    response = requests.post(POSTURL, json = img)
    
    return response

def identify(file, n_suggestions = 3, location = None):
    response = post_image(file, coords = location)
    return response

def get_taxon_list():
    TAXONURL = "https://florid.infoflora.ch/api/v1/openapi/taxon_ids"
    TAXONIDS = requests.get(TAXONURL)
    return TAXONIDS
