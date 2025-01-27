#!/usr/bin/env Rscript
#>------------------------------------<
##
## Script name: Data analysis
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2023-09-04
##
## ---------------------------
##
## Descripton: Analysis of the API responses
## Notes: -
##
#>----------------------------------------------------------------------------<|
#> Install/load packages
rm(list = ls())
import <- function(...) {
  #' Import R packages. Install them if necessary.
  #'
  #' @param ... any argument that can be passed to install.packages.
  #' @details The function installs only packages that are missing. Packages
  #' are loaded.
  #' @examples
  #' # Load packages
  #' import("dplyr", "MASS", "terra", dependencies = TRUE)
  #'
  #' @seealso \code{\link[base]{install.packages}}
  #' @export
  args <- list(...)
  packages <- args[names(args) == ""]
  kwargs <- args[names(args) != ""]

  for (package in packages) {
    if (!require(package, character.only = TRUE)) {
      do.call(install.packages, c(list(package), kwargs))
    }
    require(package, character.only = TRUE)
  }
}

import(
  "rstudioapi", "dplyr", "ggplot2", "treemap", "readxl", "rjson", "tidyr",
  "ggbreak", "stringr", "gridExtra", "terra", "multcomp", "emmeans", "MASS",
  "reshape2", "lme4", "grDevices", "pbkrtest", "afex", "grid", #"sjPlot",
  "parallel",
  dependencies = TRUE
) # , "xlsx")

# If no variable values are to be exported to Dropbox for synchronisation with
# Overleaf, ignore the following.
if (Sys.info()[1] == "Linux") {
  dir_dbx <- "/home/manuel/Dropbox"
} else {
  dir_dbx <- "C:/Users/poppman/Dropbox"
}

#>----------------------------------------------------------------------------<|
#> Functions
get_file_location <- function() {
  this_file <- commandArgs() %>%
    tibble::enframe(name = NULL) %>%
    tidyr::separate(
      col = value,
      into = c("key", "value"), sep = "=", fill = "right"
    ) %>%
    dplyr::filter(key == "--file") %>%
    dplyr::pull(value)

  if (length(this_file) == 0) {
    this_file <- rstudioapi::getSourceEditorContext()$path
  }
  return(dirname(this_file))
}

# Set dynamic document values
# To produce the initial manuscript and dynamically update variables to encorpo-
# rate updates in the underlying data, the set_var() function was used.
# I "disabled" this function to avoid issues while running the script in another
# context.
variable_text_renew <- FALSE
export_variables_to_overleaf <- FALSE

if (export_variables_to_overleaf) {
  set_var <- function(
    name, value, digits = 2,
    file = file.path(
      dir_dbx,
      "Apps/Overleaf/SwissPlantCV/var",
      "variables.tex"
    )) {
    if (dir.exists(dirname(dirname(file)))) {
      dir.create(dirname(file), showWarnings = FALSE)
    } else {
      warning(
        paste(
          "Directory",
          dirname(dirname(file)),
          "not found. Cannot write variables."
        )
      )
      return()
    }
    
    if (get("variable_text_renew")) {
      append <- FALSE
      variable_text_renew <<- FALSE
    } else {
      append <- TRUE
    }
    
    # Remove existing definitions of the variable if there are any
    if (file.exists(file)) {
      lines <- readLines(file)
      filtered_lines <- lines[
        !grepl(paste0("{\\", name, "}"), lines, fixed = TRUE)
      ]
      writeLines(filtered_lines, file)
    }
    
    cat(
      sprintf(paste0("\\newcommand{\\", name, "}{%.", digits, "f}\n"), value),
      file = file, append = append
    )
  }
} else {
  set_var <- function(...) {return()}
}

# Simplify p-values from a vector or matrix
reduce_p <- function(x) {
  char_vals <- as.character(round(x, 2))
  char_vals[which(x < 0.05)] <- "\\llap{$<$}\\hspace{-0.05em}0.05"
  char_vals[which(x < 0.01)] <- "\\llap{$<$}\\hspace{-0.05em}0.01"
  char_vals[which(x < 1e-5)] <- "\\llap{$<$}{$10^{-5\\hspace{0.4em}}$}"
  char_vals[which(x < 1e-10)] <- "\\llap{$<$}\\num{1e-10}"
  names(char_vals) <- colnames(x)
  dim(char_vals) <- dim(x)

  return(char_vals)
}

signif_digits <- function(x, n = 3) {
  f <- function(value, nd = n) {
    char_val <- as.character(signif(value, nd))
    nc <- length(gregexpr("[[:digit:]]", char_val)[[1]])

    if (nc < n) {
      if (grepl(".", char_val, fixed = TRUE)) {
        cpse <- ""
      } else {
        cpse <- "."
      }
      char_val <- paste(
        char_val, paste0(rep("0", n - nc), collapse = ""),
        sep = cpse
      )
    }

    return(char_val)
  }

  out <- unlist(sapply(X = x, FUN = f))
  dim(out) <- dim(x)

  return(out)
}

