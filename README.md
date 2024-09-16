# SwissPlantCV
Testing state-of-the-art vascular plant species identification computer vision models for Swiss vascular plants.

## Workflow
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
    L --> M[Data Control Center<br><i>Check_misclassifications.py</i>]
    M --> J
    M --> |Fix responses<br>manually if<br>necessary| D
    M --> |User action:<br>Edit if necessary| B
    X --> Z[/Results<br>Plots, Statistics/]
classDef empty width:0px,height:0px;
```
