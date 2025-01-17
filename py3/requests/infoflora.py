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
import os, sys, re, shutil, wget, json, argparse, base64, time, logging
import pickle as pk
import pandas as pd
import urllib.request as ulrq
from alive_progress import alive_bar as pb

os.chdir(os.path.dirname(os.path.realpath(__file__)))
import base, authentication, dirselect

#-----------------------------------------------------------------------------|
# Settings
def parseArguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-out_dir", "--output_directory",
                        help = "Output directory.",
                            type = str, default = None)
    parser.add_argument("-observers", "--observer_id",
                        help = "InfoFlora observer ID.",
                            nargs = "+",
                            type = int, default = None)
    parser.add_argument("-projects", "--project_id",
                        help = "InfoFlora project ID.",
                            nargs = "+",
                            type = int, default = 93662)
    parser.add_argument("-releves", "--releve_id",
                        help = "InfoFlora releve ID.",
                            nargs = "+",
                            type = int, default = None)
    parser.add_argument("-releve_names", "--releve_names",
                        help = "Releve names.",
                            nargs = "+",
                            type = str, default = None)
    parser.add_argument("-releve_table", "--releve_table",
                        help = "Releve table (overwrites releve_names).",
                            type = str, default = None)
    parser.add_argument("-after", "--obs_after",
                        help = "Include only observations after a given date",
                        type = str, default = "2023-04-15")
    parser.add_argument("-clear_directory", "--clear_directory",
                        help = "Remove existing files and folders of the " + \
                            "output directory.",
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
obs_after = args.obs_after if __name__ == "__main__" else "2023-04-15"

## Log messages, warnings, and errors
logging.basicConfig(level = logging.INFO)

logger = logging.getLogger("stdout")

formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)s\n%(message)s"
    )

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

ch.setFormatter(formatter)
logger.addHandler(ch)

try:
    fh = logging.FileHandler(os.path.join(OUT, "log"))
    fh.setLevel(logging.WARNING)
    logger.addHandler(fh)

except:
    print("Running without storing log.")