#>----------------------------------------------------------------------------<|
#> Settings
# I disabled export of plots and tables to simplify the script and avoid
# potential issues with non-existing directories on another user's machine.
# If your folder structure is set up correctly and directory names are adjusted,
# you can set these to TRUE in order to export tables and figures.
save_plots <- FALSE
save_tables <- FALSE

# Directories
dir_this_file <- get_file_location()
if (!dir.exists(dir_this_file)) {
  if (Sys.info()[1] == "Linux") {
    dir_this_file <- "/home/manuel/ownCloud/PlantApp/rsc"
  } else {
    dir_this_file <- "C:/Users/poppman/switchdrive/PlantApp/rsc"
  }
}

dir_main <- dirname(dir_this_file)
dir_dat <- file.path(dir_main, "dat")
dir_out <- file.path(dir_main, "out")
dir_fig <- file.path(dir_main, "pub", "fig")
dir_tab <- file.path(dir_main, "pub", "tab")
dir_stt <- file.path(dir_main, "pub", "stt")
dir_etc <- file.path(dir_main, "pub", "etc")

dir_fig_online <- file.path(dir_dbx, "Apps/Overleaf/SwissPlantCV/fig")
dir_tab_online <- file.path(dir_dbx, "Apps/Overleaf/SwissPlantCV/tab")
dir_stat_online <- file.path(dir_dbx, "Apps/Overleaf/SwissPlantCV/stt")

dir.create(dir_fig, recursive = TRUE, showWarnings = FALSE)
dir.create(dir_tab, recursive = TRUE, showWarnings = FALSE)
dir.create(dir_stt, recursive = TRUE, showWarnings = FALSE)
dir.create(dir_etc, recursive = TRUE, showWarnings = FALSE)

# Style
safe_colorblind_palette <- c(
  "#88CCEE", "#CC6677", "#DDCC77", "#117733", "#332288", "#AA4499", "#44AA99",
  "#999933", "#882255", "#661100", "#6699CC", "#888888"
)

options(
  ggplot2.discrete.colour = safe_colorblind_palette,
  ggplot2.discrete.fill = safe_colorblind_palette
)

# theme_set(theme_bw())

# Set whether analyses should be conducted on species level (subspecies
# determined in the field will be evaluated as if determined to species level
# only)
SPECIESLVL <- TRUE

#>----------------------------------------------------------------------------<|
#> Load data
# Load API response data
tryCatch(
  {
    # Try to read the data using the xlsx package (only works if installed,
    # caused issues with some OS and R versions...)
    rsp <<- xlsx::read.xlsx(file.path(dir_out, "Final.xlsx"), sheetIndex = 1)
  },
  error = function(e) {
    # Read the data using the readxl package if the xlsx package failed
    rsp <<- readxl::read_excel(file.path(dir_out, "Final.xlsx"))
  }
)

head(rsp)

sites <- read.csv(file.path(dir_dat, "Releve_info.csv"))
rsp$habitat <- sites$habitat_id[match(rsp$releve_id, sites$releve_id)]
rsp$date <- sites$date[match(rsp$releve_id, sites$releve_id)]
rsp$location <- sites$location[match(rsp$releve_id, sites$releve_id)]

sampling_coordinates <- data.frame(
  do.call(rbind, strsplit(gsub("[,()]", "", rsp$location), split = " "))
)

names(sampling_coordinates) <- c("lat", "lon")
sampling_coordinates$id <- seq(1, nrow(sampling_coordinates))
sampling_coordinates$lat <- as.numeric(sampling_coordinates$lat)
sampling_coordinates$lon <- as.numeric(sampling_coordinates$lon)

sampling_locations <- terra::vect(
  sampling_coordinates,
  geom = c("lon", "lat"),
  crs = "+proj=longlat +datum=WGS84"
)

fbiogeo <- file.path(
  dir_dat,
  "BioGeoRegionen",
  "BiogeographischeRegionen",
  "N2020_Revision_BiogeoRegion.shp"
)

biogeo <- terra::vect(fbiogeo)

#>----------------------------------------------------------------------------<|
#> Add biogeographic regions
biogeo <- terra::project(biogeo, sampling_locations)
int <- terra::intersect(sampling_locations, biogeo)
rsp$biogeo_region <- int$DERegionNa

#>----------------------------------------------------------------------------<|
#> Manual taxon corrections and taxonomy reconciliation
name_short <- function(x) {
  if (typeof(x) == "list") {
    x <- x[[1]]
  }

  name <- paste(unlist(strsplit(x, split = " "))[c(1, 2)], collapse = " ")
  return(name)
}

## Remove uncertain IDs
remove_taxa <- c("Epipactis rhodanensis Gévaudan & Robatsch")
rsp <- rsp[which(!rsp$true_taxon_id %in% remove_taxa), ]

# Replace backslashes in image file paths
rsp$image_files <- gsub(
  "[^0-9A-Za-z:;._]", "/", rsp$image_files,
  ignore.case = TRUE
)

## Accept different taxonomic systems by resolving synonyms/aggregates not
## covered by the automatic synonym detection (taxonomy,py)
source(file.path(dir_main, "rsc", "taxonomy_match_manual.R"))

