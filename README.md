# SwissPlantCV
Testing state-of-the-art vascular plant species identification computer vision models for Swiss vascular plants.

## Workflow
Data validation and analysis is conducted as an iterative process with several loops (Figure 1). The main reason for this are the need to manually check taxonomic mismatches, as well as the possibility of false species identifications in the InfoFlora Fieldbook.
Plant photographs are taken in the field. They are annotated and uploaded to the InfoFlora Fieldbook via the FlorApp. The script infoflora.py is then used to download all labelled images via the InfoFlora API and store them locally with corresponding metadata. Subsequently, one or multiple BatchRequest objects are created. These point to the images and hold information about image location and metadata. The BatchRequests objects set up a connection to the identification providers via the respective APIs, send identification requests for each image, and store the response. Top taxon suggestions are then extracted in a standardised format and written to Responses.xlsx.

In the next step, the taxonomy.py is used to standardise the taxonomy bewteen different plant identification providers. To avoid having to store a data base of the entire world's plant taxonomic systems, the script only checks taxa that occur in the Responses.xlsx. If a name suggested by an identification provider does not match the name from the InfoFLora Fieldbook, the script sends an API request to WorlfFloraOnline (WFO) to check if the name is listed as a synonym. If the taxonomy cannot be resolved automatically, the user is asked to resolve the issue manually. We compared the taxon suggestion of the identification providers considering the respective taxonomic backbone and concepts of e.g. aggregates and used further taxonomic databases such as that of Kew Botanical Gardens. The script then creates Final.xlsx, which is used by Data_analysis.R. During data analysis, false identifications are flagged and exported to SingleImages.csv. This file is used by Check_misclassifications.py, which provides a GUI to explore the wrong identifications and search for obvious issus, e.g., photographs that were accidentially uploaded with the false observation. (I.e., errors from data entry in the field or any remaining unresolved taxonomy mismatches.)

After such technical issues are resolved, SingleImages.csv was used to identify observations where additional expert validation was required. After resolving remaining issues, image metadata is updated within the BatchRequest object(s). Data_analysis.R then produces the final version of plots, statistics, etc.

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
**Figure 1:** Overview of the data collection and processing workflow.
