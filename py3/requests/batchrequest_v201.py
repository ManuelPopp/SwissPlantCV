#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 24 16:35:35 2023

Send requests to the APIs of the various CV models tested in this study.
"""
__author__ = "Manuel"
__date__ = "Wed May 24 16:35:35 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "2.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Production"

#-----------------------------------------------------------------------------|
# Imports
import os, re, glob, time, random, argparse, platform
import pandas as pd
import pickle as pk
from datetime import datetime, timedelta
from alive_progress import alive_bar as pb
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import base
import plantnet, inaturalistcv, florid, floraincognita
from floraincognita import insert as insert_florinc

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.getcwd())# for debugging in IDE
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

if __name__ == "__main__":
    IMGDIR = "N:/prj/COMECO/img"
    MULTIIMG = ["florid", "floraincognita", "plantnet"]
    MODELLIST = ["florid", "floraincognita", "inaturalist", "plantnet"]
else:
    IMGDIR = None
    MULTIIMG = []
    MODELLIST = []

TAXONTABLE = os.path.join(dir_main, "dat", "Taxonomic_backbone_wHier_2022.csv")
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
                            type = str, default = "standard")
    parser.add_argument("-from_checkpoint", "--from_cpt",
                        help = "Load previous instance of Batchrequest.",
                            type = bool, default = False)
    parser.add_argument("-s", "--shutdown",
                        help = "Shutdown computer after batch is finished.",
                            action = "store_true")
    parser.add_argument("-f", "--filename",
                        help = "Filename of a specific saved batchrequest" + \
                            " to be loaded and continued/edited.",
                        type = str, default = None)
    parser.add_argument("-add_florincog", "--florinc",
                        help = "Insert Flora Incognita results into an " + \
                            "existing Batrchrequest save.",
                        type = str, default = None)
    parser.add_argument("-manual_update", "--mupdate",
                        help = "Edit entries in existing Batrchrequest save.",
                        type = str, default = None, nargs = "+")
    parser.add_argument("-r", "--repeat",
                        help = "Repeat requests for specific CV models.",
                        nargs = "+",
                        type = str, default = [])
    parser.add_argument("-u", "--update_fixed",
                        help = "Update plant part and taxon information." +
                        " Note: When -u is set, no requests will be started." +
                        " In order to continue an interrupted batch, run " +
                        "again without the -u flag after updating fixed " +
                        "InfoFlora entries.",
                        action = "store_true")
    
    args = parser.parse_args()
    
    return args

if __name__ == "__main__":
    args = parseArguments()
    dir_out = args.output_directory
    RELEVENAMES = args.releve_names if isinstance(args.releve_names, list) \
        else [args.releve_names]
    
    RELEVETABLE = args.releve_table
    FROMCPT = args.from_cpt
    LOADFILE = args.filename
    FLORINC = args.florinc
    MANUALUPDATE = args.mupdate
    REPEAT = args.repeat if isinstance(args.repeat, list) else [args.repeat]
    UPDATEFIXED = args.update_fixed
    
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

#-----------------------------------------------------------------------------|
# Classes
class Batchrequest():
    def __init__(self, img_dir = IMGDIR, out_dir = OUT,
                 single = MODELLIST, multi = MULTIIMG):
        '''
        Initialise instance of type Batchrequest.
        
        Parameters
        ----------
        img_dir : str, optional
            Directory of the image collection. The default is IMGDIR.
        out_dir : str, optional
            Output directory for logs and results. The default is OUT.
        single : list, optional
            List of CV model keys for models to which single-image requests
            shall be sent. The default is MODELLIST.
        multi : list, optional
            List of CV model keys for models to which multi-image requests
            shall be sent. The default is MULTIIMG.
        
        Returns
        -------
        Batchrequest object.
        '''
        self.out_dir = out_dir
        self.log_dir = self.path_out("log")
        
        past_batches = glob.glob(os.path.join(self.log_dir, "Batch_*"))
        
        if len(past_batches) > 0:
            ids = [os.path.split(f)[1] for f in past_batches]
            current_max_id = max([int(re.findall(r"\d+", i)[0]) for i in ids])
        
        else:
            current_max_id = -1
        
        self.id = current_max_id + 1
        self.name = "Batch_" + str(self.id).zfill(10)
        self.single = self._list_input(single)
        self.multi = self._list_input(multi)
        self.finished_releves = []
        self.t_init = datetime.now()
        self.results = {}
        self.errors = []
        self.store_n = NTOP
        self.total_releve_names = []
        self.version = "2.0.1"
        
        self.set_image_dir(img_dir)
        self.florid_taxonomy = None
    
    @property
    def _image_meta(self):
        image_meta, releve_dict = self.read_meta()
        
        return image_meta
    
    @property
    def _releve_dict(self):
        image_meta, releve_dict = self.read_meta()
        
        return releve_dict
    
    @property
    def total_releve_ids(self):
        ids = [self._releve_dict_static[name] for name in \
               self.total_releve_names]
        
        return ids
    
    @property
    def pending(self):
        '''
        Get list of pending requests.
        
        Returns
        -------
        list
            List of pending requests with their releve name, observation id,
            image (either a path or "multi"), plant organ, and CV model.
        '''
        pending = []
        
        for observation in self._image_meta_static.values():
            if observation["releve_id"] in self.total_releve_ids:
                releve_name = self._releve_dict_static_inv[
                    observation["releve_id"]
                    ]
                
                observation_id = observation["obs_id"]
                image_dict_vals = self._get_image_dict(observation_id).values()
                paths = [x["disc_location"] for x in image_dict_vals]
                parts = [x["organ"] for x in image_dict_vals]
                
                for cv_model, mode, part in zip(
                        self.single * len(paths) + self.multi,
                        [p for p in paths for q in range(
                            len(self.single)
                            )] + ["multi"] * len(self.multi),
                        [p for p in parts for q in range(
                            len(self.single)
                            )] + ["multi"] * len(self.multi)
                        ):
                    try:
                        exists = isinstance(
                            self.results[releve_name][observation_id] \
                                [mode][cv_model], dict
                            )
                        
                        if not exists:
                            p = "multi" if mode == "multi" else part
                            pending.append([
                                releve_name, observation_id, mode, p,
                                cv_model
                                ])
                    
                    except:
                        p = "multi" if mode == "multi" else part
                        
                        pending.append([
                            releve_name, observation_id, mode, p, cv_model
                             ])
        
        return sorted(pending, key = lambda x: x[0])
    
    @property
    def completed_releves(self):
        pending = set([p[0] for p in self.pending])
        
        completed = [n for n in self.total_releve_names if n not in pending]
        
        return completed
    
    def set_image_dir(self, img_dir):
        '''
        Set image directory and load image file collection metadata.
        
        Parameters
        ----------
        img_dir : str
            Image file collection directory. Must contain a META.pickle file.
        
        Returns
        -------
        None.
        '''
        self.image_dir = img_dir
        
        self.update_image_dicts()
    
    def update_image_dicts(self):
        '''
        Update image metadata and releve dictionaries.
        
        Returns
        -------
        None.
        '''
        self._image_meta_static, self._releve_dict_static = self.read_meta()
        
        self._releve_dict_static_inv = {key : value for value, key in \
                                        zip(self._releve_dict_static.keys(),
                                            self._releve_dict_static.values())}
    
    def read_meta(self):
        '''
        Read metadata for the downloaded images. (See infoflora.py for further
        information)
        
        Returns
        -------
        metadata : dict
            Dictionary containing dates, tags, file loctions, etc. of all
            images downloaded via infoflora.py.
        relevedict : dict
            Dictionary containing releve information. (Used to link releve
            names to releve IDs.)
        '''
        with open(os.path.join(self.image_dir, "META.pickle"), "rb") as f:
            metadata = pk.load(f)
        
        with open(os.path.join(self.image_dir, "RELEVE.dict"), "rb") as f:
            relevedict = pk.load(f)
        
        for obs in metadata.values():
            obs["file_locations"] = [
                os.path.join(
                    self.image_dir,
                    os.path.basename(os.path.dirname(os.path.dirname(path))),
                    os.path.basename(os.path.dirname(path)),
                    os.path.basename(path)
                    ) for path in obs["file_locations"]
                ]
        
        return metadata, relevedict
    
    def translate_id(self, infoflora_id, id_table = TAXONTABLE):
        '''
        Translate Info Flora taxon ID to FlorID taxon ID.
        
        Parameters
        ----------
        infoflora_id : int
            Info FLora taxon ID.
        id_table : str, optional
            Path to the FLorID taxonomic backbone table. The default is
            TAXONTABLE (= [main dir]/dat/Taxonomic_backbone_wHier_2022.csv).
        
        Returns
        -------
        taxon_id : int
            FlorID taxon ID.
        '''
        if not isinstance(self.florid_taxonomy, pd.core.frame.DataFrame):
            self.florid_taxonomy = pd.read_table(TAXONTABLE, sep = ",")
        
        try:
            taxon_id = self.florid_taxonomy["COMECO_ID"][
                self.florid_taxonomy["ID"] == infoflora_id
                ].values[0]
        
        except:
            mssg = "Info Flora ID {0} not found in taxonomy backbone."
            print(mssg.format(infoflora_id))
            
            taxon_id = None
        
        return taxon_id
    
    def add_releves(self, releve_name_list):
        '''
        Add releves to include during the batch request by name.
        
        Parameters
        ----------
        releve_name_list : list
            List containing the releve names.
        
        Returns
        -------
        None.
        '''
        releve_name_list = self._list_input(releve_name_list)
        
        self.total_releve_names += releve_name_list
        self.total_releve_names = list(set(self.total_releve_names))
        
        self.parameters = {
            "releve_name_list" : releve_name_list
            }
    
    def single_image_request(self,
                             cv_model,
                             image_path,
                             coordinates,
                             date,
                             organ,
                             releve_name,
                             releve_id,
                             observation_id,
                             true_taxon_id = 1037510
                             ):
        '''
        Send API request using a single image.
        
        Parameters
        ----------
        cv_model : str
            Key of the CV model.
        image_path : list
            List containing the image file path.
        coordinates : TYPE
            DESCRIPTION.
        date : str
            Date of the observation.
        organs : list
            List containing a key indicating the depicted plant part.
        releve_name : str
            Releve name.
        releve_id : int
            Releve ID.
        observation_id : int
            Observation ID.
        true_taxon_id : int
            Taxon ID of the observed plant, following the InfoFlora taxonomy.
        
        Returns
        -------
        result_dict : dict
            Dictionary containing the API response.
        '''
        print("Requesting single-image ID from {0}.".format(cv_model))
        
        mod_name, best_matches, full_json = \
            self._standard_task(
                image_path = image_path,
                coordinates = coordinates,
                date = date,
                organs = organ,
                cv_model = cv_model,
                batch = self.name,
                req_id = true_taxon_id# -> this causes errors when ID is not in the Comeco ID list!!!
                )
    
        ### Create results dict
        result_dict = {
            "timestamp" : datetime.now(),
            "question_type" : "single_image",
            "releve_name" : releve_name,
            "releve_id" : releve_id,
            "observation_id" : observation_id,
            "true_taxon_id" : true_taxon_id,
            "plant_organ" : organ,
            "image_files" : image_path,
            "cv_model" : cv_model,
            "taxon_suggestions" : best_matches,
            "full_json" : full_json
            }
        
        return result_dict
    
    def multi_image_request(self,
                             cv_model,
                             image_paths,
                             coordinates,
                             date,
                             organs,
                             releve_name,
                             releve_id,
                             observation_id,
                             true_taxon_id
                             ):
        '''
        Send API request using multiple images.
        
        Parameters
        ----------
        cv_model : str
            Key of the CV model.
        image_paths : list
            List of image file paths.
        coordinates : TYPE
            DESCRIPTION.
        date : str
            Date of the observation.
        organs : list
            List of keys indicating the depicted plant parts.
        releve_name : str
            Releve name.
        releve_id : int
            Releve ID.
        observation_id : int
            Observation ID.
        true_taxon_id : int
            Taxon ID of the observed plant, following the InfoFlora taxonomy.
        
        Returns
        -------
        result_dict : dict
            Dictionary containing the API response.
        '''
        print("Requesting multi-image ID from {0}.".format(cv_model))
        
        ### Send requests with selected images
        mod_name, best_matches, full_json = self._standard_task(
            image_path = image_paths,
            coordinates = coordinates,
            date = date,
            organs = organs,
            cv_model = cv_model,
            batch = self.name,
            req_id = true_taxon_id
            )
        
        result_dict = {
            "timestamp" : datetime.now(),
            "question_type" : "multi_image",
            "releve_name" : releve_name,
            "releve_id" : releve_id,
            "observation_id" : observation_id,
            "true_taxon_id" : true_taxon_id,
            "plant_organ" : ";".join(organs),
            "image_files" : ";".join(image_paths),
            "cv_model" : cv_model,
            "taxon_suggestions" : best_matches,
            "full_json" : full_json
            }
        
        return result_dict
    
    def run_batch(self, checkpoints = True, cp_freq = 10, repeat = False):
        '''
        Start batch request.
        
        Parameters
        ----------
        checkpoints : bool, optional
            Set whether to save checkpoints during the batch request.
            The default is True.
        cp_freq : int, optional
            Set frequency (in completed requests) at which checkpoints are
            saved if checkpoints is set to True. The default is 10.
        
        Raises
        ------
        Warning
            DESCRIPTION.
        Exception
            DESCRIPTION.
        
        Returns
        -------
        None.
        '''
        self.t_start = datetime.now()
        
        last_releve = None
        ## Use hidden argument to run alternative list for repeating
        ## requests
        print("Gathering information on pending API requests...")
        with pb(unknown = "brackets", spinner = "classic") as bar:
            request_list = self.to_repeat if repeat else self.pending
        
        print("Starting API requests...")
        with pb(len(request_list), bar = "smooth") as bar:
            for i, current_request in enumerate(request_list):
                releve_name, observation_id, image, p, \
                    cv_model = current_request
                
                ## Extract current releve id based on releve name
                releve_id = self._releve_dict_static[releve_name]
                
                ## Print notification
                if last_releve != releve_name:
                    mssg = "-" * 40 + "\nCurrent releve\nName: {0}\nID: {1}\n"
                    print(mssg.format(releve_name, releve_id))
                    last_releve = releve_name
                
                observation = self._image_meta_static[observation_id]
                
                try:
                    image_files = observation["file_locations"]
                    true_taxon_id = observation["taxon_id"]
                    date = observation["date"]
                    coordinates = (observation["y"], observation["x"])
                    img_types = observation["img_types"]
                
                except:
                    self.errors.append({
                        "releve_name" : releve_name,
                        "releve_id" : releve_id,
                        "obs_id" : observation_id,
                        "error_type" : "Failed to read metadata tag."
                        })
                    
                    mssg = "Failed to read observation information for" + \
                        " observation {0} in releve {1} (releve_id = {2})."
                    
                    raise Warning(
                        mssg.format(observation_id, releve_name, releve_id)
                        )
                    
                    continue
                
                ### Handle warnings (in particular, the iNaturalist
                ### VisionAPI quota limit warning)
                try:
                    mssg = "Current obs.: {0}\nCurrent releve: {1}"
                    print(mssg.format(observation_id, releve_name))
                    
                    if image != "multi":
                        response = self.single_image_request(
                            cv_model = cv_model,
                            image_path = image,
                            coordinates = coordinates,
                            date = date,
                            organ = p,
                            releve_name = releve_name,
                            releve_id = releve_id,
                            observation_id = observation_id,
                            true_taxon_id = true_taxon_id
                            )
                    
                    else:
                        ### Find existing multi-image request for the same
                        ### observation to use the same image combination.
                        ### Else, select new (stratified) random images.
                        try:
                            parent_dict = self \
                                .results[releve_name][observation_id]["multi"]
                            
                            response_0 = parent_dict[list(
                                parent_dict.keys()
                                )[0]]
                            
                            image_selection = response_0["image_files"] \
                                .split(";")
                            organs = response_0["plant_organ"].split(";")
                        
                        except:
                            ### Select 5 images in case more were provided
                            ### To this end, first get the first element for
                            ### each individual plant organ category.
                            indices = [img_types.index(t) for t in set(
                                img_types
                                )]
                            
                            ### Remove the selected images from the list of
                            ### remaining images
                            remaining = list(range(len(image_files)))
                            
                            for i in indices:
                                remaining.remove(i)
                            
                            ### Fill up remaining places with random images
                            if len(remaining) > 0:
                                n_additional = min(
                                    len(remaining), NSAMPLES - len(indices)
                                    )
                                
                                indices += random.sample(
                                    remaining, k = n_additional
                                    )
                            
                            indices.sort()
                            
                            ### Select subset from photo list
                            #### Select random images
                            image_selection = [image_files[i] for i in indices]
                            organs = [img_types[i] for i in indices]
                        
                        response = self.multi_image_request(
                            cv_model = cv_model,
                            image_paths = image_selection,
                            coordinates = coordinates,
                            date = date,
                            organs = organs,
                            releve_name = releve_name,
                            releve_id = releve_id,
                            observation_id = observation_id,
                            true_taxon_id = true_taxon_id
                            )
                    
                    ### Add response dict to results
                    if releve_name not in self.results.keys():
                        self.results[releve_name] = {}
                    
                    if observation_id not in self.results[releve_name].keys():
                        self.results[releve_name][observation_id] = {}
                    
                    if image not in self.results[releve_name][observation_id] \
                        .keys():
                        self.results[releve_name][observation_id][image] = {}
                    
                    if cv_model not in \
                        self.results[releve_name][observation_id][image] \
                            .keys():
                            self.results[releve_name][observation_id][image] \
                                [cv_model] = {}
                    
                    else:
                        mssg = "Response for releve {0}, observation {1}, " + \
                            "image {2}, and CV model {3} already exists an" + \
                                "d will be updated."
                        
                        Warning(mssg.format(
                            releve_name, observation_id, image, cv_model
                            ))
                    
                    ### Update response dict
                    self.results[releve_name][observation_id][image][
                        cv_model].update(response)
                    
                    ### If only testing one CV model, wait for 1 s between
                    ### API requests
                    if len(set(self.single + self.multi)) == 1:
                        time.sleep(1)
                    
                except:
                    self._checkpoint("at_last_exception")
                    
                    mssg = "Stumbled upon warning. Check API quotas."
                    raise Exception(mssg)
                
                self.finished_releves.append(releve_name)
                
                # Save as checkpoint to reduce data loss in case of error
                if checkpoints and i > 0:
                    if cp_freq % i == 0:
                        self._checkpoint()
                
                ### Increase progress bar
                bar()
    
    def path_out(self, name, *subdirs):
        '''
        Generate file location within the selected output directory.

        Parameters
        ----------
        name : str
            Filename.
        *subdirs : str or list of str, optional
            Additional subdirectories inbetween the main output directory and
            the file.

        Returns
        -------
        path : str
            File path.
        '''
        path = os.path.join(self.out_dir, *subdirs, name)
        
        return path
    
    def repeat(self,
               models_single = [],
               models_multi = [],
               releve_names = [],
               observations = [],
               checkpoints = True, cp_freq = 10
               ):
        '''
        Repeat API requests for certain models, releves, or observations.
        
        Parameters
        ----------
        models_single : list of str, optional
            List of models for which single-image API requests shall be
            repeated. The default is [].
        models_multi : list of str, optional
            List of models for which multi-image API requests shall be
            repeated. The default is [].
        releve_names : list of str, optional
            List of releves for which API requests shall be repeated. The
            default is [].
        observations : list of int, optional
            List of observation IDs for which API requests shall be repeated.
            The default is [].
        checkpoints : bool, optional
            Whether to save checkpoints. The default is True.
        cp_freq : int, optional
            Frequency (in API requests) at which checkpoints are saved if
            "checkpoint" is set to True. The default is 10.
        
        Returns
        -------
        None.
        '''
        repeat = []
        
        models_single = self._list_input(models_single)
        models_multi = self._list_input(models_multi)
        
        ## Overwrite model lists if no models are specified (assuming all
        ## requests for the given observations are to be repeated).
        if models_single == models_multi == []:
            models_single = self.single
            models_multi = self.multi
        
        releve_names = self._list_input(releve_names)
        
        ## Overwrite releve names if none are specified (assuming all releves
        ## are to be repeated).
        releve_names = releve_names if releve_names != [] else \
            self.total_releve_names
        
        observations = self._list_input(observations)
        
        releve_ids = [self._releve_dict_static[releve_name] for releve_name \
                      in releve_names]
        
        for observation in self._image_meta_static.values():
            releve_id = observation["releve_id"]
            
            if releve_id in releve_ids or observation["obs_id"] in observations:
                releve_name = self._releve_dict_static_inv[releve_id]
                observation_id = observation["obs_id"]
                image_dict_vals = self._get_image_dict(observation_id).values()
                paths = [x["disc_location"] for x in image_dict_vals]
                parts = [x["organ"] for x in image_dict_vals]
                
                for cv_model, mode, part in zip(
                        models_single * len(paths) + models_multi,
                        [p for p in paths for q in range(
                            len(models_single)
                            )] + ["multi"] * len(models_multi),
                        [p for p in parts for q in range(
                            len(models_single)
                            )] + ["multi"] * len(models_multi)
                        ):
                    
                    p = "multi" if mode == "multi" else part
                    
                    repeat.append([
                        releve_name, observation_id, mode, p, cv_model
                         ])
        
        self.to_repeat = sorted(repeat, key = lambda x: x[0])
        N = len(self.to_repeat)
        
        print(f"Found {N} requests to repeat.")
        
        self.run_batch(checkpoints = checkpoints, cp_freq = cp_freq,
                       repeat = True)
    
    def delete(self,
               releves = [],
               observations = [],
               cv_models = []
               ):
        '''
        Delete entries.
        
        Parameters
        ----------
        releves : list, optional
            List of releve names of releves to delete. The default is None.
        observations : list, optional
            List of observation IDs of observations to delete.
            The default is None.
        cv_models : list, optional
            List of CV models for which results are to delete.
            The default is None.
            
        Returns
        -------
        None.
        '''
        releves = self._list_input(releves)
        observations = self._list_input(observations)
        cv_models = self._list_input(cv_models)
        
        for releve in releves:
            try:
                del self.results[releve]
            except:
                pass
            
            try:
                self.finished_releves.remove(releve)
            except:
                pass
        
        if len(observations) > 0:
            if any(isinstance(v, str) for v in observations):
                print("Warning: Observation keys should be of type int.")
            
            for releve_name, releve in zip(list(self.results.keys()),
                                        list(self.results.values())):
                keys = releve.keys()
                
                for key in list(keys):
                    if key in observations:
                        del self.results[releve_name][key]
        
        if len(cv_models) > 0:
            for releve_name in list(self.results.keys()):
                for observation_id in list(self.results[releve_name].keys()):
                    for image in list(self.results[releve_name][
                                      observation_id].keys()):
                        for cv_model in list(
                                self.results[releve_name][observation_id][
                                    image].keys()):
                            if cv_model in cv_models:
                                del self.results[releve_name][observation_id][
                                    image][cv_model]
    
    def _standard_task(self, image_path, coordinates, date, organs, cv_model,
                      return_n = NTOP, batch = None, req_id = None):
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
        req_id : int, optional
            Add a taxon ID for which probabilities should be returned
            regardless whether it is amongst the top 5 suggestions. Note: Since
            data originates from the Info Flora online fieldbook, Info Flora
            IDs are entered here. They will be translated to FlorID IDs for
            FlorID requests.
        
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
            response = florid.post_image(image_path, coordinates, date,
                                         true_id = req_id
                                         )
            
            ids = florid.species_ranking(response, n = return_n)
        
        else:
            floraincognita.post_image(image_path, batch)
            response = []
            ids = []
        
        return [cv_model, ids, response]
    
    def _insert_manual(self, source = "floraincognita", **kwargs):
        '''
        Insert results from manually generated Flora Incognita results .json
        or input prompt into a previously generated Batchrequest object.
        
        Parameters
        ----------
        source : str {"floraincognita" or "prompt"}, optional
            Data source. The default is "floraincognita".
        
        **kwargs : dict
            Additional arguments required to locate and edit a result.
        
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
        if source == "floraincognita":
            if len(self.results) > 0:
                insert_florinc(self)
            
            else:
                raise Exception(
                    "Batchrequest object contains no editable results."
                    )
        else:
            if all(arg in kwargs for arg in [
                    "releve_name", "obs_id", "image", "cv_model"
                    ]):
                releve_name = kwargs["releve_name"]
                obs_id = kwargs["obs_id"]
                image = kwargs["image"]
                cv_model = kwargs["cv_model"]
                
                if "new_response" in kwargs:
                    updates = {"taxon_suggestions" : kwargs["new_response"]}
                
                elif "new_true_id" in kwargs:
                    updates = {"true_taxon_id" : kwargs["new_true_id"]}
                
                else:
                    raise Exception(
                        "Missing arguments. Provide either 'new_response'" + \
                            " or 'new_true_id' to change an entry."
                            )
                try:
                    self.results[releve_name][int(obs_id)][image][cv_model] \
                        .update(updates)
                
                except KeyError:
                    image = image.replace("\\", "/")
                    self.results[releve_name][int(obs_id)][image][cv_model] \
                        .update(updates)
            else:
                raise Exception("Missing arguments. Entry cannot be located.")
    
    def _update_fixed_taxon_ids(self):
        self.update_image_dicts()
        
        mssg = "Replacing previous taxon id {0} by new taxon id {1}."
        N = 0
        for k0 in self.results.keys():
            for k1 in self.results[k0].keys():
                metadata = self._image_meta[k1]
                taxon_id = metadata["taxon_id"]
                
                for k2 in self.results[k0][k1].keys():
                    for k3 in self.results[k0][k1][k2].keys():
                        old_id = self.results[k0][k1][k2][k3]["true_taxon_id"]
                        if old_id != taxon_id:
                            print(mssg.format(old_id, taxon_id))
                            self.results[k0][k1][k2][k3][
                                "true_taxon_id"
                                ] = taxon_id
                            
                            N += 1
        print(f"Replaced true taxon IDs in {N} responses.")
    
    def _update_fixed_plant_organs(self):
        self.update_image_dicts()
        
        N = 0
        res_k = list(self.results.keys())
        for k0 in res_k:
            old_k0_k = list(self.results[k0].keys())
            
            for k1 in old_k0_k:
                image_dict_vals = self._get_image_dict(k1).values()
                paths = [x["disc_location"] for x in image_dict_vals]
                p_sansext = [x.rsplit("_", 1)[0] for x in paths]
                parts = [x["organ"] for x in image_dict_vals]
                
                old_k1_k = list(self.results[k0][k1].keys())
                
                for old_img_dir in old_k1_k:
                    old_sansext = os.path.splitext(
                        str(old_img_dir)
                        )[0].rsplit("_", 1)[0]
                    
                    first_key = list(
                        self.results[k0][k1][old_img_dir].keys()
                        )[0]
                    
                    old_parts = self.results[k0][k1][old_img_dir][first_key][
                        "plant_organ"
                        ]
                    
                    if not (old_sansext in p_sansext):
                        continue
                    
                    elif not old_parts == parts[p_sansext.index(old_sansext)]:
                        d = {a : (b, c) for a, b, c in zip(
                            p_sansext, paths, parts
                            )}
                        
                        (new_img_dir, plnt_org) = d[old_sansext]
                        
                        self.results[k0][k1][new_img_dir] = self \
                            .results[k0][k1][old_img_dir]
                        
                        for cvm in self.results[k0][k1][new_img_dir].keys():
                            self.results[k0][k1][new_img_dir][cvm][
                                "image_files"
                                ] = new_img_dir
                            
                            self.results[k0][k1][new_img_dir][cvm][
                                "plant_organ"
                                ] = plnt_org
                        
                        del self.results[k0][k1][old_img_dir]
                        
                        if "multi" in self.results[k0][k1].keys():
                            for cvm in self.results[k0][k1]["multi"].keys():
                                results = self.results[k0][k1]["multi"][cvm]
                                
                                mult_imgs = results["image_files"]
                                mult_parts = results["plant_organ"]
                                
                                pattern = fr"{old_sansext}_(\w+).jpg"
                                replacement = new_img_dir
                                imgf = re.sub(pattern, replacement, mult_imgs)
                                
                                self.results[k0][k1]["multi"][cvm][
                                    "image_files"
                                    ] = imgf
                                
                                mult_list = imgf.split(";")
                                
                                if replacement in mult_list:
                                    loc = mult_list.index(replacement)
                                
                                    parts_list = mult_parts.split(";")
                                    parts_list[loc] = plnt_org
                                    
                                    self.results[k0][k1]["multi"][cvm][
                                        "plant_organ"
                                        ] = ";".join(parts_list)
                        
                        print(f"Changed {old_img_dir} to {new_img_dir}.")
                        N += 1
        
        print(f"Changed file locations and plant organ keys for {N} results.")
        
        return
    
    def _cleanup_duplicates(self):
        '''
        Try to replace duplicate dictionary keys whith "duplicate" meaning keys
        that refer to the same image but with different paths (either foreward
        slashes or double backslash).
        
        Notes
        -----
        This function is "stupid" as it will update the first occurrence
        dictionary values with the second one without doing more sophisticated
        checks. (E.g., it does not check whether the respective dictionary
        entries have a date that could be used to replace the earlier entry
        with the later one. Such things don't happen here, which has to be
        kept in mind.)
        
        Returns
        -------
        None.
        '''
        mssg = "Found duplicated key:\n{0}\n{1}\nKeep: {1}."
        N = 0
        M = 0
        for k0 in self.results.keys():
            for k1 in self.results[k0].keys():
                image_keys = list(self.results[k0][k1].keys())
                image_keys_norm = [k.replace("\\", "/") for k in image_keys]
                
                # Resolve duplicate key issues
                duplicates = []
                if len(set(image_keys)) > len(set(image_keys_norm)):
                    for e in image_keys_norm:
                        dup = [
                            i for i, x in enumerate(image_keys_norm) if x == e
                            ]
                        
                        if len(dup) > 1:
                            if dup not in duplicates:
                                duplicates.append(dup)
                
                for d in duplicates:
                    first = image_keys[d[0]]
                    second = image_keys[d[1]]
                    
                    second_result = self.results[k0][k1][second]
                    
                    print(mssg.format(first, second))
                    self.results[k0][k1][first].update(second_result)
                    del self.results[k0][k1][second]
                    N += 1
                
                # Rename dictionary keys
                image_keys_updated = list(self.results[k0][k1].keys())
                
                for k in image_keys_updated:
                    if "\\" in k:
                        k_n = k.replace("\\", "/")
                        self.results[k0][k1][k_n] = self.results[k0][k1].pop(k)
                        M += 1
        print(
            f"Resolved {N} duplicate dictionary entries.\n" +
            f"Normalized {M} dictionary keys."
            )
    
    def _get_image_dict(self, observation_id):
        '''
        Output dictionary containing image names, disc locations, and depicted
        plant parts (idicated by single-letter-encoding).
        
        Parameters
        ----------
        observation_id : int
            Observation ID of the observation, for which the dictionary shall
            be generated.
        
        Returns
        -------
        out_dict : dict
            Output dictionary containing the image names as keys and nested
            dictionaries containing disc location (key "disc_location") as well
            as depicted plant part (key "organ") for each image.
        '''
        image_files = self._image_meta[observation_id]["file_locations"]
        image_files = [# Added this to ensure that the image files are found in the correct directory after moving around files.
            os.path.join(
                self.image_dir,
                os.path.basename(os.path.dirname(os.path.dirname(imf))),
                os.path.basename(os.path.dirname(imf)),
                os.path.basename(imf)
                ) for imf in image_files
            ]
        image_names = [
            os.path.splitext(
                os.path.split(p.replace("\\", "/"))[-1]
                )[0] for p in image_files
            ]
        
        image_types = self._image_meta[observation_id]["img_types"]
        
        details = [{"disc_location" : p, "organ" : o} for p, o in \
                   zip(image_files, image_types)]
        
        out_dict = {
            key : value for key, value in zip(image_names, details)
            }
        
        return out_dict
    
    def _list_input(self, value):
        '''
        Check input and ensure it is a list.
        
        Parameters
        ----------
        value : any
            Input value.
            
        Returns
        -------
        list
        '''
        value = [] if value is None else value
        value = value.tolist() if isinstance(value, pd.Series) else value
        value = value if isinstance(value, list) else [value]
        
        return value
    
    def _checkpoint(self, name = "cpt.save"):
        '''
        Create checkpoint of current instance.
        
        Returns
        -------
        None.
        '''
        with open(self.path_out(name, "log"), "wb") as f:
            pk.dump(self, f)
        
        print("Checkpoint saved.")
    
    def save(self):
        '''
        Save current instance.
        
        Returns
        -------
        None.
        '''
        with open(self.path_out(self.name, "log"), "wb") as f:
            pk.dump(self, f)
        
        print("Output saved at {0}.".format(
            str(self.path_out(self.name, "log"))
            )
            )
    
    def to_df(self):
        '''
        Return the results as a pandas.DataFrame.
        
        Returns
        -------
        out : pandas.DataFrame
            Dataframe containing the API responses.
        '''
        results_list = []
        
        for releve in self.results.values():
            for observation in releve.values():
                for image in observation.values():
                    results_list += [result for result in image.values()]
        
        df = pd.DataFrame(results_list)
        
        colnames = ["first", "second", "third", "forth", "fifth"]
        taxa = pd.DataFrame(df["taxon_suggestions"].to_list(),
                            columns = colnames)
        
        main = df[list(df.columns[:df.columns.get_loc("taxon_suggestions")])]
        
        out = pd.concat([main, taxa], axis = 1)
        
        return out
    
    def load_checkpoint(self, file = None, from_error = "auto"):
        '''
        Load pickled checkpoint of the last Batchrequest instance that has been
        running.
        
        Parameters
        ----------
        from_error : str/bool
            Restart from last error. (Alternative: Restart from last finished
            observation.) Default: "assert"; i.e., use the most recent
            checkpoint irrespective of checkpoint type.
        
        Returns
        -------
        br_cpt : Batchrequest
            Instance of type Batchrequest.
        
        Note
        ----
        Consider that you probably want to exclude previously finished releves
        from the releve_name_list when running a batch request using a
        checkpoint.
        '''
        if file is not None:
            name = file
        
        else:
            if isinstance(from_error, bool):
                name = "at_last_exception" if from_error else "cpt.save"
            
            else:
                cpt_names = os.listdir(self.path_out("log"))
                cpt_dirs = [self.path_out(n, "log") for n in cpt_names]
                
                name = os.path.split(max(cpt_dirs, key = os.path.getmtime))[1]
        
        current_out_dir = self.out_dir
        
        with open(self.path_out(name, "log"), "rb") as f:
            br_cpt = pk.load(f)
        
        if int(br_cpt.version[0]) == 2:
            self.__dict__.update(br_cpt.__dict__)
            self.out_dir = current_out_dir
        
        else:
            mssg = "Incompatible Batchrequest version {0} of loaded file."
            
            raise Exception(mssg.format(br_cpt.version))

#-----------------------------------------------------------------------------|
# Run request
if __name__ == "__main__":
    BR = Batchrequest()
    
    if REPEAT != []:
        print(f"Loading BR file {LOADFILE}.")
        BR.load_checkpoint(file = LOADFILE)
        BR._cleanup_duplicates()
        
        # For old BR file versions: Get releve names
        if BR.total_releve_names == []:
            BR.total_releve_names = list(BR.results.keys())
        
        print(f"Repeating requests for the following API(s): {REPEAT}.")
        REPEATMULTI = [r for r in REPEAT if r in MULTIIMG]
        
        if UPDATEFIXED:
            BR.update_image_dicts()
            BR._update_fixed_taxon_ids()
            BR._update_fixed_plant_organs()
        
        BR.repeat(models_single = REPEAT,
                  models_multi = REPEATMULTI
                  )
    
    elif FROMCPT:
        BR.load_checkpoint()
        ## Changes in image META are only recognised after updating! (Else, BR
        ## uses ._image_meta_static to update .pending.) Since the script might
        ## have stopped encountering an error in the image data set, it is
        ## advisable to update here. (Of course, issues with the image data
        ## need to be resolved first.)
        BR.update_image_dicts()
        
        if UPDATEFIXED:
            print("Updating fixed taxon IDs and plant parts.")
            BR._update_fixed_taxon_ids()
            BR._update_fixed_plant_organs()
        
        else:
            BR.run_batch()
    
    elif FLORINC is not None:
        BR.load_checkpoint(file = FLORINC)
        
        if UPDATEFIXED:
            BR._update_fixed_taxon_ids()
            BR._update_fixed_plant_organs()
        
        BR._insert_manual()
    
    elif MANUALUPDATE is not None:
        [BRFILE, RNME, OID, IMG, CVM, UPWHAT] = MANUALUPDATE
        BR.load_checkpoint(file = BRFILE)
        
        if UPDATEFIXED:
            BR._update_fixed_taxon_ids()
            BR._update_fixed_plant_organs()
        
        what, value = UPWHAT.split("=")
        if what == "new_true_id":
            print(f"New true ID: {value}")
            BR._insert_manual(
                source = "prompt",
                releve_name = RNME,
                obs_id = OID,
                image = IMG,
                cv_model = CVM,
                new_true_id = value
                )
        elif what == "new_response":
            print("New value:")
            print(value.split(";"))
            
            BR._insert_manual(
                source = "prompt",
                releve_name = RNME,
                obs_id = OID,
                image = IMG,
                cv_model = CVM,
                new_response = value.split(";")
                )
        else:
            raise Exception("Invalid input parameter.")
    
    elif UPDATEFIXED and (LOADFILE is not None):
        print("Try fix only\nUpdating fixed taxon IDs and plant parts.")
        BR.load_checkpoint(file = LOADFILE)
        BR._update_fixed_taxon_ids()
        BR._update_fixed_plant_organs()
    
    else:
        BR.add_releves(releve_name_list = RELEVENAMES)
        BR.run_batch()
    
    BR.save()
    
    # Export data as Excel sheet
    df = BR.to_df()
    
    ## Add species names (using the Info Flora taxonomic backbone)
    SD = base.SpeciesDecoder("comeco_local")
    
    df["true_taxon_name"] = [SD.decode(tid) for tid in df["true_taxon_id"]]
    
    ## Drop duplicates from dataframe
    df = df.drop_duplicates(
        subset = [
            "releve_name", "observation_id", "true_taxon_id", "plant_organ",
            "image_files", "cv_model"
                ], keep = "last"
        )
    
    ## Save to Excel file
    if os.path.isfile(BR.path_out("Responses.xlsx")):
        with pd.ExcelWriter(BR.path_out("Responses.xlsx"), mode = "a",
                            if_sheet_exists = "replace") as writer:
            df.to_excel(writer, sheet_name = BR.name, index = False)
        print(
            "Wrote sheet to Excel table " + BR.path_out("Responses.xlsx") + "."
            )
    
    else:
        df.to_excel(BR.path_out("Responses.xlsx"), sheet_name = BR.name,
                    index = False)
        print("Created Excel table at " + BR.path_out("Responses.xlsx") + ".")
    
    # Shutdown system if shutdown flag was set
    if args.shutdown:
        cmd = "shutdown /s /t 1" if platform.system() == "Windows" \
            else "systemctl poweroff"
        
        os.system(cmd)