if (length(taxonomy_mismatches) != length(alternative_names) |
  length(taxonomy_mismatches) != length(alternative_aggs)) {
  stop("Taxonomy reconciliation vectors are of different lengths. Check!")
}

columns_names <- which(
  names(rsp) %in% c("first", "second", "third", "forth", "fifth")
)

columns_match <- which(
  names(rsp) %in% c(
    "match_first", "match_second", "match_third", "match_forth", "match_fifth"
  )
)

if (TRUE) {
  for (line in 1:nrow(rsp)) {
    fullname <- rsp$true_taxon_name[line]
    name <- name_short(rsp$true_taxon_name[line])

    # Check whether there are known mismatches between taxonomic systems
    if (
      name %in% taxonomy_mismatches |
        fullname %in% taxonomy_mismatches |
        name %in% apply(FUN = name_short, MARGIN = 2, rsp[line, columns_names])
    ) {
      indices <- which(taxonomy_mismatches == fullname)

      if (length(indices) == 0) {
        indices <- which(taxonomy_mismatches == name)
      }

      for (c in 1:length(columns_names)) {
        result <- rsp[line, columns_names[c]][[1]]

        # Check whether the suggested name is a "synonym" according to an alter-
        # native taxonomic system
        if (result %in% alternative_names[indices]) {
          rsp[line, columns_match[c]] <- 0

          # Check whether the suggested name is grouped in an aggregate
          # following some system
        } else if (result %in% alternative_aggs[indices]) {
          rsp[line, columns_match[c]] <- 1
        } else if (
          name_short(result) == name & grepl(glob2rx("* agg*."), result)
        ) {
          rsp[line, columns_match[c]] <- 1
        }
      }
    }
  }
}

## Fix subspecies matches
row_indices <- which(grepl(glob2rx("* sub*."), rsp$true_taxon_name))

for (line in row_indices) {
  sname <- name_short(rsp$true_taxon_name[line])

  for (c in 1:length(columns_names)) {
    result <- rsp[line, columns_names[c]][[1]]
    if (startsWith(result, sname)) {
      if (grepl(glob2rx("* agg*."), result)) {
        if (SPECIESLVL) {
          rsp[line, columns_match[c]] <- 1
        } else {
          rsp[line, columns_match[c]] <- 2
        }
      } else if (grepl(glob2rx("* sub*."), result)) {
        if (rsp[line, columns_match[c]] != 0) {
          print(
            paste(
              "Check subspecies: True =",
              rsp$true_taxon_name[line],
              "Predicted =", result
            )
          )
        }
      } else {
        if (SPECIESLVL) {
          rsp[line, columns_match[c]] <- 1
        } else {
          rsp[line, columns_match[c]] <- 0
        }
      }
    }
  }
}

## Set match level to zero in cases predicted taxon is on subspecies-level but
## analyses are performed on species-level only
if (SPECIESLVL) {
  for (c in 1:length(columns_names)) {
    rsp[
      which(
        rsp[, columns_match[c]] == -1 &
          grepl(glob2rx("* sub*."), rsp[[columns_names[c]]])
      ), columns_match[c]
    ] <- 0
  }
}

## Adjust match level where field ID is on subspecies level
## This may cause "double-matches" in cases where some taxonomy suggests two
## different species while our taxonomy lists them as subspecies, e.g.
## iNaturalist uses Cerastium holosteoides instead of C. fontanum subsp. vulgare
## and also suggests C. fontanum as second suggestion in one case. Here, we will
## get 0, 0 then.
if (SPECIESLVL) {
  for (r in grep(glob2rx("* sub*."), rsp$true_taxon_name)) {
    for (c in columns_match) {
      if (rsp[r, c] == 1) {
        rsp[r, c] <- 0
      }
    }
  }
}

#>----------------------------------------------------------------------------<|
#> Add field identifications
# Load taxonomic backbone
tbb <- read.csv(
  file.path(dir_dat, "Taxonomic_backbone_wHier_2022.csv"),
  sep = ",", header = TRUE, skip = 1
) %>%
  dplyr::select(
    ID, Species_level_ID, Name, Genus, Family, Order, Class, Phylum, COMECO_ID
  )

head(tbb)

# Add taxonomic information to API responses
df <- dplyr::left_join(
  x = rsp,
  y = tbb,
  by = dplyr::join_by(true_taxon_id == ID)
)

cv_model_names <- c(
  "Flora Incognita", "FlorID", "FlorID vision", "iNaturalist", "Pl@ntNet"
)

df$cv_model_name <- cv_model_names[
  match(df$cv_model, c(
    "floraincognita", "florid", "florvision", "inaturalist", "plantnet"
  ))
]

#-------------------------------------------------------------------------------

# Add habitat information
habitat_list <- c(
  "Aquatic",
  "Shores and wetlands",
  "Glaciers, rock, rubble and scree",
  "Grassland",
  "Herbaceous fringes and scrubland",
  "Forests",
  "Ruderal sites",
  "Plantations, fields and crops"
)

