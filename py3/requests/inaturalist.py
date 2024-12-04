#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 10 16:36:20 2023
"""
__author__ = "Manuel"
__date__ = "Wed May 10 16:36:20 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Source: https://pyinaturalist.readthedocs.io/en/stable/index.html

#-----------------------------------------------------------------------------|
# Imports
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import base, authentication
import os, requests
from datetime import datetime
from pyinaturalist import get_access_token, create_observation, \
    update_observation, get_observations

#-----------------------------------------------------------------------------|
# Settings
BASEURL = "https://www.inaturalist.org"

#-----------------------------------------------------------------------------|
# Classes
class Session():
    def __init__(self):
        self.token = None
        self.authenticate()
        self.created_during_session = []
    
    def authenticate(self):
        try:
            self.auth = authentication.from_arbitrary_dict(
                "iNaturalistOBSERVATIONS"
                )
        
        except:
            print("User credentials not found. Open input prompt.")
            self.auth = authentication.authenthicate()
        
        self.token = get_access_token(username = self.auth["usr"],
                                      password = self.auth["pw"],
                                      app_id = self.auth["app_id"],
                                      app_secret = self.auth["app_secret"]
                                      )
    
    def create_observation(self, image_paths, obs_time, lat, lon, acc,
                           tags = "SwissPlantsTest"):
        response = create_observation(
            taxon_id = None,
            observed_on_string = obs_time,
            description = "",
            tag_list = tags,
            latitude = lat,
            longitude = lon,
            positional_accuracy = acc,
            access_token = self.token,
            photos = image_paths
            )
        
        self.created_during_session.append(response[0]["id"])
        
        return response[0]["id"]
    
    def replace_photos(self, image_paths, obs_id):
        response = update_observation(
            obs_id,
            access_token = self.token,
            photos = image_paths,
            ignore_photos = False
            )
    
    def get_observation(self, obs_id):
        response = get_observations(
            id = obs_id,
            converters = "json"
            )

x = Session()
r = x.authenticate()
test_img_folder = "C:/Users/poppman/Desktop/Salamandra"
coords = base.get_coords('N:/prj/COMECO/img\\2966350\\14490793\\img_2_v.jpg')
coords = get_coords(os.path.join(test_img_folder, "img1.jpg"))

obs = get_observations(id = 157494731)
obs
