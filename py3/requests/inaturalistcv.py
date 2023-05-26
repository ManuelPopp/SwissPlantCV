#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 22 18:05:13 2023

Predict taxon names using the iNaturalist CV API.
"""
__author__ = "manuel"
__date__ = "Mon May 22 18:05:13 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Sources
#https://rapidapi.com/inaturalist-inaturalist-default/api/visionapi
# Images are resized to 300 × 300 px on the iNaturalist server

#-----------------------------------------------------------------------------|
# Imports
import os, requests

os.chdir(os.path.dirname(os.path.realpath(__file__)))
import authentication

#-----------------------------------------------------------------------------|
# Settings
POSTURL = "https://visionapi.p.rapidapi.com/v1/rapidapi/score_image"
APPSCRTNAME = "iNaturalistCV"

HEADER = authentication.from_arbitrary_dict(APPSCRTNAME)

# In order to return only taxa below phylum Tracheophyta (vascular plants)
# -> set TAXONFROM = 211194
TAXONFROM = None

#-----------------------------------------------------------------------------|
# Functions
def post_image(image_path, coordinates):
    files = {"image" : open(image_path, "rb")}
    
    payload = {
        "lat" : str(coordinates[0]),
        "lng" : str(coordinates[1])
        }
    
    if TAXONFROM is not None:
        payload["taxon_id"] = TAXONFROM
    
    headers = HEADER
    
    response = requests.post(
        POSTURL, data = payload, files = files, headers = headers
        )
    
    json_result = response.json()
    
    return json_result

def species_ranking(response_json, n = 5):
    species = [r["taxon"]["name"] for r in response_json["results"]]
    
    return species[:n]
