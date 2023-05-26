#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 11 16:28:14 2023
"""
__author__ = "Manuel"
__date__ = "Thu May 11 16:28:14 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, re, shutil, requests, json, argparse
import pickle as pk
import pandas as pd

os.chdir(os.path.dirname(os.path.realpath(__file__)))
import base, infoflora, localcomeco, comeco, plantnet, inaturalist

from infoflora import Observations

#-----------------------------------------------------------------------------|
# Settings
def parseArguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-releve", "--releve", \
                        help = "Releve name.", \
                            type = str)
    
    parser.add_argument("-out_dir", "--output_directory", \
                        help = "Output directory.", \
                            type = str, default = None)
    
    parser.add_argument("-img_dir", "--image_directory", \
                        help = "Directory to store the images.", \
                            type = str, default = "N:/prj/COMECO/img")
    
    parser.add_argument("-clear_directory", "--clear_directory", \
                        help = "Remove existing files and folders of the " + \
                            "output directory.", \
                            type = bool, default = False)
    
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()

dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)
dir_out = os.path.join(dir_main, "out") if args.output_directory is None else \
    args.output_directory

dir_img = os.path.join(dir_main, "img") if args.image_directory is None else \
    args.image_directory

RELEVENAME = args.releve
REMOVE = args.clear_directory

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    p = os.path.join(dir_main, "dat", *args)
    return p

def image_dir(*args):
    p = os.path.join(dir_img, *args)
    return p

def output_dir(*args):
    p = os.path.join(dir_out, *args)
    return p

#-----------------------------------------------------------------------------|
# Workflow
'''_________________________________________________________________________'''
# Fetch observations
my_obs = Observations()
my_obs.get_observations(projects = [93662], observers = None,
                        releve_names = RELEVENAME)

my_obs.download_images(directory = dir_img, remove = REMOVE)

# Load image information
ds_info = base.load_meta(image_dir("META.pickle"))

'''_________________________________________________________________________'''
# Send identification requests
## Ask Pl@nt Net
#plantnet.post_image(img_path, organs = "auto")