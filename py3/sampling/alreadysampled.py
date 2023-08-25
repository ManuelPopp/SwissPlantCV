#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 21 20:39:08 2023

Update list of habitats and species that have already been sampled
"""
__author__ = "manuel"
__date__ = "Sun May 21 20:39:08 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, sys

dir_req = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "requests")

sys.path.append(dir_req)
os.chdir(dir_req)

import base, authentication, dirselect
from infoflora import Observations

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.realpath(__file__))
dir_main = os.path.dirname(dir_py)

USER = None
PROJECT = 93662

max_return = 1000
obs_after = "2023-04-15"

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    p = os.path.join(dir_main, "dat", args)
    return p

def out_dir(*args):
    p = os.path.join(dir_main, "out", args)
    return p

#-----------------------------------------------------------------------------|
# Run
my_obs = Observations()
my_obs.get_observations([PROJECT], [USER],
                        releves = [None], releve_names = [])
