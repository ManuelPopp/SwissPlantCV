# SwissPlantCV
Testing state-of-the-art vascular plant species identification computer vision models for Swiss vascular plants.

## Dependencies
Script files within this repo are separated by programming language (Python and R) and stage of the project.
Python scripts are stored in subdirectories of [./py3](https://github.com/ManuelPopp/SwissPlantCV/tree/main/py3), whereby each subdirectory accompanies a `requirements.txt` file to facilitate installation of required modules. The parent directory contains such a `requirements.txt` combining all required modules. Note that modules for geospatial analyses are included. These may require correct set-up of [GDAL](https://gdal.org/en/stable/), which cannot be done through a Python package manager like pip. Some modules were only used to facilitate manual data cleaning or to plan fieldwork. It is therefore recommended to only install modules for the required task (i.e., the modules listed in the respective subdirectory).
R scripts were used for analysis of the final data and plotting. The main R script is [./rsc/Data_analysis.R](https://github.com/ManuelPopp/SwissPlantCV/blob/main/rsc/Data_analysis.R), which is set up to install missing requirements automatically.

## Repository organisation
This repository comprises various subdirectories
```
📂 SwissPlantCV/
├── 📂 bat/
│   └── ... (Various files used to run scripts with pre-defined input parameters.)
├── 📂 dat/
│   ├── 📂 BioGeoRegionen/
│   │   ├── 📂 BiogeographischeRegionen/
│   │   │   └── N2020_Revision_BiogeoRegion.* (Shapefile of biogeographical regions of Switzerland.)
│   │   └── README.txt (Information on the shapefile within the subdirectory.)
│   ├── GBIF_obs_per_year.csv (Number of GBIF records per year, obtained via GBIF API.)
│   ├── growth_form_info.csv (Information on growth form for aquatic and woody taxa. Manually checked.)
│   ├── Habitats.xlsx (TypoCH habitat types, manually compiled following Delarze et al., 2015; see manuscript.)
│   ├── Synonyms.db (Database to translate between taxonomic backbones.
│   │                Pickled instance of class SynonymDatabase (py3/analyses/taxonomy.py),
│   │                compiled via WFO API and manual resolving.)
│   └── Taxonomic_backbone_wHier_2022.csv (Taxonomix backbone for Swiss flora.)
├── 📂 out/
│   └── Final.xlsx (Excel sheet summarising all API responses.)
├── 📂 py3/
│   ├── 📂 analyses/
│   │   ├── Check_misclassifications.py (Tkinter graphical interface to check wrong IDs manually.)
│   │   ├── locationprecision.py (Was used to obtain stats on location precision for sampling points.)
│   │   ├── taxonomy.py (Provides SynonymDatabase class to build taxonomy database.
│   │   └── requirements.txt (Python modules used during this step.)
│   ├── 📂 misc/
│   ├── 📂 requests/
│   │   ├── authentication.py (Load encrypted user credentials for some APIs.)
│   │   ├── base.py (Basic functions for coordinate conversion, EXIF handling, file encyption, etc.)
│   │   ├── batchrequest_v201.py (Provides BatchRequest class to send API requests and store responses.)
│   │   ├── <identification provider>.py (Functions to handle the request formats for the different APIs.)
│   │   └── requirements.txt (Python modules used during this step.)
│   ├── 📂 sampling/
│   │   ├── <scriptname>.py (Scripts to facilitate fieldwork, e.g., to visualise sampled habitat types.)
│   │   └── requirements.txt (Python modules used during this step.)
│   ├── 📂 tk_Search_Releves/
│   │   ├── Releve_species_lists.py (Tkinter graphical interface to check InfoFlora Fieldbook export for potential sampling locations.)
│   │   └── requirements.txt (Python modules used during this step.)
│   └── requirements.txt (All additional Python modules used.)
├── 📂 rsc/
│   ├── Barplot_best_match.R (Create stacked barplot Figure 3.)
│   ├── Citizen_science_stats.R (Create barplots of citizen science observations.)
│   ├── Completed_habitats_to_table.R (Create LaTeX table of sampled habitats.)
│   ├── Data_analysis.R (Main script for data analysis.)
│   ├── Habitat_level_accuracy.R (Comparison of identification success summarised by habitat type.)
│   ├── Included_taxa.R (To check on which wrongly IDd taxa the resp. model was not trained.)
│   ├── Observation_level_accuracy.R (Comparison of identification success summarised by observation.)
│   ├── Sampling_design.R (Create map from initial submission, etc.)
│   ├── Tables_acc_per_plant_part.R (Create LaTeX table of ID success per plant part)
│   ├── Taxon_in_<ID provider>.R (Check if specific taxon known to model. Where no API -> manual check.)
│   ├── taxonomy_match_manual.R (List of synonyms that were manually resolved.)
│   └── wfo.R (Check synonyms using WFO.)
└── README.md (This file.)

```

## Workflow
Data validation and analysis is conducted as an iterative process with several loops (Figure 1). The main reason for this are the need to manually check taxonomic mismatches, as well as the possibility of false species identifications in the InfoFlora Fieldbook.
Plant photographs are taken in the field. They are annotated and uploaded to the InfoFlora Fieldbook via the FlorApp. The script infoflora.py is then used to download all labelled images via the InfoFlora API and store them locally with corresponding metadata. Subsequently, one or multiple BatchRequest objects are created. These point to the images and hold information about image location and metadata. The BatchRequests objects set up a connection to the identification providers via the respective APIs, send identification requests for each image, and store the response. Top taxon suggestions are then extracted in a standardised format and written to Responses.xlsx.

In the next step, the taxonomy.py is used to standardise the taxonomy bewteen different plant identification providers. To avoid having to store a data base of the entire world's plant taxonomic systems, the script only checks taxa that occur in the Responses.xlsx. If a name suggested by an identification provider does not match the name from the InfoFLora Fieldbook, the script sends an API request to WorlfFloraOnline (WFO) to check if the name is listed as a synonym. If the taxonomy cannot be resolved automatically, the user is asked to resolve the issue manually. We compared the taxon suggestion of the identification providers considering the respective taxonomic backbone and concepts of e.g. aggregates and used further taxonomic databases such as that of Kew Botanical Gardens. The script then creates Final.xlsx, which is used by Data_analysis.R. During data analysis, false identifications are flagged and exported to SingleImages.csv. This file is used by Check_misclassifications.py, which provides a GUI to explore the wrong identifications and search for obvious issus, e.g., photographs that were accidentially uploaded with the false observation. (I.e., errors from data entry in the field or any remaining unresolved taxonomy mismatches.)

After such technical issues are resolved, SingleImages.csv was used to identify observations where additional expert validation was required. After resolving remaining issues, image metadata is updated within the BatchRequest object(s). Data_analysis.R then produces the final version of plots, statistics, and LaTeX tables.

```mermaid
graph TD
    A[Field sampling] --> |FlorApp| B[(InfoFlora<br>Fieldbook)]
    B --> |infoflora.py| C[/Images + metadata/]
    D[(<br>BatchRequest Object<br><i>batchrequest_v201.py</i>)] <--> E[Plant ID<br>service API]
    C --> D
    D --> F[/Responses.xlsx/]
    F --> J[(Taxonomy<br>Database<br><i>taxonomy.py</i>)]
    I[WFO API] <--> J
    J --> H[/Final.xlsx/]
    K[User input] <--> J
    H --> X[Data analysis<br><i>Data_analysis.R</i>]
    X --> L[/SingleImages.csv/]
    L --> |Expert validation| B
    L --> M[Data Control Center<br><i>Check_misclassifications.py</i>]
    M --> J
    M --> |Fix missing<br>responses<br>manually if<br>necessary| D
    M --> |User action:<br>Edit if necessary| B
    X --> Z[/Results<br>Plots, Statistics/]
classDef empty width:0px,height:0px;
```
**Figure 1:** Overview of the data collection and processing workflow. Additional steps involved manual insertion of Flora Incognita and FlorID "vision only" results into the BatchRequest objects, resp. the Responses.xlsx via additional scripts. This is due to the circumstance that Flora Incognita did not provide direct access to their API but ran the model locally and sent us the results as json. For the vision only version of FlorID, the information was separately extracted from the responses (already present in the Batchrequest objects, but not stored separately from the combined model output).
