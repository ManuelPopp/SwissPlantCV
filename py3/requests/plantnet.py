#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 16:42:00 2023

Predict taxon names using the Pl@ntNet API
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 16:42:00 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Sources
#https://my.plantnet.org/doc/openapi
#https://github.com/plantnet/my.plantnet/blob/master/examples/post/run.py

#-----------------------------------------------------------------------------|
# Imports
import os, json
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import requests

#-----------------------------------------------------------------------------|
# General settings/variables
IMG_MAXSIZE = 1600
API_KEY = "2b10ZfcibrJnVEJkivyWiuAO"
PROJECT = "weurope"
api_endp = "https://my-api.plantnet.org/v2/identify/{0}?api-key={1}"
POSTURL = api_endp.format(PROJECT, API_KEY)

organs_dict = {"i" : "flower",
               "v" : "leaf",
               "f" : "fruit",
               "t" : "bark",
               "s" : "auto",
               "Unknown" : "auto"
               }

#-----------------------------------------------------------------------------|
# Functions
def convert_organ_id(organ):
    plantnet_organ_id = organs_dict[organ]
    
    return plantnet_organ_id
    
def post_image(files, organs = "auto"):
    '''
    Post image to Plant Net.
    
    Parameters
    ----------
    files : str, list
        Path to the image file(s).
    organs : optional; str, list
        Must contain at least one of leaf, flower, fruit, bark, auto.
        Optional: habit, other.

    Returns
    -------
    response : requests.response
        Response type opject.
    '''
    
    img_files = [("images", (f, open(f, "rb"))) for f in files] if \
        isinstance(files, list) else [("images", (files, open(files, "rb")))]
    
    plant_organs = organs if isinstance(organs, list) else [organs]
    
    if plant_organs[0] in organs_dict.keys():
        plant_organs = [convert_organ_id(o) for o in plant_organs]
    
    data = {
        "organs" : plant_organs
        }
    
    req = requests.Request("POST",
                           url = POSTURL,
                           files = img_files,
                           data = data)
    
    prepared_req = req.prepare()
    session = requests.Session()
    response = session.send(prepared_req)
    
    json_result = json.loads(response.text)
    
    return json_result

def species_ranking(response_json, n = 5):
    species = [
        r["species"]["scientificName"] for r in response_json["results"]
        ]
    
    return species[:n]