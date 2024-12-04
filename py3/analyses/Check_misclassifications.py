#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 04 10:51:21 2023

Check misclassifications and other issues in a graphical user interface.

Script writing boosted by ChatGPT.
"""
__author__ = "Manuel"
__date__ = "Mon Sep 04 10:51:21 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Production"

#-----------------------------------------------------------------------------|
import os, subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import pandas as pd

IMGHEIGHT = 350
TKBUTTONWIDTH = 15
last_changed_entry = None

print("Starting up...")
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)
dir_spl = os.path.join(dir_main, "spl")
edit_br_py = os.path.join(dir_py, "requests", "batchrequest_v201.py")
edit_syn_py = os.path.join(dir_py, "analyses", "taxonomy.py")

# Batch request info
br_table = pd.read_excel(
    os.path.join(dir_spl, "Releve_table.xlsx"),
    sheet_name = "Batch_request"
    )

def get_br_name(name):
    idx = list(br_table["name"] == name).index(True)
    column_name = br_table.columns[br_table.iloc[idx] == True].values[0]
    prefix, number = str(column_name).split("_")
    br_name = "Batch_" + str(number).zfill(10)
    
    return br_name

def is_valid_file_path(file_path):
    return os.path.isfile(file_path)

def open_csv():
    file_path = os.path.join(dir_main, "out", "SingleImages.csv")
    if file_path:
        df_init = pd.read_csv(file_path, encoding = "ISO-8859-1")
        mask = df_init["image_files"].apply(is_valid_file_path)
        df = df_init[mask]
        
        display(df)

def edit_response(br, rel, obs, img, cvm, new, pysc = edit_br_py):
    exit_status = subprocess.call(
        f'py {pysc} --mupdate {br} {rel} {obs} {img} {cvm} new_response="{new}"'
        )

def edit_synonyms(taxon, synonym, pysc = edit_syn_py):
    exit_status = subprocess.call(
        f'py {pysc} --add_synonym "{taxon}" "{synonym}"'
        )

def display(df):
    row_index = 0
    total_images = len(df)
    
    def show_image():
        nonlocal row_index
        if 0 <=  row_index < total_images:
            # Image
            image_path = df["image_files"][row_index]
            image = Image.open(image_path)
            width, height = image.size
            IMGWIDTH = int(IMGHEIGHT * width // height)
            img = image.resize((IMGWIDTH, IMGHEIGHT))
            photo = ImageTk.PhotoImage(img)
            label.config(image = photo)
            label.image = photo
            image_label.config(
                text = f"Image {row_index + 1} of {total_images}"
                )
        
        else:
            label.config(image = "")
            image_label.config(text = "No Images to Display")
    
    def get_infos():
        nonlocal row_index
        cvmodel = df["cv_model"][row_index]
        true_id = df["true_taxon_name"][row_index]
        
        apires = [
            df["first"][row_index],
            df["second"][row_index],
            df["third"][row_index],
            df["forth"][row_index],
            df["fifth"][row_index]
        ]
        
        response = "\n".join(apires)
        
        image_path = df["image_files"][row_index]
        
        text_1.set(f"API\n{cvmodel}")
        text_2.set(f"True ID\n{true_id}")
        text_3.set(f"Prediction\n{response}")
        img_dir.set(image_path)
        
        # Update synonyms dropdown
        dropdown_selection.set("")
        synonyms_dropdown["menu"].delete(0, "end")
        for s in apires:
            synonyms_dropdown["menu"].add_command(
                label = s, command = tk._setit(dropdown_selection, s)
            )
    
    def prev_image():
        nonlocal row_index
        row_index = max(row_index - 1, 0)
        show_image()
        get_infos()
        
        nonlocal entry_page
        entry_page.set(row_index + 1)
        
        global last_changed_entry
        last_changed_entry = "Previous"
    
    def next_image():
        nonlocal row_index
        row_index = min(row_index + 1, total_images - 1)
        show_image()
        get_infos()
        
        nonlocal entry_page
        entry_page.set(row_index + 1)
        
        global last_changed_entry
        last_changed_entry = "Next"
    
    def left_key(event):
        try:
            if last_changed_entry.winfo_class() != "Entry":
                prev_image()
                '''
                cursor_index = last_changed_entry.index(tk.INSERT)
                if cursor_index > 0:
                    last_changed_entry.icursor(cursor_index - 1)
                '''
        except:
            prev_image()
    
    def right_key(event):
        try:
            if last_changed_entry.winfo_class() != "Entry":
                next_image()
                '''
                cursor_index = last_changed_entry.index(tk.INSERT)
                entry_text_length = len(last_changed_entry.get())
                if cursor_index < entry_text_length:
                    last_changed_entry.icursor(cursor_index + 1)
                '''
        except:
            next_image()
    
    def on_entry_change(entry):
        global last_changed_entry
        last_changed_entry = entry
    
    def goto():
        nonlocal entry_page
        nonlocal row_index
        page = entry_page.get()
        row_index = page - 1
        show_image()
        get_infos()
        
        global last_changed_entry
        last_changed_entry = "GoTo"
    
    def manual_edit_response():
        nonlocal row_index
        if new_val.get() == "":
            tk.messagebox.showwarning("Warning", "No values entered.")
        
        else:
            proceed = tk.messagebox.askokcancel(
                title = "Overwrite API response",
                message = "Do you want to overwrite the original API response?"
                )
            
            if proceed:
                rel = df["releve_name"][row_index]
                br = get_br_name(rel)
                img = df["image_files"][row_index]
                obs = df["observation_id"][row_index]
                cvm = df["cv_model"][row_index]
                new = new_val.get()
                edit_response(br, rel, obs, img, cvm, new, pysc = edit_br_py)
            
            else:
                print("Edit cancelled.")
        
        new_val.delete(0, tk.END)
        global last_changed_entry
        last_changed_entry = "Edit"
    
    def hit_return(event):
        if last_changed_entry == goto_val:
            goto()
        
        elif last_changed_entry == edit:
            manual_edit_response()
        
        elif last_changed_entry == "Previous":
            prev_image()
        
        elif last_changed_entry == "Next":
            next_image()
        
        else:
            print("Return button hit without reasonable action linked.")
    
    def add_synonym():
        nonlocal row_index
        taxon = df["true_taxon_name"][row_index]
        synonym = dropdown_selection.get()
        if synonym == "":
            tk.messagebox.showwarning("Warning", "No values entered.")
        
        else:
            mssg = f"Do you want to add {synonym} as a synonym for {taxon}?"
            proceed = tk.messagebox.askokcancel(
                title = "Add synonym",
                message = mssg
                )
            
            if proceed:
                edit_synonyms(taxon, synonym)
            else:
                print("Edit cancelled.")
        
        dropdown_selection.set("")
        global last_changed_entry
        last_changed_entry = "AddSynonym"
    
    root = tk.Tk()
    ttk.Style().theme_use("winnative")
    root.geometry("500x590")
    root.title("Data Control Center")
    
    try:
        root.iconbitmap("Icon.ico")
        
    except:
        print("Root window icon not found.")
    
    text_1 = tk.StringVar(root, "")
    text_2 = tk.StringVar(root, "")
    text_3 = tk.StringVar(root, "")
    img_dir = tk.StringVar(root, "")
    dropdown_selection = tk.StringVar(root, "")
    
    frame = ttk.Frame(root, width = 600, height = 800)
    frame.grid(row = 0, column = 0, sticky = (tk.W, tk.E, tk.N, tk.S))
    
    label = ttk.Label(frame)
    label.grid(row = 0, column = 0, columnspan = 4)
    
    image_label = ttk.Label(frame, text = "", font = ("Helvetica", 10))
    image_label.grid(row = 1, column = 0, columnspan = 4, pady = 10)
    
    # API response information
    text_left = ttk.Label(
        frame, textvariable = text_1, font = ("Helvetica", 10), width = 15
        )
    
    text_left.grid(row = 2, column = 0, sticky = tk.N)
    
    text_center = ttk.Label(
        frame, textvariable = text_2, font = ("Helvetica", 10), width = 25
        )
    
    text_center.grid(row = 2, column = 1, sticky = tk.N)
    
    text_right = ttk.Label(
        frame, textvariable = text_3, font = ("Helvetica", 10), width = 30
        )
    
    text_right.grid(row = 2, column = 2, columnspan = 2, sticky = tk.N)
    
    # Previous/next entry buttons and keys
    prev_button = ttk.Button(frame, text = "Previous", command = prev_image)
    prev_button.grid(row = 3, column = 0, sticky = tk.W)
    
    root.bind("<Left>", left_key)
    
    next_button = ttk.Button(frame, text = "Next", command = next_image)
    next_button.grid(row = 3, column = 3, columnspan = 1, sticky = tk.W)
    
    root.bind("<Right>", right_key)
    
    # Manual input
    entry_page = tk.IntVar()
    goto_val = tk.Entry(frame, textvariable = entry_page)
    goto_val.grid(row = 3, column = 1, sticky = tk.W+tk.E)
    goto_val.bind("<Key>", lambda event: on_entry_change(goto_val))
    
    goto_button = ttk.Button(frame, text = "Go to", command = goto)
    goto_button.grid(row = 3, column = 2, sticky = tk.W)
    
    root.bind("<Return>", hit_return)
    
    # Image path
    imagepath = tk.Entry(
        frame,
        textvariable = img_dir,
        fg = "black", bg = "white", bd = 0, state = "readonly"
        )
    
    imagepath.grid(row = 4, column = 0, columnspan = 3, sticky = tk.W+tk.E)
    
    # Edit BatchRequest object
    new_val = tk.Entry(frame)
    new_val.grid(row = 5, column = 0, columnspan = 2, sticky = tk.W+tk.E)
    new_val.bind("<Key>", lambda event: on_entry_change(new_val))
    
    edit = ttk.Button(
        frame,
        text = "Enter new value",
        command = manual_edit_response,
        width = TKBUTTONWIDTH
        )
    
    edit.grid(row = 5, column = 2, sticky = tk.W)
    
    # Add synonym dropdown
    synonyms_dropdown = tk.OptionMenu(frame, dropdown_selection, [])
    synonyms_dropdown.grid(
        row = 6, column = 0, columnspan = 2, sticky = tk.W+tk.E
        )
    
    # Edit BatchRequest object
    new_syn = ttk.Button(
        frame,
        text = "Add synonym",
        command = add_synonym,
        width = TKBUTTONWIDTH
        )
    
    new_syn.grid(row = 6, column = 2, sticky = tk.W)
    
    show_image()
    get_infos()
    
    label.grid_propagate(False)
    text_left.grid_propagate(False)
    text_center.grid_propagate(False)
    text_right.grid_propagate(False)
    
    root.mainloop()

if __name__ ==  "__main__":
    open_csv()
    print("App is running.")