df$habitat_main <- habitat_list[as.numeric(substr(df$habitat, 1, 1))]

# Add plant life form information
sp_info <- read.csv(
  file.path(dir_dat, "growth_form_info.csv"),
  header = TRUE, skip = 1
)

df$growth_form <- sp_info$growth_form[match(df$Name, sp_info$sp_name)]

# Correct inconsistent labeling for ferns
df$plant_organ[which(df$growth_form == "Fern")] <- gsub(
  "i", "f", df$plant_organ[which(df$growth_form == "Fern")]
)

# Add full plant organ names
plant_organ_names <- c(
  "Inflorescence", "Infructescence", "Vegetative", "Trunk", "Several"
)
df$plant_organ_name <- plant_organ_names[
  match(df$plant_organ, c("i", "f", "v", "t", "s"))
]

#-------------------------------------------------------------------------------

# Set aggregate-level matches to 5 in case a wrong species was suggested
col_nam <- match(c("first", "second", "third", "forth", "fifth"), names(df))
col_val <- match(
  c(
    "match_first", "match_second", "match_third", "match_forth", "match_fifth"
  ), names(df)
)

for (j in 1:length(col_val)) {
  for (i in 1:nrow(df)) {
    if (
      df[[col_val[j]]][i] == 1 & !grepl(glob2rx("* agg*."), df[[col_nam[j]]][i])
    ) {
      df[i, col_val[j]] <- 5
    }
  }
}

head(df)

species_list <- df %>%
  group_by(Species_level_ID) %>%
  summarize(Species = first(Name))

n_sites <- length(unique(df$releve_id))
set_var("totalreleves", n_sites, digits = 0)

n_species <- length(unique(species_list$Species))
set_var("totalspec", n_species, digits = 0)

#>----------------------------------------------------------------------------<|
#> General data set info
counts <- df %>%
  group_by(releve_id) %>%
  summarise(
    n_obs = n_distinct(observation_id)
  )

md <- median(counts$n_obs, na.rm = TRUE)
hist(counts$n_obs, nclass = 14)
sd(counts$n_obs)
se <- sd(counts$n_obs) / sqrt(length(counts$n_obs))
md - round(sd(counts$n_obs))
md + round(sd(counts$n_obs))

set_var("obsperrelevelower", md - round(sd(counts$n_obs)), 0)
set_var("obsperreleveupper", md + round(sd(counts$n_obs)), 0)

n_obs_total <- length(unique(df$observation_id))
set_var("totalobs", n_obs_total, 0)

n_photos_total <- df %>%
  filter(question_type == "single_image") %>%
  group_by(cv_model) %>%
  summarise(N = n()) %>%
  first() %>%
  dplyr::select(N) %>%
  as.numeric()

set_var("totalphotos", n_photos_total, 0)

n_habitats_total <- length(unique(df$habitat))
set_var("nhabitats", n_habitats_total, 0)

#>----------------------------------------------------------------------------<|
#> Visualize data set taxon composition
taxa <- df %>%
  group_by(Species_level_ID) %>%
  summarise(
    # Count = n(),
    Species = dplyr::first(Species_level_ID),
    Genus = dplyr::first(Genus),
    Family = dplyr::first(Family)
  ) %>%
  group_by(Genus) %>%
  summarise(
    Count = n(),
    Genus = dplyr::first(Genus),
    Family = dplyr::first(Family)
  ) %>%
  ungroup() %>%
  arrange(Family, Genus)
head(taxa)

taxa <- data.frame(taxa)
taxa$Family <- factor(taxa$Family)
taxa$Genus <- factor(taxa$Genus, levels = taxa$Genus)
set.seed(49)
base_colours <- sample(palette(rainbow(length(unique(taxa$Family)))))
taxa$Fill <- base_colours[as.numeric(taxa$Family)]

# Create nested pie chart
taxa_pie_family <- cbind(
  taxa[, c(3, 2, 4)], data.frame(Level = rep("Family", nrow(taxa)))
) %>%
  group_by(Family, Level, Fill) %>%
  summarise(Count = sum(Count)) %>%
  magrittr::set_colnames(c("Taxon", "Level", "Fill", "Count")) %>%
  ungroup() %>%
  mutate(prop = Count / sum(Count) * 100) %>%
  mutate(ypos = cumsum(prop) - 0.5 * prop) %>%
  mutate(yang = 90 + (ypos / 100 * 360))
taxa_pie_family$Alpha <- rep("high", nrow(taxa_pie_family))

taxa_pie_genus <- cbind(
  taxa[, c(1, 2, 4)], data.frame(Level = rep("Genus", nrow(taxa)))
) %>%
  group_by(Genus, Level, Fill) %>%
  summarise(Count = sum(Count)) %>%
  magrittr::set_colnames(c("Taxon", "Level", "Fill", "Count")) %>%
  ungroup() %>%
  mutate(prop = Count / sum(Count) * 100) %>%
  mutate(ypos = cumsum(prop) - 0.5 * prop) %>%
  mutate(yang = 90 + (ypos / 100 * 360))

