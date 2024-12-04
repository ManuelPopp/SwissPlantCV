#!/usr/bin/Rscript
#>------------------------------------<?
##
## Script name: Sampling design
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2023-04-18
##
## ---------------------------
##
## Notes: -
##
##
#>------------------------------------<?

#>----------------------------------------------------------------------------<?
#> Install/load packages
packages <- c("readxl", "xlsx", "ggplot2", "vegan", "betapart", "sf", "dplyr",
              "tidyr", "xml2", "plotKML", "lubridate", "utils")
for(i in 1:NROW(packages)){
  if(!require(packages[i], character.only = TRUE)){
    install.packages(packages[i])
    library(packages[i], character.only = TRUE)
  }
}

#>----------------------------------------------------------------------------<?
#> Main settings
dir_main = "/home/manuel/ownCloud - Manuel Richard Popp (wsl.ch)@drive.switch.ch/PlantApp"
dir_dat <- file.path(dir_main, "dat")
dir_out <- file.path(dir_main, "out")
dir.create(dir_out)
dir_fig <- file.path(dir_main, "fig")
dir.create(dir_fig)
dir_shp <- file.path(dir_main, "gis", "shp")
dir.create(dir_shp)

## Main colour scheme
cols <- c(
  "forestgreen",
  "darkgreen",
  rgb(179, 213, 198, 100, maxColorValue = 255),
  rgb(21, 105, 103, 100, maxColorValue = 255),
  rgb(149, 0, 0, 100, maxColorValue = 255),
  rgb(0, 142, 197, 100, maxColorValue = 255)
)

## Colour scheme for "Formationen"/Habitat areas (highest level)
class_cols <- c(
  "blue", "khaki1", "cyan", "chartreuse", "chartreuse4", "darkgreen",
  "darkgrey", "brown"
  )

## Swiss Grid (CH1903 / LV03 -- Swiss CH1903 / LV03) PROJ.4
EPSG21781 <- paste(
  "+proj=somerc +lat_0=46.9524055555556",
  "+lon_0=7.43958333333333 +k_0=1 +x_0=600000 +y_0=200000",
  "+ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0",
  "+units=m +no_defs +type=crs"
  )

#>----------------------------------------------------------------------------<?
#> Import functions
source(file.path(dir_main, "rsc/fun/Species_Matrix.R"))
source(file.path(dir_main, "rsc/fun/KML_Styling.R"))

#>----------------------------------------------------------------------------<?
#> Load data
## Load habitat list
dir_habitats <- file.path(dir_dat, "Habitats.xlsx")
habitats <- readxl::read_excel(dir_habitats, sheet = 1, col_names = TRUE)
habitats$Habitat_Sci[habitats$Habitat_Sci == "0"] <- NA

## Load biogeographic regions shapefile
dir_bio_reg = file.path(
  dir_dat, "BioGeoRegionen", "BiogeographischeRegionen",
  "N2020_Revision_BiogeoRegion.shp"
  )

bio_reg <- sf::st_read(dir_bio_reg)

bio_reg_agg <- bio_reg %>%
  group_by(RegionNumm) %>%
  summarise(
    geometry = st_union(geometry),
    Shape_Area = sum(Shape_Area),
    Region = min(RegionNumm),
    DeName = unique(DERegionNa)
    )

## Load habitat observations table
dir_habitat_obs <- file.path(dir_dat, "Observed_habitats_Apr2023.csv")

habitat_obs_table <- read.csv(dir_habitat_obs, encoding = "UTF-8")
habitat_obs <- sf::st_as_sf(
  habitat_obs_table, coords = c("x", "y"), crs = EPSG21781
  )

## Transform sf objects to a common coordinate reference system
habitat_obs <- sf::st_transform(habitat_obs, crs = st_crs(bio_reg_agg))

#>----------------------------------------------------------------------------<?
#> Plot biogeographic regions
pdf(file = file.path(dir_fig, "Releves.pdf"), width = 10, height = 10)
par(mar = c(0.25, 0, 1, 0), oma = c(0, 0, 0, 0))
plot(bio_reg_agg$geometry,
     col = cols[bio_reg_agg$RegionNumm],
     main = "Biogeographic Regions")
legend("bottom", ncol = ceiling(length(bio_reg_agg$Region)/2),
       fill = cols[bio_reg_agg$Region],
       legend = bio_reg_agg$DeName)

