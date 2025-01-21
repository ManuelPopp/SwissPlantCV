#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 16:42:00 2023

Predict taxon names using the Pl@ntNet API

Pl@ntNet currently uses Inceptionv3 
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 16:42:00 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Production"

# Sources
#https://my.plantnet.org/doc/openapi
#https://github.com/plantnet/my.plantnet/blob/master/examples/post/run.py
#https://my.plantnet.org/doc/newfloras
# Mathias Chouet, PlantNet, pers. comm. (emails, e.g. from 2023-11-22)

#-----------------------------------------------------------------------------|
# Imports
import os, json, time, warnings
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import authentication, requests

#-----------------------------------------------------------------------------|
# General settings/variables
try:
    API_KEY = authentication.from_arbitrary_dict("PlantNet")["API_KEY"]
except:
    API_KEY = input(
        "Please enter your PlantNet API key (leave empty if not required): "
        )

PROJECT = "k-middle-europe"# "k-middle-europe" or "all"
TYPE = "kt"# "kt" or "legacy"# As of Oct 1st, 2023, "kt" is the default.

POSTURL = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?" + \
    f"type={TYPE}&api-key={API_KEY}"

organs_dict = {
    "i" : "flower",
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
    Post image to PlantNet.
    
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
    
    req = requests.Request(
        "POST", url = POSTURL, files = img_files, data = data
        )
    
    prepared_req = req.prepare()
    
    for a in range(3):
        try:
            session = requests.Session()
            response = session.send(prepared_req)
            
            json_result = json.loads(response.text)
            
            if "results" in json_result.keys():
                break
            
            else:
                raise Warning("Request failed.")
        
        except:
            print("Request failed at attempt {0}.".format(a))
            
            if "statusCode" in json_result.keys():
                print("Status code: " + str(json_result["statusCode"]))
                print(json_result["message"])
            
            time.sleep(5)
    
    if not response.ok:
        Warning(response.text)
    
    else:
        try:
            remaining_ids = json_result["remainingIdentificationRequests"]
            print(
                "Remaining PlantNet IDs for today: {0}\n".format(remaining_ids)
                )
        
        except:
            Warning("Failed to get number of remaining PlantNet IDs.")
            print("Response:\n")
            print(json_result)
    
    return json_result

def species_ranking(response_json, n = 5):
    species = [
        r["species"]["scientificName"] for r in response_json["results"]
        ]
    
    return species[:n]