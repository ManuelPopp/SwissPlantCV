#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 13:10:57 2023
"""
__author__ = "Manuel"
__date__ = "Wed Apr 26 13:10:57 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"
#-----------------------------------------------------------------------------|
# Imports
import os, argparse, datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk
from dateutil import parser

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(__file__)
dir_main = os.path.dirname(os.path.dirname(dir_py))
database_time_format = "%yyyy-%mm-%ddT%H:%M:%S %Z"

#-----------------------------------------------------------------------------|
# Functions
def data_dir(*args):
    p = os.path.join(dir_main, "dat", *args)
    return p

def species_list(df, releve_id):
    releve = df[df["releve_id"] == releve_id].to_dict(orient = "list")
    for key in releve:
        if len(set(releve[key])) == 1:
            releve[key] = releve[key].pop()
    return releve

#-----------------------------------------------------------------------------|
# Load data
habitats = pd.read_excel(data_dir("Habitats.xlsx"),
                         sheet_name = "Species")

observations = pd.read_csv(data_dir("Observed_habitats_Apr2023.csv"))

#-----------------------------------------------------------------------------|
# Get species list
class ReleveFinder(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.pack(padx = 0, pady = 0)
        self.winfo_toplevel().title("Relevé finder")
        self.winfo_toplevel().iconbitmap(
            os.path.join(dir_py, "ico/Dandelion.ico")
            )
        self.releve_id = tk.IntVar()
        
        self.master.minsize(250, 50)
        
        self.message = tk.Text(self, width = 40, height = 2)
        self.message.pack()
        self.message.insert("1.0", "Enter the Relevé ID of a sample and hit\n" +
                            "search to display site information.")
        self.display = tk.Entry(self)
        self.display.pack(side = tk.LEFT)
        
        self.find = tk.Button(self)
        self.find["text"] = "Search"
        self.find["command"] = self.get_species_list
        self.find.pack(side = tk.LEFT)
    
    def get_species_list(self):
        self.releve_id.set(int(self.display.get()))
        relev_dict = species_list(observations, self.releve_id.get())
        
        date = relev_dict["date"] if isinstance(relev_dict["date"], str) else \
            relev_dict["date"].pop()
        date_time = parser.parse(date)
        year, month = date_time.year, date_time.month
        
        habitat_id = map(int, str(relev_dict["habitat_id"]))
        
        subset = habitats
        for i, ID in enumerate(habitat_id):
            subset = subset[subset[subset.columns[i]] == ID]
        habitat = set(subset["Habitat_Sci"])
        H = habitat.pop() if len(habitat) > 1 else list(habitat)[0]
        
        output_str = "¦ Releve id: {0} ¦ Releve type: {1} ¦ Date: {2} ¦ " + \
            "Elevation: {3} ¦\n\nHabitat type: {4}\n\nSpecies list:\n{5}"
        output = output_str.format(
                self.releve_id.get(), relev_dict["releve_type"],
                "/".join([str(year), str(month)]),
                str(relev_dict["altitude_min"]) + " m",
                H,
                "\n".join(set(relev_dict["Species"]))
                )
        
        popup = tk.Toplevel(self)
        popup.title("Result")
        popup.iconbitmap(
            os.path.join(dir_py, "ico/Dandelion.ico")
            )
        geometry = "380x{0}".format(
            (len(set(relev_dict["Species"])) + 5) * 15
            )
        popup.geometry(geometry)
        text_out = tk.Text(popup,
                           height = 1000,
                           width = 300,
                           font = ("Arial", 8))
        text_out.pack()
        text_out.insert("1.0", output)

root = tk.Tk()
app = ReleveFinder(root)
app.mainloop()