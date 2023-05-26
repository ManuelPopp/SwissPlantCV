#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 7 13:52:52 2023

Create a vector layer with information relevant for finding sampling sites
of a specific habitat type.
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
import os
from qgis.core import QgsProject, QgsProcessing, QgsProcessingParameterNumber

import pandas as pd
import geopandas as gpd

#-----------------------------------------------------------------------------|
# Settings
project = QgsProject.instance()