#>----------------------------------------------------------------------------<?
#> Extract biogeographic regions
#> I use bio_reg, since aggregating festures returned non-closed linestring
joined <- sf::st_join(habitat_obs, bio_reg, left = FALSE)
joined$habitat_id_lvl <- nchar(as.character(joined$habitat_id))
joined$habitat_group <- as.numeric(substr(joined$habitat_id, 1, 1))
joined$habitat_class <- as.numeric(substr(joined$habitat_id, 2, 2))

#>----------------------------------------------------------------------------<?
#> Find localities with high probability for specific habitats of interest
## Subset observations to those with fully identified habitats
full_id <- joined[joined$habitat_id_lvl >= 3,]

## Summarise to habitat (not species) level
full_id_habitats <- full_id %>%
  group_by(releve_id, releve_type, DERegionNa) %>%
  summarise(N_Species = n_distinct(Species),
            elevation = median(na.omit(altitude_min)),
            habitat_id = median(na.omit(habitat_id)),
            date = max(date))

## Remove single-species points and a single "outlier" habitat with > 1000
## records
full_id_habitats <- full_id_habitats[full_id_habitats$N_Species > 1,]
full_id_habitats <- full_id_habitats[full_id_habitats$N_Species < 1000,]

## Subset for specific releve types
releve_types <- c("ABS", "BB", "BB+", "C", "E", "PR", "PR+", "S")
full_id_habitats <- full_id_habitats[
  full_id_habitats$releve_type %in% releve_types, ]

## Add elevational zonation
full_id_habitats$Elevation_zone <- cut(
  full_id_habitats$elevation,
  breaks = c(-1/0, 300, 800, 1800, 3000, 1/0),
  labels = c("planar", "kollin", "montan", "alpin", "nival"),
  include.lowest = FALSE,
  right = FALSE
  )

## Plot fully identified habitats
lvls <- unique(habitats$Habitat_area_descr)[
  sort(unique(habitats$Habitat_area))
  ]

full_id_habitats$Klasse <- factor(
  lvls[
    as.numeric(
      substr(as.character(full_id_habitats$habitat_id), 1, 1)
      )
    ],
  levels = lvls
)

plot(full_id_habitats$geometry,
     cex = 1.2,#log(full_id_habitats$N_Species) / 10,
     pch = as.numeric(full_id_habitats$Elevation_zone),
     col = class_cols[as.numeric(full_id_habitats$Klasse)],
     add = TRUE)

legend("topleft", title = "Relev?s",
       legend = c(
         levels(full_id_habitats$Klasse),
         levels(full_id_habitats$Elevation_zone)
         ),
       col = c(
         class_cols,
         rep("black", length(levels(full_id_habitats$Elevation_zone)))
       ),
       pch = c(
         rep(19, length(levels(full_id_habitats$Klasse))),
         seq(1,length(levels(full_id_habitats$Elevation_zone)))
         ),
       cex = 1.2,
       bty = "n"
       )
dev.off()

## Create overview table of sampling frequency for different habitats
### Create non-spatial table and split habitat ID levels
full_id_habitats[,
                 c("Formation", "Klasse", "Verband")
                 ] <- do.call(rbind,
                              lapply(as.character(
                                full_id_habitats$habitat_id),
                                FUN = function(x){
                                  as.numeric(
                                    strsplit(x,"")[[1]][1:3]
                                  )
                                  }
                                )
                              )
full_id_habitats_table <- sf::st_drop_geometry(full_id_habitats)

### Remove type zero entries (zeros on any level of habitat ID
### are normally reserved for habitats without vegetation)
full_id_habitats_table <- full_id_habitats_table[
  which(
    full_id_habitats_table$Klasse != 0 &
      full_id_habitats_table$Verband != 0
  ),
]

full_id_habitats_table$Formation <- factor(
  lvls[full_id_habitats_table$Formation],
  levels = lvls)
full_id_habitats_table$Klasse <- factor(full_id_habitats_table$Klasse)
full_id_habitats_table$Verband <- factor(full_id_habitats_table$Verband)

### Remove rows with entries for "Bebaute Anlagen ohne Vegetation"
full_id_habitats_table <- full_id_habitats_table[
  which(!is.na(full_id_habitats_table$Formation)),
  ]

### Calculate sampling frequencies
sampling_freq <- full_id_habitats_table %>%
  group_by(DERegionNa,
           #Elevation_zone,
           Formation,
           Klasse,
           Verband) %>%
  summarise(Aufnahmen = n())

### Add observations with frequency zero
habitat_table <- habitats %>%
  group_by(Habitat_area, Habitat_type_0, Habitat_type_1) %>%
  summarise() %>%
  drop_na()

habitat_table$Habitat_area <- factor(
  levels(sampling_freq$Formation)[habitat_table$Habitat_area],
  levels = lvls
  )

