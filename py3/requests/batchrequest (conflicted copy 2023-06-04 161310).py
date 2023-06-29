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
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

#-----------------------------------------------------------------------------|
# Imports
import os, re, glob, time, datetime, random, argparse
import pandas as pd
import pickle as pk
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import plantnet, inaturalistcv, localflorid

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

IMGDIR = "N:/prj/COMECO/img"
MULTIIMG = ["florid", "plantnet"]
MODELLIST = ["florid", "inaturalist", "plantnet"]
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
    
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()
    dir_out = args.output_directory
    RELEVENAMES = args.releve_names if isinstance(args.releve_names, list) \
        else [args.releve_names]
    RELEVETABLE = args.releve_table
    FROMCPT = args.from_cpt
    
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

def standard_task(image_path, coordinates, date, organs, cv_model,
                  return_n = NTOP):
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
        Tags for plant organ/part. Must be in ["f", "i", "s", "t", "v"] where
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
        List containing CV model name, N best matches, and the full response
        json.
    '''
    if cv_model == "plantnet":
        response = plantnet.post_image(image_path, organs = organs)
        ids = plantnet.species_ranking(response, n = return_n)
        
        ## Since PlantNet only allows 500 IDs on the base subscription (without
        ## additional payment or exception status), we wait for 24 hrs in case
        ## the quota is reached
        if response["remainingIdentificationRequests"] <= 0:
            mssg = "PlantNet API quota reached. I will sleep for 24 hrs " + \
                "and continue the batch then."
            
            print(mssg)
            
            time.sleep(24 * 60 * 60)
    
    elif cv_model == "inaturalist":
        response = inaturalistcv.post_image(image_path, coordinates)
        
        ids = inaturalistcv.species_ranking(response, n = return_n)
    
    else:
        response = localflorid.post_image(image_path, coordinates, date)
        ids = localflorid.species_ranking(response, n = return_n)
    
    return [cv_model, ids, response]

def load_checkpoint():
    '''
    Load pickled checkpoint of the last Batchrequest instance that has been
    running.

    Returns
    -------
    br_cpt : Batchrequest
        Instance of type Batchrequest.
    
    Note
    ----
    Consider that you probably want to exclude previously finished releves from
    the releve_name_list when running a batch request using a checkpoint.
    
    '''
    with open(out_file("cpt.save", "log"), "rb") as f:
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
    
    def run_batch(self, releve_name_list,
                  start_from_releve = 0,
                  to_releve = None,
                  start_from_observation = None,
                  to_observation = None,
                  continue_batch = True):
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
        metadata, relevedict = read_meta()
        
        self.parameters = {
            "releve_name_list" : releve_name_list,
            "start_from_releve" : start_from_releve,
            "to_releve" : to_releve,
            "start_from_observation" : start_from_observation,
            "to_observation" : to_observation
            }
        
        self.t_start = datetime.datetime.now()
        self.results = []
        self.errors = []
        
        ## Remove previously finished releves from releve name list
        if continue_batch:
            for r in self.finished_releves:
                releve_name_list = list(releve_name_list)
                releve_name_list.remove(r)
            
            start_from_observation = self.last_observation_index
        
        start_from_observation = 0 if start_from_observation is None else \
            start_from_observation
        
        for releve_index, releve_name in enumerate(
                releve_name_list[start_from_releve:to_releve]
                ):
            
            ## Extract current releve id based on releve name
            releve_id = relevedict[releve_name]
            
            print("Current releve\nName: {0}\nID: {1}\n".format(releve_name,
                                                                releve_id))
            
            ## Get list of releve ids from observation metadata
            observation_releve_ids = [m["releve_id"] for m in metadata]
            
            ## Get locations of observations that belong to the current releve
            locs = [i for i, rid in enumerate(observation_releve_ids) \
                    if rid == releve_id]
            
            ## Get subset of observations that belong to the current releve
            releve_observations = [metadata[l] for l in locs]
            
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
                    releve_observations[start:to_observation]
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
                            mod_name, best_matches, full_json = standard_task(
                                image_path = image_path,
                                coordinates = coordinates,
                                date = date,
                                organs = organ,
                                cv_model = CV
                                )
                        except:
                            mssg = "Current obs.: {0}\nCurrent releve idx´: {1}"
                            print(mssg.format(oidx, releve_index))
                            self._checkpoint("at_last_exception")
                            
                            mssg = "Stumbled upon warning. Check API quotas."
                            raise Exception(mssg)
                    
                        ### Add response to results
                        self.results.append({
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
                            })
                    
                    ### If only testing one CV model, wait for 1.5 s between
                    ### API requests
                    if len(MODELLIST) == 1:
                        time.sleep(1.5)
                
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
                    image_paths = [image_files[i] for i in indices]
                    organs = [img_types[i] for i in indices]
                    
                    ### Send requests with selected images
                    mod_name, best_matches, full_json = standard_task(
                        image_path = image_paths,
                        coordinates = coordinates,
                        date = date,
                        organs = organs,
                        cv_model = CV
                        )
                    
                    self.results.append({
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
                        })
                
                self.last_observation_index = oidx
            
            self.finished_releves.append(releve_name)
            
            # Save as checkpoint to reduce data loss in case of error
            self._checkpoint()
    
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

#-----------------------------------------------------------------------------|
# Run request
BR = load_checkpoint() if FROMCPT else Batchrequest()
BR.run_batch(releve_name_list = RELEVENAMES)
BR.save()