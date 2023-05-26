#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 12:19:52 2023

Download observations and photos from the Info Flora online fieldbook.
"""
__author__ = "Manuel"
__date__ = "Sun Apr 30 12:19:52 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Sources
#https://docs.infoflora.ch/api/observation-v4

#-----------------------------------------------------------------------------|
# Imports
import os, re, shutil, requests, wget, json, argparse, base64, hashlib
import pickle as pk
import pandas as pd
import urllib.request as ulrq

os.chdir(os.path.dirname(os.path.realpath(__file__)))
import base, authentication, dirselect

#-----------------------------------------------------------------------------|
# Settings
def parseArguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-out_dir", "--output_directory", \
                        help = "Output directory.", \
                            type = str, default = None)
    parser.add_argument("-observers", "--observer_id", \
                        help = "InfoFlora observer ID.", \
                            nargs = "+", \
                            type = int, default = None)
    parser.add_argument("-projects", "--project_id", \
                        help = "InfoFlora project ID.", \
                            nargs = "+", \
                            type = int, default = 93662)
    parser.add_argument("-releves", "--releve_id", \
                        help = "InfoFlora releve ID.", \
                            nargs = "+", \
                            type = int, default = None)
    parser.add_argument("-releve_names", "--releve_names", \
                        help = "Releve names.", \
                            nargs = "+", \
                            type = str, default = None)
    parser.add_argument("-releve_table", "--releve_table", \
                        help = "Releve table (overwrites releve_names).", \
                            type = str, default = None)
    parser.add_argument("-clear_directory", "--clear_directory", \
                        help = "Remove existing files and folders of the " + \
                            "output directory.", \
                            type = bool, default = False)
    
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()

    OUT = args.output_directory
    USER = args.observer_id if isinstance(args.observer_id, list) else \
        [args.observer_id]
    PROJECT = args.project_id if isinstance(args.project_id, list) else \
        [args.project_id]
    RELEVES = args.releve_id if isinstance(args.releve_id, list) else \
        [args.releve_id]
    RELEVENAMES = args.releve_names if isinstance(args.releve_names, list) \
        else [args.releve_names]
    RELEVETABLE = args.releve_table
    REMOVE = args.clear_directory

max_return = 1000
max_return_releves = 10
obs_after = "2023-04-15"

#-----------------------------------------------------------------------------|
# Classes
class Observations():
    def __init__(self):
        self.auth = None
        self.token = None
        self.authenticate()
        self.old_meta = []
    
    def authenticate(self):
        try:
            self.token = authentication.get_token(
                provider_url = "https://auth.infoflora.ch/oauth2/token",
                saved = "InfoFloraOAuth"
                )
        
        except:
            print("Attempting to read user credentials...")
            try:
                self.auth = authentication.from_credentials("InfoFloraLogin")
            
            except:
                print("User credentials not found. Open input prompt.")
                self.auth = authentication.authenthicate()
    
    def log_out(self):
        self.auth = None
    
    def update_releve_table(self, file,
                            projects = [93662], observers = [None]):
        '''
        Write an Excel file containing data on releves existing on Info Flora.

        Parameters
        ----------
        file : str
            Path to an existing or to create Excel file.
        projects : list of int, optional
            List of project IDs. The default is [93662].
        observers : list of int, optional
            List of observer IDs. The default is [None].

        Returns
        -------
        exit_status : int
            Status code.
        '''
        
        RELEVEENDPOINT = "https://obs.infoflora.ch/rest/v4/releves"
        
        releve_url = RELEVEENDPOINT + "?after=" + obs_after + \
            "&limit={0}".format(max_return_releves)
        
        releve_url_updated = releve_url + "&offset={0}"
        
        if not projects == [None]:
            releve_url += "&projects=" + ",".join(map(str, projects))
            releve_url_updated += "&projects=" + ",".join(map(str, projects))
        
        if not observers == [None]:
            releve_url += "&observers=" + ",".join(map(str, observers))
            releve_url_updated += "&observers=" + ",".join(map(str, observers))
        
        releve_url_updated += "&after=" + obs_after
        
        ## Settings for repeated requests (multiple requests might be required
        ## due to response item limit).
        status = 200
        releve_df = None
        offset = 0
        
        while status == 200:
            if self.token is not None:
                rresponse = ulrq.urlopen(
                    ulrq.Request(releve_url, headers = {
                        "accept" : "application/json",
                        "authorization" : self.token["token_type"] + " " + \
                            self.token["access_token"]
                        })
                    )
            else:
                request = ulrq.Request(releve_url)
                b64str = base64.b64encode(bytes("%s:%s" % self.auth, "ascii"))
                request.add_header(
                    "authorization", "Basic %s" % b64str.decode("utf-8")
                    )
                
                rresponse = ulrq.urlopen(request)
            
            status = rresponse.getcode()
            
            if status == 200:
                content = json.load(rresponse)
                
                releve_dat = content["data"]
                
                if releve_dat == []:
                    break
                
                releve_batch = pd.DataFrame(releve_dat)[
                    ["id", "name", "surface", "last_modified_when"]
                    ]
            
            if releve_df is None:
                releve_df = releve_batch.copy()
            
            else:
                releve_df = pd.concat([releve_df, releve_batch])
            
            offset += max_return_releves
            releve_url = releve_url_updated.format(offset)
            
        releve_df = releve_df.sort_values(by = "name")
            
        ### Set "include" column to False
        releve_df["include"] = False
        
        ### Check whether Excel file already exists. If so, use existing
        ### values for "include".
        if os.path.isfile(file):
            old_excel = pd.read_excel(file, sheet_name = "Releves")
            
            for i, row in old_excel.iterrows():
                releve_id = row["id"]
                include_releve = row["include"]
                
                if releve_id in releve_df["id"].values:
                    idx = releve_df["id"] == releve_id
                    releve_df.loc[idx, "include"] = include_releve
            
        releve_df.to_excel(file, sheet_name = "Releves", index = False)
        
        return 0
    
    def get_observations(self, projects, observers,
                         releves = None, releve_names = None):
        '''
        Get observations accessible to a user from InfoFlora.ch.

        Parameters
        ----------
        projects : int
            InfoFlora project IDs.
        observers : int
            InfoFlora observer IDs.
        releves : int, optional
            InfoFlora releve ID. The default is None.
        releve_names : str, optional
            Releve names. Overwrites "releves" with releve IDs obtained from
            InfoFlora for matching releves.

        Returns
        -------
        None.

        '''
        RELEVEENDPOINT = "https://obs.infoflora.ch/rest/v4/releves"
        
        OBSENDPOINT = "https://obs.infoflora.ch/rest/v4/observations"
        
        releve_url = RELEVEENDPOINT + "?after=" + obs_after + \
            "&limit={0}".format(max_return_releves)
        
        releve_url_updated = releve_url + "&offset={0}"
        
        request_url = OBSENDPOINT + "?limit={0}".format(max_return)
        request_url_updated = request_url + "&offset={0}"
        
        if not projects == [None]:
            releve_url += "&projects=" + ",".join(map(str, projects))
            request_url += "&projects=" + ",".join(map(str, projects))
        
        if not observers == [None]:
            releve_url += "&observers=" + ",".join(map(str, observers))
            request_url += "&observers=" + ",".join(map(str, observers))
        
        ## Translate releve names to releve IDs-------------------------------|
        status = 200
        releve_dict = dict()
        offset = 0
        
        while status == 200:
            if self.token is not None:
                rresponse = ulrq.urlopen(
                    ulrq.Request(releve_url, headers = {
                        "accept" : "application/json",
                        "authorization" : self.token["token_type"] + " " + \
                            self.token["access_token"]
                        })
                    )
            else:
                request = ulrq.Request(releve_url)
                b64str = base64.b64encode(bytes("%s:%s" % self.auth, "ascii"))
                request.add_header(
                    "authorization", "Basic %s" % b64str.decode("utf-8")
                    )
                
                rresponse = ulrq.urlopen(request)
            
            status = rresponse.getcode()
            
            if status == 200:
                content = json.load(rresponse)
                
                releve_dat = content["data"]
                
                if releve_dat == []:
                    break
                
                for releve in releve_dat:
                    if releve["name"] is not None:
                        releve_dict[releve["name"]] = releve["id"]
            
            offset += max_return_releves
            releve_url = releve_url_updated.format(offset)
        
        if releve_names is None:
            releve_names = releve_dict.keys()
        
        if len(releve_dict) != 0:
            releves = [releve_dict[r] for r in releve_names]
            
        with open(os.path.join(OUT, "RELEVE.dict"), "wb") as f:
            pk.dump(releve_dict, f)
        
        print("Found releves:")
        print(releves)
        
        ##--------------------------------------------------------------------|
        
        if not releves == [None]:
            request_url += "&releves_ids=" + ",".join(map(str, releves))
        
        print("Using request url: " + request_url)
        
        if self.token is not None:
            response = ulrq.urlopen(
                ulrq.Request(request_url, headers = {
                    "accept" : "application/json",
                    "authorization" : self.token["token_type"] + " " + \
                        self.token["access_token"]
                    })
                )
        else:
            request = ulrq.Request(request_url)
            b64str = base64.b64encode(bytes("%s:%s" % self.auth, "ascii"))
            request.add_header(
                "authorization", "Basic %s" % b64str.decode("utf-8")
                )
            
            response = ulrq.urlopen(request)
        
        self.url = response.url
        print("Response code: " + str(response.getcode()))
        
        if response.getcode() == 200:
            content = json.load(response)
            
            print("Content total count: " + str(content["total_count"]))
            print("Content filtered count: " + str(content["filtered_count"]))
            
            self.observations = content["data"]
            self.n_observations = content["total_count"]
            
        elif response.getcode() == 401:
            raise Warning("Authentication failed.")
            
        else:
            self.observations = None
            
            raise Warning(response.text)
    
    def _get_image_urls(self, observation):
        obs = self.observations[observation] if \
            isinstance(observation, int) else observation
        
        docs = obs["documents"]
        URLS = [d["file_url"] for d in docs]
        
        return URLS
    
    def _set_observation_meta(self, observation, key, value):
        obs = self.observations[observation] if \
            isinstance(observation, int) else observation
        
        obs[key] = value
    
    def _drop_observation(self, observation_id):
        for obs in self.observations:
            if obs["obs_id"] == id:
                self.observations.remove(obs)
    
    def download_images(self, directory = None, remove = False):
        
        out_dir = dirselect.select_directory() if directory is None \
            else directory
        
        if remove:
            shutil.rmtree(out_dir)
            self.old_meta = []
        else:
            old_meta_file = os.path.join(out_dir, "META.pickle")
            
            if os.path.isfile(old_meta_file):
                self.old_meta = base.load_meta(old_meta_file)
        
        warnings = dict()
        
        ## Create list of current observations to clean up old metadata files
        ## later
        obs_ids = list()
        
        for observation in self.observations:
            ## Create folder
            obs_id = observation["obs_id"]
            
            releve_id = observation["releve_id"]
            
            current_dir = os.path.join(out_dir, str(releve_id), str(obs_id))
            
            ## Remove previously existing version of the observation
            if os.path.isdir(current_dir):
                shutil.rmtree(current_dir)
            
            ## Get image information
            rem = observation["rem"]
            remarks = rem.split(",") if rem is not None else []
            img_types = [re.sub("\w+:", "", r).strip() for r in remarks]
            
            ## Download images
            url_list = self._get_image_urls(observation)
            
            if len(url_list) != len(img_types):
                warning_curr = "Length of URL list ({0}) " + \
                    "differs from length of image type notation ({1}). " + \
                        "Noted image types: {2}."
                
                warnings[str(obs_id)] = warning_curr.format(len(url_list),
                                                            len(img_types),
                                                            str(img_types))
                
                img_types = ["Unknown"] * len(url_list)
            
            if len(url_list) > 0:
                os.makedirs(current_dir, exist_ok = True)
            
            disc_locations = list()
            
            for idx, (URL, suffix) in enumerate(zip(url_list, img_types)):
                f_ext = os.path.splitext(URL)[-1]
                fname = "img_{0}_{1}{2}".format(idx, suffix, f_ext)
                
                dest = os.path.join(current_dir, fname)
                
                response = wget.download(URL, dest)
                print(response)
                
                disc_locations.append(dest)
            
            self._set_observation_meta(observation,
                                       "img_types",
                                       img_types)
            
            self._set_observation_meta(observation,
                                       "file_locations",
                                       disc_locations)
        
        ## Remove observations that have been replaced from old metadata
        for old in self.old_meta:
            if isinstance(old, dict):
                if old["obs_id"] in obs_ids:
                    self.old_meta.remove(old)
        
        with open(os.path.join(out_dir, "META.pickle"), "wb") as f:
            pk.dump(self.observations + self.old_meta, f)
        
        with open(os.path.join(out_dir, "ERRORS.txt"), "w") as f:
            f.write(json.dumps(warnings))

if __name__ == "__main__":
    #-------------------------------------------------------------------------|
    # Additional settings
    if RELEVETABLE == "standard":
        print("Attempting to use standard releve table...")
        this_file = os.path.dirname(os.path.realpath(__file__))
        dir_py = os.path.dirname(this_file)
        dir_main = os.path.dirname(dir_py)
        
        RELEVETABLE = os.path.join(dir_main, "spl", "Releve_table.xlsx")
        
        if not os.path.isfile(RELEVETABLE):
            raise Warning("Unable to locate standard releve table.")
    
    if os.path.isfile(RELEVETABLE):
        releve_df = pd.read_excel(RELEVETABLE, sheet_name = "Releves")
        idx = releve_df[releve_df["include"] == True].index
        
        ## Overwrite RELEVENAMES list with selection from table
        RELEVENAMES = releve_df.loc[idx, "name"]
    
    #-------------------------------------------------------------------------|
    # Run
    my_obs = Observations()
    my_obs.get_observations(PROJECT, USER,
                            releves = RELEVES, releve_names = RELEVENAMES)
    
    print("Starting downloads...")
    my_obs.download_images(directory = OUT, remove = REMOVE)