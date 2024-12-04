#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 14:34:04 2023
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 14:34:04 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import sys, os
import tkinter as tk
from tkinter import filedialog as fd

#-----------------------------------------------------------------------------|
# Classes
class FolderDialog(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.pack(padx = 0, pady = 0)
        self.master.minsize(150, 50)
        self.winfo_toplevel().title("Download image appendices")
        
        self.output_folder = tk.StringVar()
        self.output_folder.set("")
        
        self.create_widgets()
    
    def create_widgets(self):
        ## Display
        self.display_current_out = tk.Entry(self)
        self.display_current_out.grid(row = 0, column = 0, columnspan = 7,
                                  sticky = "EW")
        
        self.display_current_out["textvariable"] = self.output_folder
        
        ## Select output directory
        self.select_out_button = tk.Button(self)
        self.select_out_button["text"] = "Select output directory"
        self.select_out_button["command"] = self.select_out_folder
        self.select_out_button.grid(row = 1, column = 0, columnspan = 3,
                                 sticky = "EW")
        
        ## Confirm input
        self.select_button = tk.Button(self)
        self.select_button["text"] = "OK"
        self.select_button["command"] = self.set_var
        self.select_button.grid(row = 1, column = 4, columnspan = 4,
                                  sticky = "E")
        
    def select_out_folder(self):
        current_selection = self.output_folder.get()
        set_dir_to = current_selection if current_selection != "" else "/"
        selection = fd.askdirectory(title = "Select destination directory",
                                       initialdir = set_dir_to)
        
        self.output_folder.set(selection)
    
    def set_var(self):
        global directory
        directory = self.output_folder.get()
        
        self.master.destroy()

#-----------------------------------------------------------------------------|
# Functions
def select_directory():
    global directory
    directory = None
    
    if not sys.stdin.isatty():
        root = tk.Tk()
        app = FolderDialog(root)
        app.mainloop()
    else:
        directory = input("Enter output directory: ")
    
    return directory
