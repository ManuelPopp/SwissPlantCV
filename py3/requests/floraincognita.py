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
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, shutil
p = "N:/prj/COMECO/img/2962829/14269515/img_0_s.jpg"

#-----------------------------------------------------------------------------|
# Settings
STDOUT = "H:/"

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