which(duplicated(habitat_table))

habitat_table$Habitat_type_0 <- factor(habitat_table$Habitat_type_0)
habitat_table$Habitat_type_1 <- factor(habitat_table$Habitat_type_1)

for(i in 1:nrow(habitat_table)){
  for(j in unique(sampling_freq$DERegionNa)){
    matches <- which(
      sampling_freq$DERegionNa == j &
        sampling_freq$Formation == habitat_table$Habitat_area[i] &
        sampling_freq$Klasse == habitat_table$Habitat_type_0[i] &
        sampling_freq$Verband == habitat_table$Habitat_type_1[i]
    )
    if(length(matches) < 1){
      new_line <- data.frame(DERegionNa = j,
                             Formation = habitat_table[i, 1],
                             Klasse = habitat_table[i, 2],
                             Verband = habitat_table[i, 3],
                             Aufnahmen = 0)
      #### Just to make sure...
      names(new_line) <- names(sampling_freq)
      sampling_freq <- rbind(sampling_freq, new_line)
      print(paste(length(matches), "entries found for",
                  sampling_freq$DERegionNa,
                    sampling_freq$Formation,
                    sampling_freq$Klasse,
                    sampling_freq$Verband))
    }else{
      print(paste(length(matches), "entries found."))
    }
  }
}

which(duplicated(sampling_freq))

### Add description for level 2 data
lvl_2 <- as.data.frame(
  readxl::read_excel(dir_habitats, sheet = 4, col_names = TRUE)
  )

sampling_freq$Beschreibung <- mapply(function(a, b, c){
  desc <- lvl_2$Description[which(
    lvl_2$Habitat_area == a & lvl_2$Habitat_type_lvl_0 == b &
      lvl_2$Habitat_type_lvl_1 == c
  )]
  if(length(desc) == 1){
    return(desc)
  }else{
    return("")
  }
},
a = as.numeric(sampling_freq$Formation),
b = as.numeric(sampling_freq$Klasse),
c = as.numeric(sampling_freq$Verband))

### Sort data and export
sampling_freq <- sampling_freq[
  with(
    sampling_freq,
    order(DERegionNa, Formation, Klasse, Verband)
  ),
]

xlsx::write.xlsx(as.data.frame(sampling_freq %>%
                                 group_by(DERegionNa,
                                          Formation) %>%
                                 summarise(Aufnahmen = sum(Aufnahmen))),
                 file = file.path(dir_out, "Sampling_frequency.xlsx"),
                 sheetName = "Level_0",
                 row.names = FALSE,
                 append = FALSE)

xlsx::write.xlsx(as.data.frame(sampling_freq %>%
                                 group_by(DERegionNa,
                                          Formation,
                                          Klasse) %>%
                                 summarise(Aufnahmen = sum(Aufnahmen))),
                 file = file.path(dir_out, "Sampling_frequency.xlsx"),
                 sheetName = "Level_1",
                 row.names = FALSE,
                 append = TRUE)

xlsx::write.xlsx(as.data.frame(sampling_freq),
                 file = file.path(dir_out, "Sampling_frequency.xlsx"),
                 sheetName = "Level_2",
                 row.names = FALSE,
                 append = TRUE)

xlsx::write.xlsx(as.data.frame(sampling_freq %>%
                                 group_by(Formation,
                                          Klasse,
                                          Verband,
                                          Beschreibung) %>%
                                 summarise(Aufnahmen = sum(Aufnahmen))),
                 file = file.path(dir_out, "Sampling_frequency.xlsx"),
                 sheetName = "Level_2_no_region",
                 row.names = FALSE,
                 append = TRUE)

## Export fully ID'd habitats
dir_full_habitats_kml <- file.path(dir_out, "kml", "Fully_IDd_habitats.kml")

## Set pin colours
c_s <- class_cols[full_id_habitats$Formation]
pcols = mapply(FUN = rgb_to_kml_aged,
              colour = c_s,
              date = full_id_habitats$date)

## Add habitat descriptions
full_id_habitats$habitat_desc <- habitats$Habitat_Sci[
  match(
    as.character(full_id_habitats$habitat_id),
    gsub("NA", "", paste0(
      as.numeric(habitats$Habitat_area),
      habitats$Habitat_type_0,
      habitats$Habitat_type_1,
      habitats$Habitat_type_2
      )
    )
    )
  ]

## Add habitat one level above, where no description was found
not_found <- which(is.na(full_id_habitats$habitat_desc))
lvl <- 4