taxa_pie_genus$Alpha <- rep(
  c("high", "low"), ceiling(nrow(taxa_pie_genus) / 2)
)[1:nrow(taxa_pie_genus)]

taxonomy_piechart <- ggplot2::ggplot(
  rbind(taxa_pie_genus, taxa_pie_family),
  aes(x = Level, y = Count, fill = Fill, group = Taxon, alpha = Alpha)
) +
  geom_bar(stat = "identity") +
  geom_col(aes(x = 0, y = 0)) +
  coord_polar(theta = "y") +
  theme_void() +
  theme(legend.position = "none") +
  geom_text(
    aes(x = Level, y = Count, angle = yang, label = Taxon),
    size = 1.5, color = "white", position = position_stack(vjust = 0.5)
  ) +
  scale_alpha_manual(values = c(1, 0.5))

# Export figures of covered taxa
if (save_plots) {
  f_out <- file.path(dir_fig, "Taxonomy_pie.pdf")
  pdf(file = f_out, height = 15, width = 15)
  print(taxonomy_piechart)
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

if (save_plots) {
  f_out <- file.path(dir_fig, "Tree_map.pdf")
  pdf(file = f_out, height = 15, width = 16)
  treemap::treemap(
    taxa,
    index = c("Family", "Genus"),
    vSize = "Count",
    vColor = "Family",
    type = "index",
    force.print.labels = TRUE,
    lowerbound.cex.labels = 0.2,
    # algorithm = "pivotSize",
    align.labels = list(c("center", "top"), c("center", "center")),
    fontsize.title = 0,
    title = "" # "Representation of taxa in the data set"
  )
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

#>----------------------------------------------------------------------------<|
#> Ensure data type factor
df$cv_model <- as.factor(df$cv_model)
df$cv_model_name <- as.factor(df$cv_model_name)
df$habitat <- as.factor(df$habitat)
df$habitat_main <- as.factor(df$habitat_main)
df$biogeo_region <- as.factor(df$biogeo_region)
df$plant_organ <- as.factor(df$plant_organ)
df$plant_organ_name <- as.factor(df$plant_organ_name)
df$question_type <- as.factor(df$question_type)
df$growth_form <- as.factor(df$growth_form)

#>----------------------------------------------------------------------------<|
#> Top 1 and top 3 matches
# Get top 1 and top 3 matches
df$Top1 <- df$match_first <= 0
df <- df %>%
  rowwise() %>%
  mutate(Top3 = any(match_first <= 0, match_second <= 0, match_third <= 0))

df_single <- df %>% filter(question_type == "single_image")
df_multi <- df %>% filter(question_type == "multi_image")

# Top 1 and top 3 matches including higher-level matches, i.e., allow aggregates
# instead of species-level matches only.
df$Top1_hl <- df$match_first <= 2
df <- df %>%
  rowwise() %>%
  mutate(Top3_hl = any(match_first <= 2, match_second <= 2, match_third <= 2))

# Sort by request type (single image or multi image)
df_single <- df %>% filter(question_type == "single_image")
df_multi <- df %>% filter(question_type == "multi_image")

# Export remaining "wrong" predictions (for single images) to use in the
# Data Control Center tkinter app for manual inspection
n_right <- df_single %>%
  group_by(releve_name, observation_id, image_files) %>%
  summarise(
    right = sum(Top1_hl, na.rm = TRUE),
    field_taxon = first(true_taxon_name),
    suggestions = paste(first, collapse = ", ")
  )

suspicious_images <- n_right[which(n_right$right < 1), ]
nrow(suspicious_images)

suspicious_obs <- suspicious_images %>%
  group_by(observation_id) %>%
  summarise(N = n())

suspicious_obs <- suspicious_obs[order(suspicious_obs$N, decreasing = TRUE), ]
nrow(suspicious_obs)
paste(suspicious_obs$observation_id, collapse = ",")

if (save_tables) {
  write.csv(
    df_single[which(!df_single$Top1_hl), ],
    file = file.path(dir_out, "SingleImages.csv")
  )
}

if (save_tables) {
  only_florid_correct <- df_single[which(n_right$right == 1), ] %>%
    filter(cv_model == "florid" & Top1)

  only_florid_correct_names <- only_florid_correct$true_taxon_name

  not_in_tbb <- df_single[
    which(
      !df_single$first %in% c(
        tbb$Name,
        sapply(
          strsplit(tbb$Name, " "),
          function(words) paste(head(words, 2), collapse = " ")
        )
      ) & !df_single$Top1_hl
    ),
  ] %>%
    mutate(flor_id_correct = true_taxon_name %in% only_florid_correct_names) %>%
    dplyr::select(first, cv_model, flor_id_correct) %>%
    dplyr::distinct()

  if (!file.exists(file.path(dir_out, "NotFoundInTBB.xlsx"))) {
    write.table(
      not_in_tbb,
      file = file.path(dir_out, "NotFoundInTBB.csv"),
      quote = FALSE, row.names = FALSE, sep = ";"
    )
  } else {
    nin_tbb <- read_xlsx(file.path(dir_out, "NotFoundInTBB.xlsx"))

    df_tmp <- df_single %>%
      mutate(swiss_species = 1, plant = 1, flor_id_correct = TRUE) %>%
      filter(!cv_model %in% c("florvision"))

    for (i in 1:nrow(df_tmp)) {
      if (df_tmp$first[i] %in% nin_tbb$first) {
        idx <- match(df_tmp$first[i], nin_tbb$first)
        df_tmp$flor_id_correct[i] <- nin_tbb$flor_id_correct[idx]
        df_tmp$swiss_species[i] <- nin_tbb$swiss_species[idx]
        df_tmp$plant[i] <- nin_tbb$plant[idx]
      }
    }

    summarised <- df_tmp %>%
      group_by(cv_model_name) %>%
      summarise(
        Total = n(),
        Top1 = sum(Top1),
        Top1_hl = sum(Top1_hl),
        Not_a_Swiss_plant = sum(swiss_species == 0 | plant == 0),
        Not_a_plant = sum(plant == 0),
        Of_which_Top_3_hl = sum((swiss_species == 0 | plant == 0) & Top3_hl),
        Of_which_FlorID_Correct = sum(swiss_species == 0 & flor_id_correct)
      ) %>%
      mutate(
        cv_model_name = paste0("{", cv_model_name, "}")
      ) %>%
      tibble::column_to_rownames(var = "cv_model_name") %>%
      as.matrix() %>%
      t()

    row.names(summarised) <- c(
      "Total", "Species-level Top 1", "Aggregate-level Top 1", "No Swiss plant",
      "Not a plant",
      "Non-Swiss Top 1 but correct Top 3",
      "Non-Swiss Top 1 where FlorID Top 1"
    )

    write.table(
      summarised[-1, ],
      file = file.path(dir_tab_online, "Non_Swiss_Plants.tex"),
      sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = TRUE,
      quote = FALSE
    )
  }
}

#>----------------------------------------------------------------------------<|
#> General summary: CV model accuracy
# Note: This general summary gives a quick comparison between various CV models.
# At this point, data might not be representative, since it they are not strati-
# fied by any factor and observations contain various numbers of images (thus,
# some species have a stronger impact on the result than others simply through
# the number of images attached to their observations and their frequency in the
# data set.)
summary_single <- df_single %>%
  group_by(cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

summary_multi <- df_multi %>%
  group_by(cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

set_var("mintoponemultispec", min(summary_multi$Top1_acc))
set_var("maxtoponemultispec", max(summary_multi$Top1_acc))
set_var("mintoponemultiagg", min(summary_multi$Top1_acc_hl))
set_var("maxtoponemultiagg", max(summary_multi$Top1_acc_hl))

single_vs_multi <- merge(
  summary_single[, c("cv_model_name", "Top1_acc")],
  summary_multi[, c("cv_model_name", "Top1_acc")],
  by = "cv_model_name",
  all.x = TRUE
)

single_vs_multi_hl <- merge(
  summary_single[, c("cv_model_name", "Top1_acc_hl")],
  summary_multi[, c("cv_model_name", "Top1_acc_hl")],
  by = "cv_model_name",
  all.x = TRUE
)

if (save_tables) {
  write.csv(
    summary_single,
    file = file.path(dir_tab, "Summary_single.csv"),
    row.names = FALSE
  )

  write.csv(
    summary_multi,
    file = file.path(dir_tab, "Summary_multi.csv"),
    row.names = FALSE
  )
}

for (i in 2:ncol(summary_single)) {
  summary_single[, i] <- round(summary_single[, i], 2)
  summary_multi[, i] <- round(summary_multi[, i], 2)
}

for (i in 2:ncol(single_vs_multi)) {
  single_vs_multi[, i] <- round(single_vs_multi[, i], 2)
  single_vs_multi_hl[, i] <- round(single_vs_multi_hl[, i], 2)
}

if (save_tables) {
  write.table(
    summary_single[, c(1, 2, 4, 3, 5)],
    file = file.path(dir_tab_online, "Summary_single.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )

  write.table(
    summary_multi[, c(1, 2, 4, 3, 5)],
    file = file.path(dir_tab_online, "Summary_multi.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )

  write.table(
    single_vs_multi,
    file = file.path(dir_tab_online, "Single_vs_multi.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE, na = "{-}"
  )

  write.table(
    single_vs_multi_hl,
    file = file.path(dir_tab_online, "Single_vs_multi_hl.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE, na = "{-}"
  )
}

# Remove FlorID vision for further analyses
df <- df[which(df$cv_model != "florvision"), ]
df_single <- df_single[which(df_single$cv_model != "florvision"), ]
df_multi <- df_multi[which(df_multi$cv_model != "florvision"), ]

#>----------------------------------------------------------------------------<|
#> Add information on whether a taxon is included in a CV model
setwd(file.path(dir_main, "rsc"))
#source("Included_taxa.R")

#>----------------------------------------------------------------------------<|
#> Summarise data set
## Use GLMs to get factors across which differences are large
setwd(file.path(dir_main, "rsc"))
source("GLM.R")

## Observation-level accuracy (accuracy across all observations in the data set)
setwd(file.path(dir_main, "rsc"))
source("Observation_level_accuracy.R")
if (save_plots) {
  f_out <- file.path(dir_fig, "Acc_by_observation.pdf")
  ggsave(f_out, plot = gg_obslvl_single, width = 5, height = 5)
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

### Habitat-level accuracy
setwd(file.path(dir_main, "rsc"))
source("Habitat_level_accuracy.R")
if (save_plots) {
  f_out <- file.path(dir_fig, "Acc_by_habitat.pdf")
  ggsave(f_out, plot = gg_hablvl_single, width = 5, height = 5)
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

### Combined plot
if (save_plots) {
  f_out <- file.path(dir_fig, "Acc_comb_obs_hab.pdf")
  pdf(f_out, width = 10, height = 5)
  grid.arrange(
    gg_obslvl_single +
      xlab("(a) By observation"),
    gg_hablvl_single +
      theme(
        # axis.title.x = element_blank(),
        axis.title.y = element_blank(),
        axis.text.y = element_blank(),
        axis.ticks.y = element_blank()
      ) +
      xlab("(b) By habitat type"),
    ncol = 2, bottom = "Identification provider",
    widths = c(1, 0.92)
  )
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

## Regional/habitat level accuracy
regional <- df_single %>%
  group_by(cv_model_name, habitat_main, biogeo_region) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

regional_long <- reshape2::melt(
  regional[
    regional$cv_model_name != "FlorID vision",
    which(!(names(regional) %in% c("Top3_acc", "Top3_acc_hl")))
  ],
  id.vars = c("cv_model_name", "habitat_main", "biogeo_region"),
  variable.name = "Measure"
)

regional_long$Level <- dplyr::recode_factor(
  regional_long$Measure,
  Top1_acc = "Species", Top1_acc_hl = "Aggregate"
)

gg_reg <- ggplot(
  data = regional_long,
  aes(x = biogeo_region, y = value, fill = Level)
) +
  geom_boxplot() +
  xlab("Biogeographical region") +
  ylab("Top 1 accurracy") +
  facet_wrap(facets = "cv_model_name") +
  scale_x_discrete(
    labels = function(x) {
      sub("Alpen", "Alpen-\n", sub("\\s", "\n", x))
    }
  ) +
  theme_bw()

# Do not use: Misleading due to grouping by biogeo instead observation id.
gg_hab <- ggplot(
  data = regional_long,
  aes(x = habitat_main, y = value, fill = Level)
) +
  geom_boxplot() +
  xlab("Main habitat type") +
  ylab("Top 1 accurracy") +
  facet_wrap(facets = "cv_model_name") +
  scale_x_discrete(
    labels = function(x) {
      gsub("^([^ ]+ [^ ]+) (.*)$", "\\1\n\\2", x)
    }
  ) +
  theme_bw() +
  theme(
    legend.position = "bottom",
    legend.direction = "horizontal",
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

# if (save_plots) {
#   f_out <- file.path(dir_fig_online, "Acc_by_habitat_main.pdf")
#   pdf(file = f_out, height = 6, width = 6)
#   print(gg_hab)
#   dev.off()
# }

habitat <- df_single %>%
  group_by(cv_model_name, habitat_main, observation_id) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

#>----------------------------------------------------------------------------<|
#> Accuracy per plant part
pp_single <- df_single %>%
  group_by(Species_level_ID, plant_organ, cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl)),
    Species = dplyr::first(Species_level_ID),
    Genus = dplyr::first(Genus),
    Family = dplyr::first(Family),
    Order = dplyr::first(Order),
    Class = dplyr::first(Class),
    Phylum = dplyr::first(Phylum)
  )

head(pp_single)

pp_single$plant_organ <- factor(pp_single$plant_organ)
pp_single$cv_model_name <- factor(pp_single$cv_model_name)
pp_single$Class <- factor(pp_single$Class)

# Comparison of plant part accuracy
# Plot does not make a lot of sense, since without prior averaging, points are
# mostly 1 and partly 0.
# ggplot(
#   data = pp_single, aes(x = plant_organ, y = Top1_acc, fill = plant_organ)
# ) +
#   geom_violin() +
#   theme(
#     axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1),
#     legend.position = "none"
#   ) +
#   facet_grid(. ~ cv_model_name) +
#   xlab("Identification provider") +
#   ylab("Top 1 accuracy")
source("Tables_acc_per_plant_part.R")

# Vegetative parts
pp_single_veg <- pp_single %>% filter(plant_organ == "v")
head(pp_single_veg)
ggplot(
  data = pp_single_veg,
  aes(x = cv_model_name, y = Top3_acc, fill = cv_model_name)
) +
  geom_violin() +
  facet_grid(. ~ Class)

ggplot(
  data = pp_single_veg,
  aes(x = cv_model_name, y = Top3_acc, fill = cv_model_name)
) +
  geom_boxplot() +
  facet_grid(. ~ Class)

# Flowers/fruits
pp_single_f <- pp_single %>% filter(plant_organ %in% c("i", "f"))
head(pp_single_f)
ggplot(
  data = pp_single_f, aes(x = cv_model_name, y = Top3_acc, fill = cv_model_name)
) +
  geom_violin() +
  facet_grid(. ~ Class)

ggplot(
  data = pp_single_f, aes(x = cv_model_name, y = Top3_acc, fill = cv_model_name)
) +
  geom_boxplot() +
  facet_grid(. ~ Class)

pp_single_f %>%
  group_by(cv_model_name, Species_level_ID) %>%
  summarise(Overall_top1 = mean(Top1_acc)) %>%
  group_by(cv_model_name, ) %>%
  summarise(Top1 = mean(Overall_top1))

# Several parts
pp_single_sev <- pp_single %>% filter(plant_organ == "s")
head(pp_single_sev)
ggplot(
  data = pp_single_sev,
  aes(x = cv_model_name, y = Top1_acc, fill = cv_model_name)
) +
  geom_violin() +
  facet_grid(. ~ Class)

ggplot(
  data = pp_single_sev,
  aes(x = cv_model_name, y = Top1_acc, fill = cv_model_name)
) +
  geom_boxplot() +
  theme(
    axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1),
    legend.position = "none"
  ) +
  facet_grid(. ~ Class) +
  xlab("Identification provider") +
  ylab("Top 1 accuracy")

pp_single_sev %>%
  group_by(cv_model_name, Species_level_ID) %>%
  summarise(Overall_top1 = mean(Top1_acc)) %>%
  group_by(cv_model_name, ) %>%
  summarise(Top1 = mean(Overall_top1))

#>----------------------------------------------------------------------------<|
#> Accuracy by growth form
df_gf <- df_single %>%
  group_by(Species_level_ID, growth_form, cv_model_name, observation_id) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

df_gf_w <- df_single %>%
  group_by(Species_level_ID, growth_form, observation_id) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  )

sink(file.path(dir_stt, "Growth_form_pairwise_wilcox.txt"))
cat("Species-level comparisons:")
pairwise.wilcox.test(
  df_gf_w$Top1_acc, df_gf_w$growth_form,
  p.adjust.method = "holm"
)

cat("\n\nAggregate-level comparisons:")
pairwise.wilcox.test(
  df_gf_w$Top1_acc_hl, df_gf_w$growth_form,
  p.adjust.method = "holm"
)
sink()

file.copy(
  from = file.path(dir_stt, "Growth_form_pairwise_wilcox.txt"),
  to = file.path(dir_stat_online, "Growth_form_pairwise_wilcox.txt")
)

# tmp1 <- df_gf
# tmp1$Accuracy <- tmp1$Top1_acc
# tmp1$Level <- "Species"
# tmp2 <- df_gf
# tmp2$Accuracy <- tmp2$Top1_acc_hl
# tmp2$Level <- "Genus"
#
# df_gf <- rbind(tmp1, tmp2)
# df_gf$combined <- paste(df_gf$Level, df_gf$cv_model_name)


gg_gf_t1 <- ggplot(
  data = df_gf,
  aes(x = growth_form, y = Top1_acc, fill = growth_form)
) +
  geom_boxplot(alpha = 0.7) +
  facet_wrap(~cv_model_name, ncol = length(unique(df_gf$cv_model_name))) +
  theme_bw() +
  scale_fill_manual("Growth form", values = safe_colorblind_palette) +
  ylab("Species-level accuracy") +
  theme(
    legend.position = "none",
    axis.title.x = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank()
  )

gg_gf_hl <- ggplot(
  data = df_gf,
  aes(x = growth_form, y = Top1_acc_hl, fill = growth_form)
) +
  geom_boxplot(alpha = 0.7) +
  facet_wrap(. ~ cv_model_name, ncol = length(unique(df_gf$cv_model_name))) +
  theme_bw() +
  scale_fill_manual("Growth form", values = safe_colorblind_palette) +
  xlab("") +
  ylab("Genus-level accuracy") +
  theme(
    legend.position = "none",
    axis.text.x = element_text(angle = 45, hjust = 1),
    strip.text.x = element_blank()
  )

df_gf_counts <- df_gf[which(df_gf$cv_model_name == "FlorID"), ] %>%
  group_by(growth_form) %>%
  summarise(n_observations = n())

for (i in 1:nrow(df_gf_counts)) {
  set_var(
    paste0("nobs", df_gf_counts$growth_form[i]),
    df_gf_counts$n_observations[i], 0
  )
}

if (save_plots) {
  f_out <- file.path(dir_fig, "Growth_form_accuracy.pdf")
  pdf(file = f_out, height = 5, width = 7.5)
  combined_plot <- grid.arrange(
    gg_gf_t1, gg_gf_hl,
    ncol = 1, heights = c(0.9, 1.1)
  )
  grid.text("Growth form", x = 0.5, y = 0.02, gp = gpar(fontsize = 12))
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}
