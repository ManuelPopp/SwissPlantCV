#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 16 14:07:36 2023
"""
__author__ = "Manuel"
__date__ = "Tue May 16 14:07:36 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"
#-----------------------------------------------------------------------------|
import numpy as np
import pandas as pd
import os, rasterio

file_dict = {
    "TAVE" : 'Data/Temp_annual_mean.tif',
    "TRNG" : 'Data/Temp_annual_range.tif',
    "PREC_Annual" : 'Data/Prec_annual_sum.tif',
    "PREC_Summer" : 'Data/Prec_summer_sum.tif',
    "SRAD" : 'Data/CHELSA_sradyy_25.tif',
    "VGH_MX" : "Data/vegH25_max.tif",
    "VGH_Q1" : "Data/vegH25_q25.tif",
    "EVI" : "Data/Annual_median_EVI_2018_2021.tif",
    "EVI_Season" : "Data/Seasonal_diff_EVI_2018_2021.tif",
    "ASP" : "Data/Aspect_25.tif",
    "TWI" : "Data/TWI_25.tif",
    "TRI" : "Data/TRI_25.tif",
    "SoilR" : "Data/SPEEDMIND_SoilR_25.tif",
    "SoilF" : "Data/SPEEDMIND_SoilF_25.tif",
    "LULC" : "Data/LU-CH_2018all.tif",
    "VMG" : "Data/vmg25.tif",
    }

var_names = [
    'TAVE', 'TRNG', 'PREC_Annual', 'PREC_Summer', 'SRAD', 
    'VGH_MX', 'VGH_Q1', 'EVI', 'EVI_Season',
    'SoilR', 'SoilF',
    'ASP','TRI','TWI'
    ]

layer_names = [
    'TAVE', 'TRNG', 'PREC_Annual', 'PREC_Summer', 'SRAD', 
    'VGH_MX', 'VGH_Q1', 'EVI', 'EVI_Season',
    'VMG1', "VMG2", 
    'SoilR', 'SoilF',
    'ASP','TRI','TWI',
    'LULC'
    ]

min_max_values = pd.read_table("H:/COMECO/min_max_env_Nov22.csv",
                               header = 0, sep = ";")

main_dir = "D:/version2"
out_dir = "H:/COMECO/Raster"

for var_name in var_names:
    rast = file_dict[var_name]
    raster = rasterio.open(os.path.join(main_dir, rast))
    kwargs = raster.meta
    
    values = raster.read().astype("float64")
    
    val_min, val_max = min_max_values[var_name].values
    
    normalised = ((values - val_min) / (val_max - val_min)) * 20000. - 10000.
    
    no_data = 65535.
    
    rounded = normalised.round()
    rounded = np.where(values == kwargs["nodata"], no_data, rounded)
    
    integer = rounded.astype("int16")
    
    
    kwargs["nodata"] = None
    kwargs.update(
        dtype=rasterio.int16,
        count=1,
        compress='lzw')
    
    with rasterio.open(
            os.path.join(out_dir, var_name + ".tif"), "w", **kwargs
            ) as dst:
        dst.write(integer)

# Create two variables from VMG
raster = rasterio.open(os.path.join(main_dir, file_dict["VMG"]))
values = raster.read().astype("float64")
kwargs = raster.meta

VMG1 = ((100 - values) / 50 - 1) * 10000
VMG2 = (values / 50 - 1) * 10000

VMG1 = np.where(values == kwargs["nodata"], 0, VMG1)
VMG2 = np.where(values == kwargs["nodata"], 0, VMG2)

for name, data in zip(["VMG1.tif", "VMG2.tif"], [VMG1, VMG2]):
    with rasterio.open(
            os.path.join(out_dir, name), "w", **kwargs
            ) as dst:
        dst.write(data)

file_list = [os.path.join(out_dir, lyr_name + ".tif") \
             for lyr_name in layer_names]

# Write LULC (not normalised)
raster = rasterio.open(os.path.join(main_dir, file_dict["LULC"]))
values = raster.read()
kwargs = raster.meta

with rasterio.open(
        os.path.join(out_dir, "LULC.tif"), "w", **kwargs
        ) as dst:
    dst.write(values.astype("int16"))

# Save as raster stack
with rasterio.open(file_list[0]) as src0:
    meta = src0.meta

meta.update(count = len(file_list))

with rasterio.open(os.path.join(out_dir, "ENV.tif"), "w", **meta) as dst:
    for id, layer in enumerate(file_list, start = 1):
        with rasterio.open(layer) as src1:
            dst.write_band(id, src1.read(1))