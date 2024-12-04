#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 10:30:37 2023

Match taxon names using the Swiss taxonomic backbone for vascular plants.
"""
__author__ = "Manuel"
__date__ = "Wed Aug 16 10:30:37 2023"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Production"

#-----------------------------------------------------------------------------|
# Imports
import os, time, easygui, subprocess, argparse
import pandas as pd
import pickle as pk
import pykew.powo as powo
from datetime import datetime
from pykew.powo_terms import Name as NamePOWO
from alive_progress import alive_bar as pb

#-----------------------------------------------------------------------------|
# Arguments and settings
def parseArguments():
    parser = argparse.ArgumentParser()
    
    # Use as: py taxonomy.py -addsyn "Taxon name" "Synonym name"
    parser.add_argument("-addsyn", "--add_synonym",
                        help = "Add a synonym to the data base.",
                        type = str, nargs = 2, default = False)
    
    args = parser.parse_args()
    
    return args

args = parseArguments()

ADDSYNONYM = args.add_synonym

#-----------------------------------------------------------------------------|
# Settings
dir_py = os.path.dirname(os.getcwd())# for debugging in IDE
dir_py = os.path.dirname(os.path.dirname(__file__))
dir_main = os.path.dirname(dir_py)

INFOFLORATAXBB = "Checklist_2017_simple_version_20230503.xlsx"
TAXBB = os.path.join(dir_main, "dat", INFOFLORATAXBB)
SYNDBFILE = os.path.join(dir_main, "dat", "Synonyms.db")
RESPONSES = os.path.join(dir_main, "out", "Responses.xlsx")
OUTPUT = os.path.join(dir_main, "out", "Final.xlsx")

taxonomy_bb = pd.read_excel(TAXBB, sheet_name = "Checklist 2017",
                            skiprows = 5, header = 0)

taxonomy_bb.columns = [
    "ISFS", "taxon_id", "rank", "taxon_name", "family", "indigenous",
    "boundary", "within_taxon_name", "within_ISFS", "within_taxon_id"
    ]

taxonomy_bb["toplevel"] = taxonomy_bb.apply(
    lambda row: pd.isnull(row["within_taxon_id"]),
    axis = 1
    )

taxonomy_bb["within_taxon_name"] = taxonomy_bb.apply(
    lambda row: row["taxon_name"] if pd.isnull(row["within_taxon_name"]) else
    row["within_taxon_name"],
    axis = 1
    )

WFOMATCH = "https://list.worldfloraonline.org/matching_rest.php?input_string="
WFOGET = "https://list.worldfloraonline.org/"

#-----------------------------------------------------------------------------|
# Classes
class SubtaxonIterator():
    def __init__(self, taxon, backbone):
        '''
        Initiate the iterator.
        
        Parameters
        ----------
        taxon : str
            Taxon name (must be included in the Swiss taxonomic database).
        backbone : pd.DataFrame
            Taxonomic database. Must contain the columns "taxon_name", and
            "within_taxon_name".
        
        Returns
        -------
        None.
        '''
        self.taxon = taxon
        self.backbone = backbone
        self.list = [taxon]
        self.subtaxa = []
    
    def __iter__(self):
        '''
        Return the next item.
        
        Raises
        ------
        Exception
            Error if there are no items left in the subtaxa list.
        
        Returns
        -------
        item : str
            Subtaxon name.
        '''
        try:
            item = self.list.pop(0)
            
            subtaxa = self.backbone[
                self.backbone["within_taxon_name"] == item
                ]["taxon_name"].to_list()
            
            subtaxa = [s for s in subtaxa if s != item]
            
            self.list.extend(subtaxa)
            
            return subtaxa
        
        except:
            raise Exception("Nothing to iterate over.")
    
    def get(self):
        '''
        Return a list of all lower level taxa.
        
        Returns
        -------
        list
            Subtaxon names.
        '''
        while True:
            try:
                self.subtaxa.extend(self.__iter__())
            
            except:
                break
        
        return self.subtaxa

class TaxonomyTree():
    def __init__(self, backbone):
        '''
        Create a taxonomy tree.
        
        Parameters
        ----------
        backbone : pd.DataFrame
            Taxonomic database. Must contain the columns "taxon_name",
            "within_taxon_name", and "toplevel".
        
        Returns
        -------
        None.
        '''
        self.backbone = backbone
        self.backbone["lvl"] = self.backbone.apply(
            lambda row: 0 if row["rank"] in ["sp", "hybrid"] else 1 if \
                row["rank"] in "aggr" else 2 if row["rank"] == "superaggr" \
                    else -1,
            axis = 1
            )
    
    def parent(self, taxon):
        parent = self.backbone[self.backbone["taxon_name"] == taxon][
            "within_taxon_name"
            ].to_list()
        
        return parent[0] if len(parent) > 0 else None
    
    def children(self, taxon):
        rows = self.backbone[self.backbone["within_taxon_name"] == taxon]
        
        children = [c["taxon_name"] for i, c in rows.iterrows()] if \
            len(rows) > 0 else None
        
        return children

class SynonymDatabase():
    def __init__(self):
        self.instanciated = datetime.now()
        self.database = {}
    
    def add_taxon(self, name):
        '''
        Add a taxon to the data base and search for synonyms.
        
        Parameters
        ----------
        name : str
            Taxon name.
        
        Returns
        -------
        None.
        '''
        original_query_name = name
        query = self._create_query(name)
        
        if query is None:
            
            return
        
        failed_attempts = 0
        
        while True:
            try:
                print("Sending API request for {0}".format(name))
                powo_results = powo.search(query)
                
                accepted_taxa = []
                
                for r in powo_results:
                    if r["accepted"]:
                        accepted_taxa.append((r["name"], r["fqId"]))
                
                break
            
            except:
                print("Request failed.")
                failed_attempts += 1
                
                if failed_attempts > 5:
                    
                    print("Failed five consecutive times. Skipped taxon.")
                    
                    return
                
                elif failed_attempts > 2:
                    mssg = "What the heck is {0} supposed to mean? " + \
                        "Please enter some valid name manually: "
                    
                    try:
                        if failed_attempts > 3:
                            ### Skip this and evoke user inut promt right away
                            ### by raising an error
                            raise Exception("Too many tries.")
                        
                        cmd = " ".join(["Rscript",
                             os.path.join(dir_main, "rsc", "wfo.R"),
                             "'" + name + "'"])
                        
                        res = subprocess.run(cmd, capture_output = True,
                                             text = True
                                             )
                        
                        if len(res.stdout) == 12:#i.e., out = [1] "NA NA"\n
                            
                            raise Exception("WFO: Failed to match taxon name.")
                        
                        name = res.stdout.strip("[1] ").strip().strip("'") \
                            .strip('"')
                    
                    except:
                        name = easygui.enterbox(mssg.format(name))
                        failed_attempts = 0
                    
                    if name is None:
                        return
                    
                    else:
                        query = self._create_query(name)
                
                elif failed_attempts == 1:
                    query = self._create_query(name, level = 1)
                
                else:
                    time.sleep(1)
        
        try:
            accepted_taxon = accepted_taxa[0]
            
            find_synonyms = True
        
        except:
            ## If it didn't work, just skip this one. Missing entries will
            ## be manually added if required later on in the analyses.
            find_synonyms = False
            synonyms = []
        
        failed_attempts = 0
        
        while find_synonyms:
            try:
                mssg = "Sending request for accepted taxon {0}."
                print(mssg.format(" ".join(accepted_taxon)))
                
                response = powo.lookup(accepted_taxon[1])
                
                if "synonyms" in response.keys():
                    synonyms = response["synonyms"]
                    synonyms = [s["name"] + " " + s["author"] for s in
                         synonyms if \
                             s["taxonomicStatus"] == "Homotypic_Synonym"]
                    
                    '''
                    # Dropping the endings creates too many false matches.
                    # Only iNaturalist is not using author names and
                    # iNaturalist uses the POWO database, so the accepted
                    # taxon name without author should be the name iNaturalist
                    # associates with the taxon.
                    without_author = [
                        " ".join(s.split(" ")[:2]) for s in synonyms
                        ]
                    
                    synonyms.extend(without_author)
                    '''
                
                else:
                    synonyms = []
                
                try:
                    accepted_names = [
                        " ".join([response["name"], response["authors"]]),
                        " ".join(# Just to make sure subspecies are also covd.
                            response["name"].split(" ")[:-1] +
                            [response["authors"] + " subsp."] +
                            response["name"].split(" ")[-1:]
                            ),
                        accepted_taxon[0]
                        ]
                
                except:
                    accepted_names = [accepted_taxon[0]]
                
                synonyms.extend(accepted_names)
                
                break
            
            except:
                n_tries = 5
                failed_attempts += 1
                
                if failed_attempts > n_tries:
                    mssg = "API request failed {0} consecutive times. " + \
                        "Species will be dropped."
                    
                    print(mssg.format(n_tries))
                    
                    synonyms = []
                    break
                
                print("Request failed.")
                failed_attempts += 1
                time.sleep(0.5)
        
        ## Make sure current query name and original query name are allwed as
        ## synonyms
        synonyms.extend([name, " ".join(
            name.split(" ")[:2]
            )])
        
        synonyms.extend([original_query_name, " ".join(
            original_query_name.split(" ")[:2]
            )])
        
        self.database[original_query_name] = {"synonyms" : list(set(synonyms))
            }
    
    def remove_taxon(self, name):
        '''
        Removes a taxon from the data base.
        
        Parameters
        ----------
        name : str
            Taxon name.
        
        Returns
        -------
        None.
        '''
        try:
            del self.database[name]
        
        except:
            print("Taxon not found in database.")
    
    def add_synonyms(self, taxon, synonyms):
        '''
        Adds a synonym or a list of synonyms to an existing data base entry.
        If no matching entry exists, it will be created.
        
        Parameters
        ----------
        taxon : str
            Taxon name.
        synonyms : str or list of str
            Synonyms to the taxon name.
        
        Returns
        -------
        None.
        '''
        if taxon in self.database.keys():
            if isinstance(synonyms, list):
                self.database[taxon]["synonyms"].extend(synonyms)
            
            else:
                self.database[taxon]["synonyms"].append(synonyms)
        else:
            if isinstance(synonyms, list):
                self.database[taxon] = {"synonyms" : synonyms}
            
            else:
                self.database[taxon] = {"synonyms" : [synonyms]}
    
    def add_list(self, taxon_list):
        '''
        Wrapper to add a list of taxa.
        
        Parameters
        ----------
        taxon_list : list
            List of taxon names.
        
        Returns
        -------
        None.
        '''
        taxon_list = list(set(taxon_list))
        taxon_list.sort()
        
        with pb(len(taxon_list), bar = "smooth") as bar:
            for taxon in taxon_list:
                if taxon not in self.database.keys():
                    self.add_taxon(taxon)
                
                bar()
                time.sleep(0.5)
        
    def get_sublevel_taxa(self, name, backbone = taxonomy_bb):
        '''
        Search taxonomy backbone for all lower taxa.
        
        Parameters
        ----------
        name : str
            Taxon name.
        backbone : pandas.DataFrame, optional
            Taxonomy backbone. The default is taxonomy_bb.
        
        Returns
        -------
        SubtaxonIterator
            Subtaxon iterator object.
        '''
        iterator = SubtaxonIterator(name, backbone)
        
        return iterator.get()
    
    def is_synonym(self, taxon, true_taxon):
        '''
        Check whether a taxon is a synonym of true_taxon.
        
        Parameters
        ----------
        taxon : str
            Taxon name.
        true_taxon : str
            Taxon to match with.
        
        Returns
        -------
        bool
            Match or no match.
        '''
        if taxon is None or true_taxon is None:
            return False
        
        else:
            return taxon in self.database[true_taxon]["synonyms"]
    
    def is_lower(self, taxon, true_taxon):
        sublevel_synonyms = self.get_sublevel_taxa(true_taxon)
        
        return taxon in sublevel_synonyms
    
    def _create_query(self, name, level = 0):
        name = name.replace("nothosubsp", "subsp")# Some issue with Pulsatilla alpina. Not in the data set. Simply replaced to avoid issues.
        
        if "agg." in name:
            print("Cannot query for aggregates.")
            
            return None
        
        parts = name.split(" ")
        genus, epithet, remainder = parts[0], parts[1], parts[2:]
        
        query = {NamePOWO.genus : genus,
                 NamePOWO.species : epithet
            }
        
        remainder = " ".join(remainder)
        
        if remainder.startswith("subsp."):
            remainder = remainder.strip("subsp. ")
            parts = remainder.split(" ")
            subspecies, remainder = parts[0], " ".join(parts[1:])
            add = " subsp. " + subspecies
        
        elif remainder.startswith("var."):
            remainder = remainder.strip("var. ")
            parts = remainder.split(" ")
            var, remainder = parts[0], " ".join(parts[1:])
            add = " var. " + var
        
        elif "subsp." in remainder:
            parts = remainder.split(" subsp. ")
            species_author = parts[0]
            subspecies = parts[1].split(" ")[0]
            add = " subsp. " + subspecies
        
        elif "var." in remainder:
            parts = remainder.split(" var. ")
            var_author = parts[0]
            var = parts[1].split(" ")[0]
            add = " var. " + var
        
        else:
            author = " ".join(remainder)
            subspecies = var = add = ""
            
            if author != "":
                query.update({NamePOWO.author : author})
        
        match level:
            case 0:
                if add == "":
                    query = query
                
                else:
                    query = " ".join([genus, epithet]) + add
            
            case 1:
                query = " ".join([genus, epithet.strip("×")]) + add
            
            case 2:
                query = " ".join([genus, epithet.strip("×")])
            
            case _:
                query = query
        
        return query
    
    def save(self, path):
        '''
        Save current instance.
        
        Returns
        -------
        None.
        '''
        with open(path, "wb") as f:
            pk.dump(self, f)
        
        print("Output saved at {0}.".format(path))

#-----------------------------------------------------------------------------|
# Main class
class Matcher():
    def __init__(self, backbone, synonym_db = "create_new"):
        self.Tree = TaxonomyTree(backbone)
        
        if synonym_db == "create_new":
            self.Synonyms = SynonymDatabase()
            self.Synonyms.add_list(backbone["taxon_name"].to_list())
        
        else:
            with open(synonym_db, "rb") as f:
                self.Synonyms = pk.load(f)
    
    def match(self, taxon, true_taxon):
        #print(f"Matching {taxon} and true taxon {true_taxon}.")
        ## Replace potentially "wrong" abbreviations
        taxon = taxon.replace("agg.", "aggr.")
        
        ## Check whether the input taxons are equal or synonyms
        if self.Synonyms.is_synonym(taxon, true_taxon):
            matching_lvl = 0
        
        ## Check whether first input taxon is a (sub)child of the true taxon
        elif self.Synonyms.is_lower(taxon, true_taxon):
            children = self.Tree.children(true_taxon)
            
            ### Set matching level to sub-child
            matching_lvl = -2
            
            ### Replace matching level if taxon matches a direct child
            for child in children:
                if self.Synonyms.is_synonym(taxon, child):
                    matching_lvl = -1
                    break
        ## Check whether first input taxon matches a parent taxon
        else:
            parent = self.Tree.parent(true_taxon)
            
            if self.Synonyms.is_synonym(taxon, parent):
                matching_lvl = 1
            
            else:
                matching_lvl = 10 if \
                    taxon.split(" ")[0] == true_taxon.split(" ")[0] else None
        
        return matching_lvl

#-----------------------------------------------------------------------------|
# Match taxa
if ADDSYNONYM:
    print("Adding synonym {0} for taxon {1}.".format(
        ADDSYNONYM[1], ADDSYNONYM[0])
        )
    
    with open(SYNDBFILE, "rb") as f:
        Synonyms = pk.load(f)

    Synonyms.add_synonyms(ADDSYNONYM[0], ADDSYNONYM[1])
    Synonyms.save(SYNDBFILE)

else:
    print("Updating synonyms and adding to API responses...")
    
    if not os.path.isfile(SYNDBFILE):
        ## Initial run (create new synonym database)
        M = Matcher(taxonomy_bb)
        M.Synonyms.save(SYNDBFILE)
    
    else:
        ## Any subsequent run (load pre-existing synonym database)
        M = Matcher(taxonomy_bb, synonym_db = SYNDBFILE)
    
    ### Some names have been abbreviated. Here, I simply add the same synonyms
    ### for the abbreviated name, since those names are on subspecies level
    ### already and hardly confused when truncated after 47 letters.
    key_list = list(M.Synonyms.database.keys())
    
    for key in key_list:
        if len(key) > 47:
            M.Synonyms.database[key[:47] + "..."] = M.Synonyms.database[key]
    
    sheets_dict = pd.read_excel(RESPONSES, sheet_name = None, index_col = None)
    print("Found Excel file sheets: {}".format(sheets_dict.keys()))
    
    df = pd.concat(sheets_dict.values())
    
    for rank in ["first", "second", "third", "forth", "fifth"]:
        try:
            df["match_" + rank] = [M.match(
                taxon, true_taxon
                ) for taxon, true_taxon in zip(
                    map(str, df[rank].values),
                    map(str, df["true_taxon_name"].values)
                    )]
        
        except KeyError as e:
            lines = df[df["true_taxon_name"] == e.args[0]]
            mssg = f"Error in {lines}. Cannot match taxon."
            raise KeyError(mssg)
    
    df.to_excel(OUTPUT, index = False, header = True, na_rep = 100)

print("Finished.")
#time.sleep(1)
