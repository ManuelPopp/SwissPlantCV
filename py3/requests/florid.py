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
#WSL API: https://speciesid.wsl.ch/florid

#-----------------------------------------------------------------------------|
# Imports
import os, time, threading, warnings
from datetime import datetime
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import base
import requests

#-----------------------------------------------------------------------------|
# General settings/variables
IMG_MAXSIZE = 369800

LOCAL = False
FLORIDSERVER = "H:/florid_v001"
SHOULDBERUNNING = True # Use external API, not local server.
THREADS = []

#-----------------------------------------------------------------------------|
# Functions
def _run_server(path = FLORIDSERVER):
    os.chdir(path)
    os.system("poetry run sanic main:app")

def start_local_server():
    '''
    Start local FlorID server.

    Parameters
    ----------
    path : str, optional
        Path to the local version of the FlorID Git repo.
        The default is "H:/florid".

    Returns
    -------
    None.
    '''
    global SHOULDBERUNNING, THREADS
    
    try:
        page = requests.get(
            "http://127.0.0.1:8000/docs/swagger#/default/post~identify%20images"
            )
        
        server_tatus = page.status_code
    
    except:
        SHOULDBERUNNING = False
        
        server_tatus = 0
        
    if server_tatus == 200:
        Warning("Server already running at 127.0.0.1:8000.")
        
        SHOULDBERUNNING = True
    
    else:
        THREADS.append(threading.Thread(target = _run_server))
        THREADS[0].start()

def post_image(image_files,
               coords = None,
               date = None,
               n_suggestions = 5,
               true_id = 1046220):
    '''
    Post image to FlorID for identification.
    
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
    global LOCAL, SHOULDBERUNNING
    
    files = image_files if isinstance(image_files, list) else [image_files]
    if len(files) > 5:
        warnings.warn("Only the first 5 images will be used by FlorID.")
        files = files[:5]
    
    file = files[0]
    
    if coords is None:
        coords = base.get_coords(file)
        lat, lon = coords["lat"], coords["lon"]
    
    else:
        [lat, lon] = coords
    
    lat = base.dms_to_dec(lat) if isinstance(lat, tuple) else lat
    lon = base.dms_to_dec(lon) if isinstance(lon, tuple) else lon
    
    if not isinstance(lat, float):
        print("Warning: No valid coordinates found.")
    
    date_time = base.get_creation_time(file) if date is None else date
    
    img = {
      "images": files if LOCAL else [
          base.image_crop_to_b64(f, max_size = IMG_MAXSIZE) for f in files
          ],
      "lat" : lat,
      "lon" : lon,
      "date" : str(date_time.date()) if isinstance(date_time, datetime) \
          else date_time,
      "num_taxon_ids" : n_suggestions,
      "req_taxon_ids" : [true_id]
    }
    
    #POSTURL = "http://127.0.0.1:8000/identify/images" if LOCAL else \
    #    "http://10.30.4.120:1337/identify/images"
    # Use new, publicly available API:
    POSTURL = "https://speciesid.wsl.ch/florid"
    
    if LOCAL:
        if not SHOULDBERUNNING:
            start_local_server()
            time.sleep(30)
    
    response = requests.post(POSTURL, json = img)
    
    return response.json()

def species_ranking(response_json, n = 5):
    species = response_json["top_n"]["by_combined"]["name"]
    
    if species[0] is None:
        species = response_json["top_n"]["by_image"]["name"]
    
    return species[:n]

def get_taxon_list():
    TAXONURL = "https://florid.infoflora.ch/api/v1/openapi/taxon_ids"
    TAXONIDS = requests.get(TAXONURL)
    
    return TAXONIDS