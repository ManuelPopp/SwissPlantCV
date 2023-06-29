#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 10:21:51 2023

Create an overview of what was sampled already.
"""
__author__ = "Manuel"
__date__ = "Thu Jun 29 10:21:51 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, sys
import simplekml
import pandas as pd
from pandas.core.base import PandasObject

this_file = os.path.dirname(os.path.realpath(__file__))
dir_py = os.path.dirname(this_file)
dir_req = os.path.join(dir_py, "requests")
dir_main = os.path.dirname(dir_py)

sys.path.append(dir_req)
from infoflora import Observations

#-----------------------------------------------------------------------------|
# Functions
def releves_to_kml(df, outfile,
                   name_column = "releve_id",
                   desc_column = "habitat_id",
                   x_column = None,
                   y_column = None,
                   coords_column = "location"):
    '''
    Funtion to use as a custom pandas.DataFrame method. The column 'location'
    of the dataframe is used to generate a KML.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    outfile : str
        Path to the output KML file.
    name_column : str, optional
        Name of the column containing the 'name' attribute of the point
        features. The default is "releve_id".
    desc_column : str, optional
        Name of the column containing the description attribute of the point
        features. The default is "habitat_id".
    x_column : str, optional
        Name of the column containing x (longitude) coordinates.
        The default is None.
    y_column : str, optional
        Name of the column containing y (latitude) coordinates.
        The default is None.
    coords_column : str, optional
        Name of the column containing locations as tuples in (lat, lon) format.
        The default is "location".

    Returns
    -------
    None.
    '''
    #df = df[["lat", "lon"]] = pd.DataFrame(df["location"].tolist())
    kml = simplekml.Kml()
    
    if x_column is None or y_column is None:
        df.apply(lambda x: kml.newpoint(name = str(x[name_column]),
                                        description = str(x[desc_column]),
                                        coords = [x[coords_column][::-1]]
                                        ),
                 axis = 1
                 )
    
    else:
        df.apply(lambda x: kml.newpoint(name = str(x[name_column]),
                                        description = str(x[desc_column]),
                                        coords = [x[x_column], x[y_column]]
                                        ),
                 axis = 1
                 )
    
    kml.save(outfile)

## Add function as a custom method to pandas.DataFrame
PandasObject.to_kml = releves_to_kml

#-----------------------------------------------------------------------------|
# Run
print("Updating completed releve list...")
my_obs = Observations()
my_obs.get_observations([93662], [None])

releves = my_obs.get_releves()

OUTTBL = os.path.join(dir_main, "spl", "Completed_habitats.csv")
OUTKML = os.path.join(dir_main, "spl", "Completed_habitats.kml")

# Write output to table
releves.to_csv(OUTTBL, index = False)

# Write output to KML
releves.to_kml(OUTKML)