#-----------------------------------------------------------------------------|
# Classes
class Observations():
    def __init__(self):
        self.auth = None
        self.token = None
        self.authenticate()
        self.META = {}
    
    def authenticate(self):
        try:
            self.token = authentication.get_token(
                provider_url = "https://auth.infoflora.ch/oauth2/token",
                saved = "InfoFloraOAuth"
                )
        
        except:
            logger.info("Attempting to read user credentials...")
            try:
                self.auth = authentication.from_credentials("InfoFloraLogin")
            
            except:
                logger.info("User credentials not found. Open input prompt.")
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
            
            #### Use pd.ExcelWriter to append an Excel sheet and prevent
            #### overwriting of other sheets in the workbook.
            with pd.ExcelWriter(file, mode = "a",
                                if_sheet_exists = "replace") as writer:
                releve_df.to_excel(writer, sheet_name = "Releves",
                                   index = False)
        
        ### If not, create a new Excel file
        else:
            releve_df.to_excel(file, sheet_name = "Releves", index = False)
        
        return 0
    
    def get_observations(self, projects, observers,
                         releves = None, releve_names = None, out = None):
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
        
        Note
        ----
        Currently, the number of releves is limited since the API response con-
        tains only a limited number of items per "page". A loop is not yet im-
        plemented at this point. (There are loops for the .update_releve_table
        method and the observations themselves, though. Thus, the issue only
        concerns the length of the provided releve list.)

        '''
        RELEVEENDPOINT = "https://obs.infoflora.ch/rest/v4/releves"
        
        OBSENDPOINT = "https://obs.infoflora.ch/rest/v4/observations"
        
        releve_url = RELEVEENDPOINT + "?after=" + obs_after + \
            "&limit={0}".format(max_return_releves)
        
        releve_url_updated = releve_url + "&offset={0}"
        
        request_url = OBSENDPOINT + "?limit={0}".format(max_return)
        
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
        
        logger.info("Creating releve dictionary...")
        
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
        
        if releve_names is None and releves is not None:
            releve_names = releve_dict.keys()
        
        if len(releve_dict) != 0 and releve_names is not None:
            releves = [releve_dict[r] for r in releve_names]
        
        if out is not None:
            with open(os.path.join(out, "RELEVE.dict"), "wb") as f:
                pk.dump(releve_dict, f)
        
        logger.info("Found releves:")
        logger.info(releves)
        
        ##--------------------------------------------------------------------|
        
        if not releves is None:
            request_url += "&releves_ids=" + ",".join(map(str, releves))
        
        logger.info("Using request url: " + request_url)
        
        self.observations = {}
        self.n_observations = 0
        request_url += "&offset={0}"
        offset = 0
        response_data = ["PLACEHOLDER"]
        
        while response_data != []:
            mssg = "Loading request page {0}. Offset = {1} observations."
            logger.info(mssg.format(int(offset / max_return), offset))
            
            if self.token is not None:
                response = ulrq.urlopen(
                    ulrq.Request(request_url.format(offset), headers = {
                        "accept" : "application/json",
                        "authorization" : self.token["token_type"] + " " + \
                            self.token["access_token"]
                        })
                    )
            else:
                request = ulrq.Request(request_url.format(offset))
                b64str = base64.b64encode(bytes("%s:%s" % self.auth, "ascii"))
                request.add_header(
                    "authorization", "Basic %s" % b64str.decode("utf-8")
                    )
                
                response = ulrq.urlopen(request)
            
            self.url = response.url
            logger.info("Response code: " + str(response.getcode()))
            
            if response.getcode() == 200:
                content = json.load(response)
                
                mssg = "Content total count: " + str(content["total_count"])
                logger.info(mssg)
                mssg = "Content filtered count: " + str(
                    content["filtered_count"]
                    )
                
                logger.info(mssg)
                
                response_data = content["data"]
                response_dict = {x["obs_id"] : x for x in response_data}
                
                self.observations.update(response_dict)
                self.n_observations += content["total_count"]
                
            elif response.getcode() == 401:
                response_data = []
                
                logger.error("Authentication failed.")
                
            else:
                response_data = []
                
                logger.warn(response.text)
            
            offset += max_return
            time.sleep(0.5)
    
    def get_releves(self, releve_types = [922, 923]):
        '''
        Output releve data.

        Raises
        ------
        Exception
            Missing data error.

        Returns
        -------
        releves : pandas.DataFrame
            Pandas DataFrame containing releve information.
        '''
        try:
            obs_zero = self.observations[list(self.observations.keys())[0]]
        
        except:
            mssg = "Instance of class 'Observation' currently stores no" + \
                " observations. Use .get_observations() to load observati" + \
                    "ons from Info Flora and retry."
            
            logger.error(mssg)
        
        releve_data = []
        
        if not isinstance(releve_types, list):
            releve_types = [releve_types]
        
        for observation in self.observations.values():
            if (observation["releve_type"] in releve_types) \
                or (releve_types == ["all"]):
                if pd.isna(observation["releve_id"]):
                    
                    mssg = "Releve ID missing from observation {0}."
                    logger.warn(mssg.format(observation["obs_id"]))
                
                releve_data.append(
                    {"releve_id" : int(observation["releve_id"]),
                     "releve_type" : int(observation["releve_type"]),
                     "date" : observation["date"],
                     "location" : (observation["y"], observation["x"]),
                     "habitat_id" : int(observation["habitat_id"]) if \
                         not pd.isna(observation["habitat_id"]) else None
                     }
                    )
        
        df = pd.DataFrame.from_records(releve_data)
        
        df = df.groupby(
                ["releve_id", "releve_type", "habitat_id"]
                ).aggregate(
                    {"date" : lambda x: x.iloc[0],
                     "location" : lambda x: x.iloc[0]
                     }
                    ).reset_index()
        
        df = df.astype({"releve_id" : "int",
                        "releve_type" : "int",
                        "habitat_id" : "int"})
        
        return df
    
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
    
    def _drop_observation(self, observation):
        observation_id = observation if isinstance(observation, int) else \
            observation["obs_id"]
        
        try:
            del self.observations[observation_id]
        
        except:
            mssg = "Could not find observation {0}"
            
            logger.info(mssg.format(observation))
    
    def download_images(self, directory = None, remove = False,
                        cleanup = True
                        ):
        
        out_dir = dirselect.select_directory() if directory is None \
            else directory
        
        if remove:
            shutil.rmtree(out_dir)
            self.META = {}
        else:
            old_meta_file = os.path.join(out_dir, "META.pickle")
            
            if os.path.isfile(old_meta_file):
                self.META = base.load_meta(old_meta_file)
        
        warnings = 0
        
        ## Create dict of current observations to clean up old metadata files
        ## later
        obs_ids = list()
        
        n_total = 0
        
        for obs in self.observations.values():
            n_total += len(self._get_image_urls(obs))
        
        with pb(n_total, bar = "smooth") as bar:
            for observation in self.observations.values():
                ## Create folder
                obs_id = observation["obs_id"]
                obs_ids.append(obs_id)
                
                releve_id = observation["releve_id"]
                
                current_dir = os.path.join(
                    out_dir, str(releve_id), str(obs_id)
                    )
                
                ## Remove previously existing version of the observation
                if os.path.isdir(current_dir):
                    shutil.rmtree(current_dir)
                
                ## Get image information
                rem = observation["rem"]
                remarks = rem.split(",") if rem is not None else []
                img_types = [re.sub("\w+:", "", r).strip() for r in remarks]
                
                for image_index, t in enumerate(img_types):
                    if not t in ["f", "i", "s", "t", "v"]:
                        mssg = "Invalid image type: {0}. " + \
                            "Must be in {{f, i, s, t, v}}."
                        
                        warnings += 1
                        logger.warn(mssg.format(t))
                
                ## Download images
                url_list = self._get_image_urls(observation)
                
                if len(url_list) != len(img_types):
                    warning_curr = "Length of URL list ({0}) " + \
                        "differs from length of image type notation ({1})." + \
                            " Noted image types: {2}."
                    
                    warnings += 1
                    logger.warn(
                        warning_curr.format(len(url_list),
                                            len(img_types),
                                            str(img_types))
                        )
                    
                    img_types = ["Unknown"] * len(url_list)
                
                if len(url_list) > 0 and not os.path.exists(current_dir):
                    os.makedirs(current_dir, exist_ok = True)
                
                else:
                    mssg = "No image URLs found: releve {0}, observation {1}."
                    
                    logger.warn(mssg.format(str(releve_id), str(obs_id)))
                
                disc_locations = list()
                
                for idx, (URL, suffix) in enumerate(zip(url_list, img_types)):
                    f_ext = os.path.splitext(URL)[-1]
                    fname = "img_{0}_{1}{2}".format(idx, suffix, f_ext)
                    
                    dest = os.path.join(current_dir, fname).replace("\\", "/")
                    
                    response = wget.download(URL, dest)
                    logger.info(response)
                    
                    disc_locations.append(dest)
                    
                    logger.info("Image disc location appended to META.")
                    
                    ## Add plot coordinates as image coordinates if image location
                    ## is missing
                    base.add_coords(dest, (observation["y"], observation["x"]),
                                    replace = True)
                    
                    ### Add creation date (for some files, this tag might have
                    ### been lost on the way)
                    base.add_creation_time(dest, observation["date"],
                                           replace = True)
                    
                    ### Increade progress bar
                    bar()
                
                self._set_observation_meta(observation,
                                           "img_types",
                                           img_types)
                
                self._set_observation_meta(observation,
                                           "file_locations",
                                           disc_locations)
                
                if cleanup and os.path.isdir(current_dir):
                    all_files = [os.path.join(current_dir, f) for f in \
                                 os.listdir(current_dir) if os.path.isfile(f)]
                    
                    for file_location in all_files:
                        if file_location not in disc_locations:
                            mssg = "Found deprecated file {0} which will " + \
                                "be removed."
                            
                            logger.info(mssg.format(file_location))
                            os.remove(file_location)
        
        ## Update observation metadata
        self.META.update(self.observations)
        
        with open(os.path.join(out_dir, "META.pickle"), "wb") as f:
            pk.dump(self.META, f)
        
        logger.info("Finished with {0} warnings.".format(warnings))

if __name__ == "__main__":
    #-------------------------------------------------------------------------|
    # Additional settings
    if RELEVETABLE == "standard":
        logger.info("Attempting to use standard releve table...")
        this_file = os.path.dirname(os.path.realpath(__file__))
        dir_py = os.path.dirname(this_file)
        dir_main = os.path.dirname(dir_py)
        
        RELEVETABLE = os.path.join(dir_main, "dat", "Releve_table.xlsx")
        
        if not os.path.isfile(RELEVETABLE):
            logger.warn("Unable to locate standard releve table.")
    
    if os.path.isfile(RELEVETABLE):
        releve_df = pd.read_excel(RELEVETABLE, sheet_name = "Releves")
        idx = releve_df[releve_df["include"] == True].index
        
        ## Overwrite RELEVENAMES list with selection from table
        RELEVENAMES = releve_df.loc[idx, "name"]
    
    #-------------------------------------------------------------------------|
    # Run
    my_obs = Observations()
    
    with pb(bar = "smooth", unknown = "brackets", spinner = "classic") as bar:
        my_obs.get_observations(PROJECT, USER,
                                releves = RELEVES, releve_names = RELEVENAMES,
                                out = OUT)
    
    logger.info("Starting downloads...")
    my_obs.download_images(directory = OUT, remove = REMOVE)