while(length(not_found) > 0 & lvl > 1){
  sheet_curr <- readxl::read_excel(dir_habitats, sheet = lvl + 1,
                                   col_names = TRUE)
  
  df_args <- c(sheet_curr[1:lvl], sep = "")
  
  full_id_habitats$habitat_desc[not_found] <- sheet_curr$Description[
    match(
      substr(as.character(full_id_habitats$habitat_id)[not_found], 1, lvl),
      gsub("NA", "",
        do.call(paste, df_args)
      )
    )
  ]
  not_found <- which(is.na(full_id_habitats$habitat_desc))
  lvl <- lvl - 1
}

descr <- paste(full_id_habitats$habitat_desc,
               full_id_habitats$releve_id,
               sep = "; Releve: ")
## Export KML
write_formattet_kml(layer = full_id_habitats,
                    file_path = dir_full_habitats_kml,
                    name_field = "habitat_id",
                    descr_field = descr,
                    colour_by = pcols,
                    colour_scheme = NA)

## Export as Shapefile
sf::st_write(full_id_habitats,
             file.path(dir_shp, "Fully_IDd_habitats.shp"),
             driver = "ESRI Shapefile",
             delete_dsn = TRUE
             )

## Attach releve IDs to habitat list
### Collapse habitat ID levels to a new column
habitats$Habitat_id <- apply(habitats[, 1:4],
                             1, paste, collapse = "")

habitats$Habitat_id <- as.numeric(gsub("NA", "", habitats$Habitat_id))

### Create empty column to store releve IDs
habitats$Pot_sampling_sites_prio <- rep(NA, nrow(habitats))

### Fill new column with potential sampling site releve IDs
for(i in 1:nrow(habitats)){
  ID <- habitats$Habitat_id[i]
  subset_curr <- full_id_habitats[full_id_habitats$habitat_id == ID, ]
  if(nrow(subset_curr) > 0){
    habitats$Pot_sampling_sites_prio[i] <- paste(
      subset_curr$releve_id[
        order(subset_curr$N_Species, decreasing = TRUE)
      ], collapse = ";"
    )
  }
}

## Create community dataset to match partial survey results
### Extract habitats of interest (lower than group level, with species lists)
hsoi <- habitats[!is.na(habitats$Habitat_type_1),]

hsoi$habitat_id <- apply(hsoi[, 1:4], 1, paste, collapse = "")
hsoi$habitat_id <- gsub("NA", "", hsoi$habitat_id)

### Create "ideal" habitat sample species presence matrix
hsoi$Species_full_name <- apply(hsoi[, c("Genus", "Epithet", "Subsp")],
                                1, paste, collapse = "_")

hsoi$Species_full_name <- gsub("_NA", "", hsoi$Species_full_name)

hsoi$Pseudo_abundance <- hsoi$Pot_dominant + 1

comm_templ <- hsoi[, c("habitat_id", "Species", "Pseudo_abundance")]

### Same "ideal" habitat template, but as a list instead of long table
ct <- split(comm_templ, f = comm_templ$habitat_id)

### Subset observations to those with survey fragments (multiple observations
### but no habitat type assigned)
multi_obs <- joined[(joined$habitat_id_lvl < 3 |
                       !joined$releve_type %in% releve_types) &
                      joined$releve_type != "N" &
                      !is.na(joined$releve_id),]

### For each survey fragment, calculate a meaningful distance to each "ideal"
### plant community
observation_ids <- unique(multi_obs$releve_id)

### Select similarity index
mthd = "simpson"

#### Define Simpson's Similarity Index
simpson_similarity <- function(x, y){
  a <- length(which(x$Species %in% y$Species))
  return(a / min(length(x$Species), length(x$Species)))
}

