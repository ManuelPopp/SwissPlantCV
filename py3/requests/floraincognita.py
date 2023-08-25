#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 08:25:13 2023

Pack image batches to send to Flora Incognita for identification
"""
__author__ = "Manuel"
__date__ = "Mon Jun  5 08:25:13 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "2.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, re, shutil, json
o = "D:/switchdrive/PlantApp/out/FloraIncognita"

#-----------------------------------------------------------------------------|
# Settings
STDOUT = "H:/"
IMGDIR = "N:/prj/COMECO/img"# Only required for Batchrequest version < 2.0.1

#-----------------------------------------------------------------------------|
# Functions
def post_image(files, batch, out_path = STDOUT):
    '''
    Create a folder of images to send to the Flora Incognita team for species
    predictions.

    Parameters
    ----------
    files : str/list
        File path or list of paths.
    batch : str
        Name of the current batch (will be appended to the output directory).
    out_path : str, optional
        Output directory. The default is STANDARDOUT.

    Returns
    -------
    None.
    '''
    img_files = files if isinstance(files, list) else [files]
    
    out_dir = STDOUT if batch is None else os.path.join(STDOUT, batch)
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok = True)
    
    for f in img_files:
        image_dir, image_name = os.path.split(f)
        obs_dir, obs_name = os.path.split(image_dir)
        parent_dir, releve_name = os.path.split(obs_dir)
        
        f_name = "_".join([releve_name, obs_name, image_name])
        f_path = os.path.join(out_dir, f_name)
        
        if len(img_files) > 1:
            g_name = "_".join([releve_name, obs_name + "m", image_name])
            g_path = os.path.join(out_dir, g_name)
            
            if os.path.isfile(g_path):
                mssg = "File {0} already exists and will be replaced."
                Warning(mssg.format(g_path))
                
                os.replace(f_path, g_path)
                
            else:
                os.rename(f_path, g_path)
        
        else:
            shutil.copy2(f, f_path)
    
    return

def merge_dicts(d0, d1):
    out = d0.copy()
    out.update(d1)
    
    return out

def load_batch(batch):
    path = os.path.join(o, batch)
    
    p_single = os.path.join(path, "_results_single.json")
    p_multi = os.path.join(path, "_results_multiobs.json")
    
    f_single = open(p_single, "rb")
    single = json.load(f_single)
    f_single.close()
    
    f_multi = open(p_multi, "rb")
    multi = json.load(f_multi)
    f_multi.close()
    
    ## Remove single image predictions that were included in the multi obs run
    single_in_multi = [k for k in multi.keys() if k.endswith(".jpg")]
    [multi.pop(k) for k in single_in_multi]
        
    json_obj = merge_dicts(single, multi)
    
    return json_obj

def insert(batchrequest_obj):
    '''
    Insert results from a .json file to a previously generated instance of type
    Batchrequest (version 2.0.1 or higher).
    
    Parameters
    ----------
    batchrequest_obj : batchrequest.Batchrequest
        Batchrequest object missing InfoFlora results.
    
    Returns
    -------
    None.
    '''
    try:
        N = batchrequest_obj.store_n
    
    except:
        N = 5
        
        mssg = "Batchrequest object lacks attribute store_n. " + \
            "Defaulting to N = 5."
        
        Warning(mssg)
    
    batch = batchrequest_obj.name
    results = load_batch(batch)
    
    for k in results.keys():
        name = k.split("/")[-1]
        releve_id, obs_id = [s.strip("m") for s in name.split("_")][:2]
        image = "_".join(name.split("_")[2:]) if name.endswith(".jpg") else \
            "multi"
        
        result = results[k]
        
        current_result = {
            "taxon_suggestions" : result["labels"][:N],
            "full_json" : result
            }
        
        try:
            releve_name = batchrequest_obj._releve_dict_static_inv[releve_id]
        
        except:
            batchrequest_obj.set_image_dir(IMGDIR)
            batchrequest_obj._image_meta_static, batchrequest_obj \
                ._releve_dict_static = batchrequest_obj.read_meta()
            
            batchrequest_obj \
                ._releve_dict_static_inv = {key : value for value, key in \
                                            zip(batchrequest_obj \
                                                ._releve_dict_static.keys(),
                                                batchrequest_obj \
                                                    ._releve_dict_static \
                                                        .values())
                                                }
            
            releve_name = batchrequest_obj \
                ._releve_dict_static_inv[int(releve_id)]
        
        keys = batchrequest_obj.results[releve_name][int(obs_id)].keys()
        
        matching_keys = [k for k in keys if image in k]
        
        if len(matching_keys) != 1:
            mssg = "List of matching images has length {0} for image {1}."
            
            raise Exception(mssg.format(len(matching_keys), image))
        
        else:
            matching_key = matching_keys[0]
        
        try:
            batchrequest_obj.results[
                releve_name
                ][int(obs_id)][matching_key]["floraincognita"].update(
                    current_result
                    )
        except:
            mssg = "Failed to find appropriate slot in Batchrequest object" + \
                ". Attempting to create slot..."
            
            Warning(mssg)
            
            batchrequest_obj.results[
                releve_name
                ][int(obs_id)][matching_key]["floraincognita"] = {
                    "timestamp" : None,
                    "question_type" : "multi_image" if image == "multi" else \
                        "single_image",
                    "releve_name" : releve_name,
                    "releve_id" : releve_id,
                    "observation_id" : obs_id,
                    "true_taxon_id" : None,
                    "plant_organ" : "multi" if image == "multi" else \
                        image[-5:-4],
                    "image_files" : name,
                    "cv_model" : "floraincognita",
                    "taxon_suggestions" : result["labels"][:N],
                    "full_json" : result
                    }