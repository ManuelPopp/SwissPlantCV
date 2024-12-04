# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:30:52 2024

@author: poppman
"""
import os, sys

os.chdir(
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)
                            )
            ), "requests"
        )
    )

sys.path.append(os.getcwd())
import authentication

API_KEY = authentication.from_arbitrary_dict("PlantNet")["API_KEY"]
print(API_KEY)