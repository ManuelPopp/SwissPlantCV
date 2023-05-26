#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  7 14:04:15 2023
"""
__author__ = "manuel"
__date__ = "Sun May  7 14:04:15 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, glob, argparse
import pandas as pd
import numpy as np
import geopandas as gpd

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)
p_shp_all = os.path.join(dir_main, "gis", "shp", "sdf", "Observations.shp")

habitat_type = input("Habitat type: ")
p_out_shp = os.path.join(dir_main, "gis", "shp", "hss", habitat_type + ".shp")
os.makedirs(os.path.dirname(p_out_shp), exist_ok = True)

def parseArguments():
    parser = argparse.ArgumentParser()
    ## web = Shapefiles generated from iNaturalist and InfoFlora observations
    ## habitats = csv of bserved habitats
    ## single = InfoFlora database of single species observations
    parser.add_argument("-databases", "--ds", \
                        help = "Databases to include. Options: 'web', " + \
                            "'habitats', or 'single'.",
                            nargs = "+", \
                            type = str, default = "all")
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()

ds = args.ds if isinstance(args.ds, list) else [args.ds]

if "all" in ds:
    ds = ["web", "habitats", "single"]

if os.path.isfile(p_out_shp):
    overwrite = input("Output file exists already. Overwrite? [y/n]: ")
    
    run = False if overwrite.lower() == "n" else True
else:
    run = True

#-----------------------------------------------------------------------------|
# Run
if run:
    os.makedirs(os.path.dirname(p_out_shp), exist_ok = True)
    
    habitat_type_l = list(habitat_type)
    
    
    #-------------------------------------------------------------------------|
    # Functions
    def data_dir(*args):
        p = os.path.join(dir_main, "dat", *args)
        return p
    
    #-------------------------------------------------------------------------|
    # Load data
    print("Loading data files...")
    habitats = pd.read_excel(data_dir("Habitats.xlsx"),
                             sheet_name = "Species")
    
    habitats.loc[pd.isna(habitats["Epithet"]), "Epithet"] = ""
    
    observations = gpd.read_file(p_shp_all)
    
    infoflora = pd.read_table(data_dir("Observed_habitats_Apr2023.csv"),
                              sep = ",")
    
    single_obs = pd.read_table(data_dir("Single_obs.csv"),
                              sep = ",")
    
    #-------------------------------------------------------------------------|
    # Subset per habitat
    ## Get habitat species lists
    print("Searching for relevant species...")
    columns = habitats.columns[np.array(range(len(habitat_type_l)))]
    
    remaining = habitats
    
    for ht, cn in zip(habitat_type_l, columns):
        remaining = remaining[remaining[cn] == float(ht)]
    
    remaining["Species"] = [g.strip() + " " + e.strip() for g, e in zip(
        remaining["Genus"], remaining["Epithet"])]
    
    char_spec = remaining["Species"][remaining["Charakterart"] == 1]
    asso_spec = remaining["Species"][remaining["Charakterart"] == 0]
    
    if "web" in ds:
        ## Subset iNaturalist and InfoFlora Vegetation Survey observations
        print("Subsetting iNaturalist and InfoFlora Vegetation Survey data...")
        obs_char = observations[observations["Species"].isin(char_spec)]
        obs_asso = observations[observations["Species"].isin(asso_spec)]
        
        obs_char["Charakterart"] = 1
        obs_asso["Charakterart"] = 0
        
        info = "Found {0} character species and {1} associated species."
        print(info.format(len(obs_char), len(obs_asso)))
    
    if "single" in ds:
        ## Subset additional InfoFlora single-species observations
        print("Subsetting additional single-observation data...")
        more_char = single_obs[single_obs["Species"].isin(char_spec)]
        more_asso = single_obs[single_obs["Species"].isin(asso_spec)]
        
        more_char = more_char[["x", "y", "Species"]]
        more_asso = more_asso[["x", "y", "Species"]]
        
        more_char = gpd.GeoDataFrame(
            more_char, geometry = gpd.points_from_xy(more_char.x, more_char.y),
            crs = "EPSG:21781"
            ).to_crs(epsg = 4326)[["Species", "geometry"]]
        
        more_asso = gpd.GeoDataFrame(
            more_asso, geometry = gpd.points_from_xy(more_asso.x, more_asso.y),
            crs = "EPSG:21781"
            ).to_crs(epsg = 4326)[["Species", "geometry"]]
        
        more_char["id"] = 0
        more_asso["id"] = 0
        more_char["source"] = "singlobs"
        more_asso["source"] = "singlobs"
        more_char["Charakterart"] = 1
        more_asso["Charakterart"] = 0
        
        info = "Found {0} character species and {1} associated species."
        print(info.format(len(more_char), len(more_asso)))
    
    #-------------------------------------------------------------------------|
    # Add observed habitats
    if "habitats" in ds:
        infoflora = infoflora[["x", "y", "habitat_id", "releve_type",
                               "releve_id"]][
                                   infoflora["releve_type"].isin(
                                       ["ABS", "BB", "BB+", "C",
                                        "E", "PR", "PR+", "S"]
                                       )
                                   ][
                                       infoflora["habitat_id"] == int(
                                           habitat_type
                                           )
                                       ]
        
        infoflora = infoflora.groupby("releve_id").agg({
                                                        "x" : "first",
                                                        "y" : "first",
                                                        "habitat_id" : "first",
                                                        "releve_id" : "first"
                                                        })
        
        infoflora_geo = gpd.GeoDataFrame(
            infoflora, geometry = gpd.points_from_xy(infoflora.x, infoflora.y),
            crs = "EPSG:21781"
            )
        
        infoflora_geo = infoflora_geo.to_crs(epsg = 4326)[["releve_id", \
                                                           "geometry"]]
        infoflora_geo = infoflora_geo.rename(columns = {
                                                        "releve_id" : "Species"
                                                        })
        infoflora_geo = infoflora_geo.astype({"Species" : "int"}) \
            .astype({"Species" : "string"})
        
        infoflora_geo["id"] = 0
        infoflora_geo["source"] = "csv"
        infoflora_geo["Charakterart"] = 2
        
        info = "Found {0} habitats of type {1}."
        print(info.format(len(infoflora_geo), habitat_type))
    
    #-------------------------------------------------------------------------|
    # Combine data
    if "web" in ds and "habitats" in ds and "single" in ds:
        obs_out = gpd.GeoDataFrame(pd.concat([obs_char, obs_asso, more_char,
                                              more_asso, infoflora_geo]))
    elif "web" in ds and "habitats" in ds:
        obs_out = gpd.GeoDataFrame(pd.concat([obs_char, obs_asso,
                                              infoflora_geo]))
    elif "web" in ds and "single" in ds:
        obs_out = gpd.GeoDataFrame(pd.concat([obs_char, obs_asso, more_char,
                                              more_asso]))
    elif "habitats" in ds and "single" in ds:
        obs_out = gpd.GeoDataFrame(pd.concat([more_char, more_asso,
                                              infoflora_geo]))
    elif "web" in ds:
        obs_out = gpd.GeoDataFrame(pd.concat([obs_char, obs_asso]))
    
    elif "habitats" in ds:
        obs_out = infoflora_geo
    
    else:
        obs_out = gpd.GeoDataFrame(pd.concat([more_char, more_asso]))
    
    obs_out["id"] = np.array(range(len(obs_out)))
    
    obs_out.to_file(p_out_shp, driver = "ESRI Shapefile")
    print("Output was saved to {0}.".format(p_out_shp))
