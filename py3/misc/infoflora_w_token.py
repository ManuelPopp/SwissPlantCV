#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 10 09:20:44 2023
"""
__author__ = "Manuel"
__date__ = "Wed May 10 09:20:44 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"
#-----------------------------------------------------------------------------|
# Imports
import os, re, shutil, requests, wget, json, argparse, base64, hashlib
import pickle as pk

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
                            type = int, default = 52219)
    parser.add_argument("-projects", "--project_id", \
                        help = "InfoFlora project ID.", \
                            nargs = "+", \
                            type = int, default = 93665)
    parser.add_argument("-releves", "--releve_id", \
                        help = "InfoFlora releve ID.", \
                            nargs = "+", \
                            type = int, default = None)
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
REMOVE = args.clear_directory

#-----------------------------------------------------------------------------|
# Classes
class observations():
    def __init__(self):
        self.auth = None
        
        try:
            self.auth_token()
        except:
            self.authenticate()
    
    def auth_token(self):
        self.app_key = authentication.from_token("InfoFloraOAuth")
    
    def authenticate(self):
        self.auth = authentication.authenthicate()
    
    def log_out(self):
        self.auth = None
    
    def get_observations(self, projects, observers, releves = None):
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

        Returns
        -------
        None.

        '''
        defs = {"limit" : 1000000}
        
        if projects is not None:
            defs["projects"] = projects
        
        if observers is not None:
            defs["observers"] = observers
        
        if releves is not None:
            defs["releves_ids"] = releves
        
        OBSURL = "https://obs.infoflora.ch/rest/v4/observations"
        AUTHURL = "https://auth.infoflora.ch/oauth2/authorize/fr"
        TOKENURL = "https://auth.infoflora.ch/oauth2/token"
        
        if self.auth is None:
            random_bytes = os.urandom(32)
            code_verifier = base64.b64encode(random_bytes)
            code_challenge = hashlib.sha256(code_verifier).digest()
            
            auth_req = requests.get(AUTHURL,
                                 params = {"client_id" : "a174ba5df51a6c9e9b3c7d4dabf4f267",#self.app_key[0],
                                           "code_challenge" : code_challenge,
                                           "code_challenge_method" : "S256",
                                           "response_type" : "code"}
                                 )
            
            token_req = requests.post(TOKENURL,
                          user = "CLIENT_ID:" + "2aa6a7c378ca7e3f19c4835e0463bc81cba6dcb47f603c0ea5a1a5db591139dafdd7367feca36e5fe6d6bd1e44b49beda8313a5a87eda9a2288a04936fcc2ca5",# self.app_key[1],
                          header = "Content-Type: application/x-www-form-urlencoded",
                          data = {
                              "grant_type" : "authorization_code",
                              "client_id" : "a174ba5df51a6c9e9b3c7d4dabf4f267",
                              "code" : AUTH_CODE,
                              "redirect_uri" : CLIENT_REDIRECT_URI,
                              "code_verifier" : CODE_VERIFIER
                              })
        else:
            response = requests.get(OBSURL,
                                    json = defs,
                                    auth = self.auth)
        
        if response.status_code == 200:
            content = response.json()
            self.observations = content["data"]
            self.n_observations = content["total_count"]
            
        elif response.status_code == 200:
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
            old_meta = []
        else:
            old_meta_file = os.path.join(out_dir, "META.pickle")
            
            if os.path.isfile(old_meta_file):
                old_meta = base.load_meta(old_meta_file)
        
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
                                       "file_locations",
                                       disc_locations)
        
        ## Remove observations that have been replaced from old metadata
        for old in old_meta:
            if old["obs_id"] in obs_ids:
                old_meta.remove(old)
        
        with open(os.path.join(out_dir, "META.pickle"), "wb") as f:
            pk.dump(self.observations + old_meta, f)
        
        with open(os.path.join(out_dir, "ERRORS.txt"), "w") as f:
            f.write(json.dumps(warnings))

#-----------------------------------------------------------------------------|
# Run
my_obs = observations()
my_obs.get_observations(PROJECT, USER, RELEVES)
my_obs.download_images(directory = OUT, remove = REMOVE)
