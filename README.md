# SwissPlantCV
Testing state-of-the-art vascular plant species identification computer vision models for Swiss vascular plants.

## Workflow
```mermaid
graph TD
    A[Field sampling] --> |FlorApp| B[(InfoFlora<br>Fieldbook)]
    B --> |infoflora.py| C[/Images + metadata/]
    D[(<br>BatchRequest Object<br>=batchrequest_v102.py=)] <--> E[Plant ID<br>service API]
    C --> D
    D --> F[/Responses.xlsx/]
    F --- G[ ]:::empty
    G --> |"taxonomy.py"| H[/Final.xlsx/]
    I[WFO API] <--> J[(Taxonomy<br>Database<br>=taxonomy.py=)]
    K[User input] --> J
    J --- G
    H --> X[Data analysis<br>=Data_analysis.R=]
    X --> L[/SingleImages.csv/]
    L --> M[Data Control Center<br>=Check_misclassifications.py=]
    M --> J
    M --> |Fix responses\nmanually if\nnecessary| D
    M --> |User action:<br>Edit if necessary| B
    X --> Z[/Results<br>Plots, Statistics/]
classDef empty width:0px,height:0px;
```
