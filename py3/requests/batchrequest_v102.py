#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 24 16:35:35 2023

Send requests to the APIs of the various CV models tested in this study.
"""
__author__ = "Manuel"
__date__ = "Wed May 24 16:35:35 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.2"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, re, glob, time, random, argparse, platform
import pandas as pd
import pickle as pk
from datetime import datetime, timedelta
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import base, plantnet, inaturalistcv, florid, floraincognita
from floraincognita import insert as insert_florinc

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

IMGDIR = "N:/prj/COMECO/img"
MULTIIMG = ["florid", "floraincognita", "plantnet"]
MODELLIST = ["florid", "floraincognita", "inaturalist", "plantnet"]
OUT = os.path.join(dir_main, "out")

# Number of samples for multi-image predictions
NSAMPLES = 5

# Number of top suggestions to return (depending on the API, the limit may
# vary. Usually it is 10 suggestions.)
NTOP = 5

def parseArguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-out_dir", "--output_directory",
                        help = "Output directory.",
                            type = str, default = OUT)
    parser.add_argument("-releve_names", "--releve_names",
                        help = "Releve names.",
                            nargs = "+",
                            type = str, default = None)
    parser.add_argument("-releve_table", "--releve_table",
                        help = "Releve table (overwrites releve_names).",
                            type = str, default = None)
    parser.add_argument("-from_checkpoint", "--from_cpt",
                        help = "Load previous instance of Batchrequest.",
                            type = bool, default = False)
    parser.add_argument("-shutdown", "--shutdown",
                        help = "Shutdown computer after batch is finished.",
                            action = "store_true")
    parser.add_argument("-r", "--overwrite",
                        help = "Overwrite existing results in the BR file.",
                            nargs = "+", type = str, default = None)
    parser.add_argument("-f", "--filename",
                        help = "Filename of a specific saved batchrequest" + \
                            " to be loaded and continued/edited.",
                        type = str, default = None)
    parser.add_argument("-add_florincog", "--florinc",
                        help = "Insert Flora Incognita results into an " + \
                            "existing Batrchrequest save.",
                        type = str, default = None)
    
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()
    dir_out = args.output_directory
    RELEVENAMES = args.releve_names if isinstance(args.releve_names, list) \
        else [args.releve_names]
    
    RELEVETABLE = args.releve_table
    FROMCPT = args.from_cpt
    OVERWRITE = args.overwrite
    LOADFILE = args.filename
    FLORINC = args.florinc
    
    
    if FLORINC is not None and OVERWRITE is not None:
        mssg = "Argument '-add_florincog' cannot be used in combination " + \
            "with '-overwrite'."
        
        raise Exception(mssg)
    
    if FLORINC is not None:
        RELEVETABLE = ""
    
    else:
        if RELEVETABLE == "standard":
            print("Attempting to use standard releve table...")
            
            RELEVETABLE = os.path.join(dir_main, "spl", "Releve_table.xlsx")
            
            if not os.path.isfile(RELEVETABLE):
                
                raise Warning("Unable to locate standard releve table.")
    
    if os.path.isfile(RELEVETABLE):
        releve_df = pd.read_excel(RELEVETABLE, sheet_name = "Batch_request")
        idx = releve_df[releve_df["include"] == True].index
        
        ## Overwrite RELEVENAMES list with selection from table
        RELEVENAMES = releve_df.loc[idx, "name"]
    
    if OVERWRITE is not None:
        MULTIIMG = [i for i in MULTIIMG if i in OVERWRITE]
        MODELLIST = [i for i in MODELLIST if i in OVERWRITE]

#-----------------------------------------------------------------------------|
# Functions
def out_file(name, *subdirs):
    '''
    Generate file location within the selected output directory.

    Parameters
    ----------
    name : str
        Filename.
    *subdirs : str or list of str, optional
        Additional subdirectories inbetween the main output directory and the
        file.

    Returns
    -------
    path : str
        File path.
    '''
    path = os.path.join(dir_out, *subdirs, name)
    
    return path

def read_meta():
    '''
    Read metadata for the downloaded images. (See infoflora.py for further
    information)

    Returns
    -------
    metadata : dict
        Dictionary containing dates, tags, file loctions, etc. of all images
        downloaded via infoflora.py.
    relevedict : dict
        Dictionary containing releve information. (Used to link releve names
        to releve IDs.)
    '''
    with open(os.path.join(IMGDIR, "META.pickle"), "rb") as f:
        metadata = pk.load(f)
    
    with open(os.path.join(IMGDIR, "RELEVE.dict"), "rb") as f:
        relevedict = pk.load(f)
    
    return metadata, relevedict

def load_checkpoint(file = None, from_error = "auto"):
    '''
    Load pickled checkpoint of the last Batchrequest instance that has been
    running.
    
    Parameters
    ----------
    from_error : str/bool
        Restart from last error. (Alternative: Restart from last finished
        observation.) Default: "auto"; i.e., use the most recent checkpoint
        irrespective of checkpoint type.
    
    Returns
    -------
    br_cpt : Batchrequest
        Instance of type Batchrequest.
    
    Note
    ----
    Consider that you probably want to exclude previously finished releves from
    the releve_name_list when running a batch request using a checkpoint.
    '''
    if file is not None:
        name = file
    
    else:
        if isinstance(from_error, bool):
            name = "at_last_exception" if from_error else "cpt.save"
        
        else:
            cpt_names = os.listdir(out_file("log"))
            cpt_dirs = [out_file(n, "log") for n in cpt_names]
            
            name = os.path.split(max(cpt_dirs, key = os.path.getmtime))[1]
    
    with open(out_file(name, "log"), "rb") as f:
        br_cpt = pk.load(f)
    
    return br_cpt

#-----------------------------------------------------------------------------|
# Classes
class Batchrequest():
    def __init__(self, out_dir = out_file("log")):
        past_batches = glob.glob(os.path.join(out_dir, "Batch_*"))
        
        if len(past_batches) > 0:
            ids = [os.path.split(f)[1] for f in past_batches]
            current_max_id = max([int(re.findall(r"\d+", i)[0]) for i in ids])
        
        else:
            current_max_id = -1
        
        self.id = current_max_id + 1
        self.name = "Batch_" + str(self.id).zfill(10)
        self.finished_releves = []
        self.last_observation_index = 0
        self.t_start = datetime.now()
        self.results = []
        self.errors = []
        self.store_n = NTOP
        self.total_releve_names = []
        self.version = "1.0.2"
    
    def run_batch(self, releve_name_list,
                  start_from_releve = 0,
                  to_releve = None,
                  start_from_observation = None,
                  to_observation = None,
                  continue_batch = True,
                  overwrite = False,
                  checkpoints = True):
        '''
        Run a batch of requests.

        Parameters
        ----------
        releve_name_list : str, list
            List of releve names to include in the batch.
        start_from_releve : int, optional, debugging
            Start the batch from a certain releve index.
            The default is 0.
        to_releve : int, optional, debugging
            Stop the batch at a certain releve index.
            The default is None.
        start_from_observation : int, optional, debugging
            Start with a certain observation within the releve.
            The default is 0.
        to_observation : int, optional, debugging
            Stop at a certain observation index.
            The default is None.
        continue_batch : bool, optional
            Continue batch in case the batch is resumed (after an error). If
            True, previously finished batches will be dropped from the releve
            name list.
        
        Notes
        -----
        The optional parameters might be useful if an error occurred and the
        process must be started at a specific request.

        Returns
        -------
        None.
        '''
        self.total_releve_names = list(
            set(self.total_releve_names + list(releve_name_list))
            )
        
        metadata, relevedict = read_meta()
        
        self.parameters = {
            "releve_name_list" : releve_name_list,
            "start_from_releve" : start_from_releve,
            "to_releve" : to_releve,
            "start_from_observation" : start_from_observation,
            "to_observation" : to_observation
            }
        
        ## Remove previously finished releves from releve name list
        if continue_batch:
            for r in self.finished_releves:
                releve_name_list = list(releve_name_list)
                
                if r in releve_name_list:
                    releve_name_list.remove(r)
            
            start_from_observation = self.last_observation_index
        
        start_from_observation = 0 if start_from_observation is None else \
            start_from_observation
        
        for releve_index, releve_name in enumerate(
                releve_name_list[start_from_releve:to_releve],
                start = start_from_releve
                ):
            
            ## Extract current releve id based on releve name
            releve_id = relevedict[releve_name]
            
            print("|" + "-" * 77 + "|")
            print("Current releve\nName: {0}\nID: {1}\n".format(releve_name,
                                                                releve_id))
            
            ## Get subset of observations that belong to the current releve
            releve_observations = [val for val in metadata.values() if \
                                   val["releve_id"] == releve_id]
            
            if len(releve_observations) == 0:
                mssg = "No observations found for releve name {0} (= relev" + \
                    "e_id {1}, index {2} in current batch run.)"
                
                self.errors.append({
                    "index" : releve_index,
                    "releve_name" : releve_name,
                    "releve_id" : releve_id,
                    "error_type" : "No observations found."
                    })
                
                raise Warning(
                    mssg.format(releve_name, releve_id, releve_index)
                    )
                
                continue
            
            start = start_from_observation if releve_index == 0 else 0
            
            for oidx, observation in enumerate(
                    releve_observations[start:to_observation], start = start
                    ):
                try:
                    image_files = observation["file_locations"]
                    observation_id = observation["obs_id"]
                    true_taxon_id = observation["taxon_id"]
                    date = observation["date"]
                    coordinates = (observation["y"], observation["x"])
                    img_types = observation["img_types"]
                
                except:
                    mssg = "Failed to read observation information for" + \
                        " observation {0} in releve {1} (releve_id = {2})."
                    
                    self.errors.append({
                        "index" : releve_index + start_from_releve,
                        "releve_name" : releve_name,
                        "releve_id" : releve_id,
                        "obs_index" : oidx + start_from_observation,
                        "error_type" : "Failed to read metadata tag."
                        })
                    
                    raise Warning(
                        mssg.format(oidx, releve_name, releve_id)
                        )
                    
                    continue
                
                mssg = "-" * 35 + "\nReleve: {0}\nObservation: {1}\n"
                print(mssg.format(releve_name, observation["obs_id"]))
                
                ## Send single image request to each model in model list
                for idx, (image_path, organ) in enumerate(
                        zip(image_files, img_types)
                        ):
                    
                    for CV in MODELLIST:
                        ### Send request with single image
                        print(
                            "Requesting single-image ID from {0}.".format(CV)
                            )
                        
                        ### Handle warnings (in particular, the iNaturalist
                        ### VisionAPI quota limit warning)
                        try:
                            mod_name, best_matches, full_json = \
                                self._standard_task(
                                    image_path = image_path,
                                    coordinates = coordinates,
                                    date = date,
                                    organs = organ,
                                    cv_model = CV,
                                    batch = self.name
                                    )
                        
                        except:
                            mssg = "Current obs.: {0}\nCurrent releve idx: {1}"
                            print(mssg.format(oidx, releve_index))
                            self._checkpoint("at_last_exception")
                            
                            mssg = "Stumbled upon warning. Check API quotas."
                            raise Exception(mssg)
                    
                        ### Add response to results
                        result_dict = {
                            "question_index" : idx,
                            "question_type" : "single_image",
                            "releve_index" : releve_index + start_from_releve,
                            "releve_name" : releve_name,
                            "releve_id" : releve_id,
                            "observation_index" : oidx + start_from_observation,
                            "observation_id" : observation_id,
                            "true_taxon_id" : true_taxon_id,
                            "plant_organ" : organ,
                            "image_files" : image_path,
                            "cv_model" : CV,
                            "taxon_suggestions" : best_matches,
                            "full_json" : full_json
                            }
                        
                        ### Append results list if overwriting is deactivated
                        if not overwrite:
                            self.results.append(result_dict)
                        
                        else:
                            ### Overwrite results if an entry for the same
                            ### releve, request, and model is present in the
                            ### existing results list.
                            rm = [str(r["releve_id"]) + str(r["cv_model"]) + \
                                  str(r["image_files"]) for r in self.results]
                            
                            curr_entr = str(result_dict["releve_id"]) + \
                                    str(result_dict["cv_model"]) + image_path
                            
                            if curr_entr in rm:
                                self.results[rm.index(curr_entr)] = result_dict
                            
                            else:
                                self.results.append(result_dict)
                    
                    ### If only testing one CV model, wait for 3 s between
                    ### API requests
                    if len(MODELLIST) == 1:
                        time.sleep(3)
                
                ## Send multi-image request to cv models that support it
                for CV in MULTIIMG:
                    print("Requesting multi-image ID from {0}.".format(CV))
                    
                    ### Increase counter
                    idx += 1
                    
                    ### Select 5 images in case more were provided
                    ### To this end, first get the first element for each indi-
                    ### vidual plant organ category.
                    indices = [img_types.index(t) for t in set(img_types)]
                    
                    ### Remove the selected images from the list of remaining
                    ### images
                    remaining = list(range(len(image_files)))
                    
                    for i in indices:
                        remaining.remove(i)
                    
                    ### Fill up remaining places with random images
                    if len(remaining) > 0:
                        n_additional = min(
                            len(remaining), NSAMPLES - len(indices)
                            )
                        
                        indices += random.sample(remaining, k = n_additional)
                    
                    indices.sort()
                    
                    ### Select subset from photo list
                    #### Select random images
                    image_paths = [image_files[i] for i in indices]
                    organs = [img_types[i] for i in indices]
                    
                    replace_original = False
                    
                    if overwrite:
                        #### If entries are to be replaced, look up which
                        #### images have been used and replace random selection
                        rm = [str(r["releve_id"]) + str(r["cv_model"]) \
                              for r in self.results]
                        
                        curr_entr = str(result_dict["releve_id"]) + \
                                str(result_dict["cv_model"])
                        
                        if curr_entr in rm:
                            r = self.results[rm.index(curr_entr)]
                            image_paths = r["image_files"].split("; ")
                            organs = r["plant_organ"].split("; ")
                            
                            replace_original = True
                    
                    ### Send requests with selected images
                    mod_name, best_matches, full_json = self._standard_task(
                        image_path = image_paths,
                        coordinates = coordinates,
                        date = date,
                        organs = organs,
                        cv_model = CV,
                        batch = self.name
                        )
                    
                    result_dict = {
                        "question_index" : idx,
                        "question_type" : "multi_image",
                        "releve_index" : releve_index + start_from_releve,
                        "releve_name" : releve_name,
                        "releve_id" : releve_id,
                        "observation_index" : oidx + start_from_observation,
                        "observation_id" : observation_id,
                        "true_taxon_id" : true_taxon_id,
                        "plant_organ" : ";".join(organs),
                        "image_files" : ";".join(image_paths),
                        "cv_model" : CV,
                        "taxon_suggestions" : best_matches,
                        "full_json" : full_json
                        }
                    
                    ### Replace results list entry if overwriting is activated
                    if replace_original:
                        ### Overwrite results if an entry for the same releve,
                        ### request, and model is present in the existing
                        ### results list.
                        self.results[rm.index(curr_entr)] = result_dict
                    
                    else:
                        ### Else, append results list
                        self.results.append(result_dict)
                
                self.last_observation_index = oidx
            
            self.finished_releves.append(releve_name)
            
            # Save as checkpoint to reduce data loss in case of error
            if checkpoints:
                self._checkpoint()
    
    def _standard_task(self, image_path, coordinates, date, organs, cv_model,
                      return_n = NTOP, batch = None):
        '''
        Run standard task (identify species and return the N best matches in a
        standardised format).

        Parameters
        ----------
        image_path : str
            Path to the image file.
        coordinates : list
            List of coordinates of the observation location (lat, lon).
        date : str
            Date of the observation in format "yyyy-mm-dd".
        organs : str
            Tags for plant organ. Must be in ["f", "i", "s", "t", "v"] where
            "f" = infructescence
            "i" = inflorescence
            "s" = several parts
            "t" = trunk
            "v" = vegetative parts
        cv_model : str
            Computer vision model/API to call. Options are "plantnet",
            "inaturalist", "florid".
        return_n : int, optional
            Number of species suggestions to return. The default is 5.

        Returns
        -------
        list
            List containing CV model name, N best matches, and the full
            response json.
        
        Notes
        -----
        This was a standalone function in the first verion. I made it a method
        in order to be able to access "self" and save checkpoints when running
        out of free API requests.
        '''
        if cv_model == "plantnet":
            try:
                response = plantnet.post_image(image_path, organs = organs)
                ids = plantnet.species_ranking(response, n = return_n)
                
                remaining_requests = int(
                    response["remainingIdentificationRequests"]
                    )
            
            except KeyError:
                ### PlantNet API responses are not consistent. We try two times
                ### to get a response in the expected format.
                print("API response format invalid. Repeating request...")
                response = plantnet.post_image(image_path, organs = organs)
                ids = plantnet.species_ranking(response, n = return_n)
                
                remaining_requests = int(
                    response["remainingIdentificationRequests"]
                    )
            
            ## Since PlantNet only allows 500 IDs on the base subscription
            ## (without additional payment or exception status), we wait for
            ## 24 hrs in case the quota is reached
            if remaining_requests <= 0:
                mssg = "Daily PlantNet API quota reached. I will sleep for" + \
                    " %s hours, %s minutes, and %s seconds to continue " + \
                        "the batch at midnight."
                
                now = datetime.now()
                tomorrow = now + timedelta(days = 1)
                midnight = datetime(
                    tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, 0
                    )
                
                d = midnight - now
                
                print(mssg % tuple(str(d).split(":")))
                
                self._checkpoint()
                
                time.sleep(d.total_seconds())
        
        elif cv_model == "inaturalist":
            response = inaturalistcv.post_image(image_path, coordinates)
            
            ids = inaturalistcv.species_ranking(response, n = return_n)
        
        elif cv_model == "florid":
            response = florid.post_image(image_path, coordinates, date)
            ids = florid.species_ranking(response, n = return_n)
        
        else:
            floraincognita.post_image(image_path, batch)
            response = []
            ids = []
        
        return [cv_model, ids, response]
    
    def _insert_manual(self):
        '''
        Insert results from manually generated Flora Incognita results .json
        into a previously generated Batchrequest object.
        
        Raises
        ------
        Exception
            Raises an Exception in case the Batchrequest object contains no
            previously populated results structure into which the Flora
            Incognita results can be injected.
        
        Returns
        -------
        None.
        '''
        if len(self.results) > 0:
            insert_florinc(self)
        
        else:
            raise Exception(
                "Batchrequest object contains no editable results."
                )
    
    def try_fix_errors(self):
        '''
        Search Batchrequest object for missing API responses and try to fix
        them.
        
        Parameters
        ----------
        releve_name_list : list
            List of releve names to include.
        
        Returns
        -------
        None.
        '''
        metadata, relevedict = read_meta()
        
        fixed_errors = []
        print("Searching for missing data...")
        
        for releve_index, releve_name in enumerate(self.total_releve_names):
            ## Extract current releve id based on releve name
            releve_id = relevedict[releve_name]
            
            ## Get subset of observations that belong to the current releve
            releve_obs = [val for val in metadata.values() if \
                          val["releve_id"] == releve_id]
            
            ## Find releve in results
            found = [i for i, r in enumerate(self.results) if \
                     r["releve_name"] == releve_name]
            
            if len(found) < 1:
                print("Found missing releve: " + releve_name)
                
                self.run_batch(releve_name_list = releve_name,
                               continue_batch = True)
                
                fixed_errors.append(releve_name)
            
            else:
                releve_results = [self.results[f] for f in found]
                
                for oidx, observation in enumerate(releve_obs):
                    observation_results = [
                        r for r in list(releve_results) if \
                            r["observation_id"] == observation["obs_id"]
                        ]
                    
                    n_files = len(observation["file_locations"])
                    n_single = len(MODELLIST)
                    n_multi = len(MULTIIMG)
                    
                    if len(observation_results) < n_files * n_single + n_multi:
                        print("Found incomplete releve: " + releve_name)
                        
                        self.run_batch(releve_name_list = self \
                                       .total_releve_names,
                                      start_from_releve = releve_index,
                                      to_releve = releve_index + 1,
                                      start_from_observation = oidx,
                                      to_observation = oidx + 1,
                                      continue_batch = False,
                                      overwrite = False,
                                      checkpoints = False)
                        
                        fixed_errors.append(releve_name)
                    
                    else:
                        print("Releve {0} complete with {1} responses." \
                                .format(releve_name, len(observation_results))
                                )
        
        if len(fixed_errors) > 0:
            self._checkpoint(name = self.name + "_fixed")
        
        else:
            print("Error check status: OK.")
    
    def _checkpoint(self, name = "cpt.save"):
        '''
        Create checkpoint of current instance.
        
        Returns
        -------
        None.
        '''
        with open(out_file(name, "log"), "wb") as f:
            pk.dump(self, f)
        
        print("Checkpoint saved.")
    
    def save(self):
        '''
        Save current instance.
        
        Returns
        -------
        None.
        '''
        with open(out_file(self.name, "log"), "wb") as f:
            pk.dump(self, f)
        
        print("Output saved at {0}.".format(str(out_file(self.name, "log"))))
    
    def to_df(self):
        '''
        Return the results as a pandas.DataFrame.
        
        Returns
        -------
        out : pandas.DataFrame
            Dataframe containing the API responses.
        '''
        df = pd.DataFrame(BR.results)
        
        colnames = ["first", "second", "third", "forth", "fifth"]
        taxa = pd.DataFrame(df["taxon_suggestions"].to_list(),
                            columns = colnames)
        
        main = df[["question_index", "question_type", "releve_index",
                   "releve_name", "releve_id", "observation_index",
                   "observation_id", "true_taxon_id", "plant_organ",
                   "image_files", "cv_model"]]
        
        out = pd.concat([main, taxa], axis = 1)
        
        return out

#-----------------------------------------------------------------------------|
# Run request
if FROMCPT:
    BR = load_checkpoint()
    BR.run_batch(releve_name_list = RELEVENAMES)

elif OVERWRITE is not None:
    BR = load_checkpoint(file = LOADFILE)
#    BR.total_releve_names = RELEVENAMES # Use to update older versions of BR
    
    print("Overwriting entries for " + ", ".join(MODELLIST))
    
    BR.run_batch(releve_name_list = RELEVENAMES, overwrite = True,
                 continue_batch = False)

elif FLORINC is not None:
    BR = load_checkpoint(file = FLORINC)
    BR._insert_manual()

else:
    BR = Batchrequest()
    BR.run_batch(releve_name_list = RELEVENAMES)

BR.save()
BR.try_fix_errors()

# Export data as Excel sheet
df = BR.to_df()

## Add species names (using the Info Flora taxonomic backbone)
SD = base.SpeciesDecoder("comeco_local")

df["true_taxon_name"] = [SD.decode(tid) for tid in df["true_taxon_id"]]

## Drop duplicates from dataframe
df = df.drop_duplicates(subset = ["releve_name", "observation_id",
                                    "true_taxon_id", "plant_organ",
                                    "image_files", "cv_model"],
                          keep = "last")

## Save to Excel file
if os.path.isfile(out_file("Responses.xlsx")):
    with pd.ExcelWriter(out_file("Responses.xlsx"), mode = "a",
                        if_sheet_exists = "replace") as writer:
        df.to_excel(writer, sheet_name = BR.name, index = False)
    
else:
    df.to_excel(out_file("Responses.xlsx"), sheet_name = BR.name,
                index = False)

# Shutdown system if shutdown flag was set
if args.shutdown:
    cmd = "shutdown /s /t 1" if platform.system() == "Windows" \
        else "systemctl poweroff"
    
    os.system(cmd)