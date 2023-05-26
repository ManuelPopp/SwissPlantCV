#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:41:43 2023
"""
__author__ = "Manuel"
__date__ = "Fri May 26 14:41:43 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os
this_file = os.path.dirname(os.path.realpath(__file__))

dir_py = os.path.dirname(this_file)

os.chdir(os.path.join(dir_py, "requests"))

import infoflora

#-----------------------------------------------------------------------------|
# Run update of infoflora observation table
dir_main = os.path.dirname(dir_py)

obs = infoflora.Observations()
obs.update_releve_table(file = os.path.join(
    dir_main, "spl", "Releve_table.xlsx"
    ))