#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 12:19:52 2023
"""
__author__ = "Manuel"
__date__ = "Sat May 6 07:19:52 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Sources
#https://docs.infoflora.ch/api/observation-v4

#-----------------------------------------------------------------------------|
# Imports
import os, re, requests, json, time
import pandas as pd
import pickle as pk
import pykew.ipni as ipni
import pykew.powo as powo

import pyproj as proj
import fiona as fi
import shapely as sh
from fiona.crs import from_epsg
from shapely.geometry import Point, mapping

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(__file__)
dir_main = os.path.dirname(os.path.dirname(dir_py))

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    p = os.path.join(dir_main, "dat", *args)
    return p

def out_shp(name):
    p = os.path.join(dir_main, "gis", "shp", "spp", name + ".shp")
    return p

def swiss_to_lonlat(point):
    trnsfrmr = proj.Transformer.from_crs(21781, 4326)
    x, y = trnsfrmr.transform(point[0], point[1])
    
    return [x, y]

#-----------------------------------------------------------------------------|
# Classes
class Taxon():
    def __init__(self,
                 species
                 ):
        self.orig_name = species
        
        result = ipni.search(species)
        orig_taxon = next(result)
        
        self.orig_taxon = orig_taxon
        self.id = orig_taxon["fqId"]
        taxon_info = powo.lookup(self.id)
        
        self.accepted_name = taxon_info["accepted"]["name"] if \
            taxon_info["synonym"] else taxon_info["name"]
    
    def get_observations(self):
        BASEURL = "https://api.inaturalist.org/v1/observations"
        
        defs = {"place_id" : 7236,
                "taxon_name" : self.accepted_name
                }
        
        response = requests.get(BASEURL, params = defs)
        self.r = response
        self.n_results = response.json()["total_results"]
        self.results = response.json()["results"]
        
        return response.status_code
    
    def export_locations(self):
        self.locs = list()
        
        for obs in self.results:
            if not obs["obscured"]:
                try:
                    location = obs["location"]
                    loc_split = location.split(",")
                    loc_float = [float(l) for l in loc_split]
                    self.locs.append(loc_float)
                except:
                    pass
        
        return self.locs

#-----------------------------------------------------------------------------|
# Load data
habitats = pd.read_excel(data_dir("Habitats.xlsx"),
                         sheet_name = "Species")

observations = pd.read_csv(data_dir("Observed_habitats_Apr2023.csv"))

#-----------------------------------------------------------------------------|
# Organise data
habitats["Species_name"] = [" ".join([str(g).strip(), str(e).strip()]) \
                            for g, e in zip(list(habitats["Genus"]),
                                list(habitats["Epithet"]))]

species_list = habitats["Species_name"].unique()

observations["Species_name"] = [" ".join(obs.split(" ")[:2]) \
                                for obs in observations["Species"]]

#-----------------------------------------------------------------------------|
# Extract observations for each species
schema = {"geometry" : "Point", 
          "properties" : {"id" : "int",
                      "source" : "str"
                    }
         }

for s in species_list:
    species = s.strip(" nan")
    
    outfile = out_shp(species.replace(" ", "_"))
    
    ## Get locations from iNaturalist
    try:
        inat_obs = Taxon(species)
        inat_obs.get_observations()
        inat_locs = inat_obs.export_locations()
    except:
        inat_locs = []
    
    ## Get locations from InfoFlora data
    infoflora_obs = observations[observations["Species_name"] == species]
    infoflora_locs = [[x, y] for x, y in zip(list(infoflora_obs["x"]),
                                             list(infoflora_obs["y"]))]
    
    ## Export species maps
    if len(inat_locs) > 0 or len(infoflora_locs) > 0:
        with fi.open(outfile, "w", "ESRI Shapefile",
                     schema = schema,
                     crs = from_epsg(4326)) as out:
            
            i = 0
            for i, loc in enumerate(inat_locs):
                [lon, lat] = loc
                point = Point(float(lat), float(lon))
                out.write({"geometry" : mapping(point),
                           "properties": {"id" : i,
                                          "source" : "iNaturalist"}
                           })
            
            for loc in infoflora_locs:
                i += 1
                [lat, lon] = swiss_to_lonlat(loc)
                point = Point(float(lon), float(lat))
                out.write({"geometry" : mapping(point),
                           "properties": {"id" : i,
                                          "source" : "InfoFlora"}
                           })
    
        sleep = 3 if i % 2 == 0 else 4
        time.sleep(sleep)