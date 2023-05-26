#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 12:19:52 2023
"""
__author__ = "manuel"
__date__ = "Sun May 7 09:54:19 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, glob
import pandas as pd
import geopandas as gpd

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(__file__)
dir_main = os.path.dirname(os.path.dirname(dir_py))
p_out_shp = os.path.join(dir_main, "gis", "shp", "sdf", "Observations.shp")
os.makedirs(os.path.dirname(p_out_shp), exist_ok = True)

#-----------------------------------------------------------------------------|
# Functions
def get_shp():
    p = os.path.join(dir_main, "gis", "shp", "spp", "*.shp")
    shpfls = glob.glob(p)
    return shpfls

#-----------------------------------------------------------------------------|
# Run

## Create output variable
out_shp = None

## Merge all shapefiles
for s in get_shp():
    species = os.path.split(s)[1].replace("_", " ").strip(".shp")
    shp = gpd.read_file(s)
    shp["Species"] = species
    
    if out_shp is None:
        out_shp = shp
    else:
        row_curr = max(out_shp["id"])
        shp["id"] += row_curr
        out_shp = gpd.GeoDataFrame(pd.concat([out_shp, shp]))

## Save output
out_shp.to_file(p_out_shp, driver = "ESRI Shapefile")