for(oid in observation_ids){
  #### Create subset for current sample site
  subset_curr <- sf::st_drop_geometry(multi_obs[multi_obs$releve_id == oid,
                                                c("Species")]) %>%
    distinct()
  
  subset_curr$habitat_id <- rep("current", nrow(subset_curr))
  subset_curr$Pseudo_abundance <- rep(1, nrow(subset_curr))
  subset_curr <- subset_curr[, c("habitat_id", "Species", "Pseudo_abundance")]
  
  #### Calculate similarity index
  if(mthd != "simpson"){
    #### COmbine current sample with "ideal" community data
    ds_curr <- rbind(comm_templ, subset_curr)
    
    #### Create presence/absence matrix
    matr_curr <- species_matrix(ds_curr,
                                taxon.col = "Species",
                                sample.col = "habitat_id",
                                abundance.col = "Pseudo_abundance",
                                mode = "pa")
    
    dist_curr <- as.matrix(vegan::vegdist(matr_curr,
                                          binary = TRUE,
                                          method = "jaccard"))
    
    distances <- 1 - dist_curr[nrow(dist_curr), -ncol(dist_curr)]
    
  }else{
    distances <- as.vector(
      unlist(
        lapply(ct, FUN = simpson_similarity, y = subset_curr)
        )
      )
    names(distances) <- names(ct)
    
    # The following works only for small datasets, due to allocating a
    # lot of memory
    #dist_curr <- as.matrix(betapart::beta.multi(as.numeric(matr_curr),
    #                                            index.family = "sorensen"
    #                                            )$beta.SIM)
  }
  
  #### Add distances to new dataset
  use_columns <- c("date", "altitude_min", "habitat_id", "releve_id",
                   "RegionNumm")
  
  vegdist_sf_curr <- multi_obs[multi_obs$releve_id == oid,][1, use_columns]
  vegdist_sf_curr[, names(distances)] <- distances
  
  if(oid == observation_ids[1]){
    vegdist_sf <- vegdist_sf_curr
  }else{
    vegdist_sf <- rbind(vegdist_sf, vegdist_sf_curr)
  }
}

sf::st_write(vegdist_sf,
             file.path(dir_out, "kml", "Similarities.kml"),
             driver = "kml", delete_dsn = TRUE)

## Attach releve IDs of reasonably good matches to habitat list
### Create empty column to store releve IDs
habitats$Pot_sampling_sites_guess <- rep(NA, nrow(habitats))

### Fill new column with potential sampling site releve IDs
tmp <- sf::st_drop_geometry(vegdist_sf)

for(i in 1:nrow(habitats)){
  ID <- habitats$Habitat_id[i]
  if(as.character(ID) %in% names(tmp)){
    subset_curr <- tmp[
      tmp[, as.character(ID)] > 0.25,
      c(1:5, which(names(tmp) == as.character(ID)))
      ]
    
    if(nrow(subset_curr) > 0){
      habitats$Pot_sampling_sites_guess[i] <- paste(
        subset_curr$releve_id[
          order(subset_curr[, as.character(ID)], decreasing = TRUE)
          ], collapse = ";"
      )
    }
  }
}

#>----------------------------------------------------------------------------<?
#> Try to find sampling sites through character species
## Identify ambiguous character species
character_spec <- habitats[habitats$Charakterart == 1,]
ambiguous_char_specs <- character_spec$Species[
  duplicated(character_spec$Species)
  ]

length(ambiguous_char_specs) / length(character_spec$Species)

## Identify unspecific character species
other_spec <- habitats[habitats$Charakterart == 0,]
unspecific_char_specs <- character_spec$Species[
  which(character_spec$Species %in% other_spec$Species)
  ]

length(unspecific_char_specs) / length(character_spec$Species)

## Find character species identified in foreign habitats
habitat_obs_table <- read.csv(dir_habitat_obs, encoding = "UTF-8")
hobs <- habitat_obs_table[, c("habitat_id",
                              "Species"
                              )]

match_with_obs <- function(species, main_habitat, df = hobs){
  sset <- hobs[species %in% hobs$Species,]
  sstr <- substr(sset$habitat_id, 1, length(main_habitat))
  if(substr(main_habitat, 1, length(sstr)) != sstr){
    return(list(species, sstr))
  }else{
    return(list())
  }
}

character_spec$habitat_id <- paste0(character_spec$Habitat_area,
                                    character_spec$Habitat_type_0,
                                    character_spec$Habitat_type_1,
                                    character_spec$Habitat_type_2)
character_spec$habitat_id <- gsub("NA", "", character_spec$habitat_id)

cheating_char_specs <- mapply(FUN = match_with_obs,
                              species = character_spec$Species,
                              main_habitat = character_spec$habitat_id)

definite_char_specs <- character_spec[!duplicated(character_spec$Species),]

potential_habitat_heatmap <- function(lvl_0, lvl_1, lvl_2,
                                      dcs = definite_char_specs,
                                      ds = habitat_obs){
  ### Select the relevant character species
  c_species <- dcs[dcs[, 1] == lvl_0 &
                     dcs[, 2] == lvl_1 &
                     dcs[, 3] == lvl_1, "Species"]
  
  ### Find the character species in the data set
  subds <- ds[ds$Species %in% c_species,]
  
  if(nrow(subds) == 0){
    print("Character species not found in the data set.")
  }else{
    subds %>%
      group_by(releve_id) %>%
      sumarise(n_char_spec = n())
  }
}