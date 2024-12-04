#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 13:24:24 2023
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 13:24:24 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, sys, getpass
import tkinter as tk
import pickle as pk
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from cryptography.fernet import Fernet as fn

u_auth = ("", "")

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)
dir_scrt = os.path.join(os.path.dirname(dir_main), "prv")

KEY_LOCATION = os.path.join(dir_scrt, "key", "FNK")

#-----------------------------------------------------------------------------|
# Classes
class Encrypter:
    def __init__(self):
        self.name = "Encrypter"
    
    def encrypt(self, dictionary, key = None):
        self.input = dictionary
        
        if key is None:
            with open(KEY_LOCATION, "rb") as f:
                self.key = pk.load(f)
        else:
            self.key = key
        
        self.FN = fn(self.key)
        
        self.enc_dict = dict()
        
        for k in self.input.keys():
            self.enc_dict[k] = self.FN.encrypt(
                self.input[k].encode("ascii")
                )
    
    def save_secret(self, path):
        with open(path, "wb") as f:
            pk.dump(self.enc_dict, f)
    
    def clear(self):
        self.input = self.FN = self.enc_dict = None

class Decrypter:
    def __init__(self):
        self.name = "Decrypter"
    
    def decrypt(self, path, key = None):
        self.file = path
        
        with open(self.file, "rb") as f:
            self.in_dict = pk.load(f)
        
        if key is None:
            with open(KEY_LOCATION, "rb") as f:
                self.key = pk.load(f)
        else:
            self.key = key
        
        self.FN = fn(self.key)
        
        self.info = dict()
        
        for k in self.in_dict.keys():
            self.info[k] = self.FN.decrypt(self.in_dict[k]).decode()
    
    def clear(self):
        self.in_dict = self.info = None

class Authenticator(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.pack(padx = 1, pady = 1)
        self.master.minsize(50, 50)
        self.master.title("User authentication")
        self.usr = tk.StringVar()
        self.pw = tk.StringVar()
        self.create_ui()
    
    def create_ui(self):
        self.usr_lbl = tk.Label(self, text = "User Name") \
            .grid(row = 0, column = 0)
        self.usr_in = tk.Entry(self, textvariable = self.usr) \
            .grid(row = 0, column = 1)
        self.pw_lbl = tk.Label(self, text = "Password") \
            .grid(row = 1, column = 0)
        self.pw_in = tk.Entry(self, textvariable = self.pw, show = "*") \
            .grid(row = 1, column = 1)
        self.button = tk.Button(self, text = "Login",
                           command = self.login).grid(row = 4, column = 0)
    
    def login(self):
        USR = self.usr.get()
        PW = self.pw.get()
        
        global u_auth
        u_auth = (USR, PW)
        
        self.master.destroy()
        
        return

#-----------------------------------------------------------------------------|
# Functions
def authenthicate(silent = False):
    '''
    Opens a user input session to enter log-in credentials. This is either a
    GUI (tkinter-based) or a simple prompt for user input, depending on whether
    the script is executed from a terminal/command prompt or other.

    Parameters
    ----------
    silent : bool, optional
        Set whether credentials should be returned by the function.
        The default is False.

    Returns
    -------
    out : tuple
        Tuple of the form (username, password).

    '''
    global u_auth
    
    if sys.stdin.isatty():
        USR = input("Enter InfoFlora user name: ")
        PW = getpass.getpass(prompt = "Enter password: ", stream = None)
        u_auth = (USR, PW)
    
    else:
        root = tk.Tk()
        app = Authenticator(root)
        app.mainloop()
    
    out = None if silent else u_auth
    return out

def from_credentials(name, silent = False):
    '''
    Decrypt saved user credentials.

    Parameters
    ----------
    name : str
        Name of the saved user credentials file.
    silent : bool, optional
        Set whether credentials should be returned by the function.
        The default is False.

    Returns
    -------
    out : tuple
        Tuple of the form (username, password).

    '''
    file = os.path.join(dir_scrt, "sec", name)
    
    if os.path.isfile(file):
        de = Decrypter()
        de.decrypt(path = file)
        credentials = de.info
        
        out = (credentials["usr"], credentials["pw"])
        de.clear()
    else:
        raise Exception("Unable to locate stored credentials.")
    
    if silent:
        global u_auth
        u_auth = out
    else:
        return out

def from_arbitrary_dict(name):
    '''
    Decrypt saved dictionary.

    Parameters
    ----------
    name : str
        Name of the saved user credentials file.
    silent : bool, optional
        Set whether credentials should be returned by the function.
        The default is False.

    Returns
    -------
    out : tuple
        Tuple of the form (username, password).

    '''
    file = os.path.join(dir_scrt, "sec", name)
    
    if os.path.isfile(file):
        de = Decrypter()
        de.decrypt(path = file)
        credentials = de.info
        
        de.clear()
    else:
        raise Exception("Unable to locate stored credentials.")
    
    return credentials

def get_token(provider_url,
              saved = None, client_id = None, client_secret = None):
    '''
    Fetch token using a client identifier and client secret.

    Parameters
    ----------
    provider_url : str
        Url to the authentication site.
    saved : str, optional
        Path to stored credentials. The default is None.
    client_id : str, optional
        Client identifier. (provide if saved is not set.) The default is None.
    client_secret : str, optional
        Client secret. (provide if saved is not set.). The default is None.

    Returns
    -------
    token : str
        Acces token.

    '''
    if saved is not None:
        file = os.path.join(dir_scrt, "sec", saved)
        
        if os.path.isfile(file):
            de = Decrypter()
            de.decrypt(path = file)
            credentials = de.info
            
            client_id, client_secret = credentials["identifier"], \
                credentials["secret"]
            
            de.clear()
        else:
            raise Exception("Unable to locate stored credentials.")
    
    ## Create BackendApplicationClient object
    client = BackendApplicationClient(client_id = client_id)
    
    ## Create OAuth2Session object
    oauth = OAuth2Session(client = client)
    
    ## Fetch token
    token = oauth.fetch_token(
        token_url = provider_url,
        auth = HTTPBasicAuth(client_id, client_secret)
        )
    
    return token

def re_encrypt():
    '''
    Re-encrypt all saved information with a newly generated key

    Returns
    -------
    None.
    
    '''
    new_key = fn.generate_key()
    
    ls = os.listdir(os.path.join(dir_scrt, "sec"))
    
    de = Decrypter()
    en = Encrypter()
    
    for f in ls:
        file = os.path.join(dir_scrt, "sec", f)
        
        if os.path.splitext(file)[1] == "":
            de.decrypt(file)
            
            en.encrypt(de.info, key = new_key)
            en.save_secret(file)
    
    with open(KEY_LOCATION, "wb") as f:
        pk.dump(new_key, f)