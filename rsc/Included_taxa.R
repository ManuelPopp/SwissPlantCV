# Part of Data_analysis.R
# This script only works when imported, no standalone functionality.
#>----------------------------------------------------------------------------<|
#> Add information on whether a taxon is included in a CV model
# Flora Incognita
florinc_fails <- sort(
  unique(
    df[which(df$cv_model == "floraincognita"), ] %>%
      group_by(Name) %>%
      summarize(matched_once = max(Top3)) %>%
      filter(matched_once < 1) %>%
      pull(Name)
  )
)

# FlorID
florid_fails <- sort(
  unique(
    df[which(df$cv_model == "florid"), ] %>%
      group_by(Name) %>%
      summarize(matched_once = max(Top3)) %>%
      filter(matched_once < 1) %>%
      pull(Name)
  )
)

florid_fails_ids <- sort(
  unique(
    df[which(df$cv_model == "florid"), ] %>%
      group_by(true_taxon_id) %>%
      summarize(matched_once = max(Top3)) %>%
      filter(matched_once < 1) %>%
      pull(true_taxon_id)
  )
)

fid_tbb <- do.call(
  rbind,
  strsplit(
    gsub("\\}", "", gsub("\\{", "", gsub("'", "", strsplit(
      readLines(file.path(dir_main, "dat", "image_taxon_dict.txt")),
      ","
    )[[1]]
    ))),
    ":"
  )
)

fid_tbb[, 1] <- as.numeric(fid_tbb[, 1])

cv_fid <- data.frame(
  original = florid_fails,
  alternative = florid_fails,
  cv_included = florid_fails_ids %in% fid_tbb[, 1])

# iNaturalist
f_inat_table <- file.path(dir_main, "dat", "inat_cv.rda")

if (!file.exists(f_inat_table)) {
  source(file.path(dir_main, "rsc", "Taxon_in_inat_cv.R"))
  inat_fails <- sort(
    unique(
      df[which(df$cv_model == "inaturalist"), ] %>%
        group_by(Name) %>%
        summarize(matched_once = max(Top3)) %>%
        filter(matched_once < 1) %>%
        pull(Name)
    )
  )
  
  cv_inat <- inat_taxa_included(inat_fails)
  cv_inat$original <- inat_fails
  save(cv_inat, file = f_inat_table)
}else{
  load(f_inat_table)
}

# PlantNet
f_pnet_table <- file.path(dir_main, "dat", "pnet_cv.rda")

if (!file.exists(f_pnet_table)) {
  plantnet_fails <- sort(
    unique(
      df[which(df$cv_model == "plantnet"), ] %>%
        group_by(Name) %>%
        summarize(matched_once = max(Top3)) %>%
        filter(matched_once < 1) %>%
        pull(Name)
    )
  )
  
  ## Load PlantNet included taxa via API
  api_key_file <- file.path(dirname(dir_main), "prv", "sec", "PlantNet")
  if (Sys.info()[1] == "Linux") {
    python <- "python3"
  } else {
    python <- "py"
  }
  ak <- system(
    paste(
      python,
      file.path(dir_main, "py3", "misc", "print_key_for_R.py")
    ),
    intern = TRUE
  )
  
  source(file.path(dir_main, "rsc", "Taxon_in_pnet_cv.R"))
  
  pnet_tbb <- check_pnet(ak)
  cv_pnet <- pnet_taxa_included(plantnet_fails, pnet_tbb)
  save(cv_pnet, file = f_pnet_table)
}else{
  load(f_pnet_table)
}

# Add information about CV model
df$cv_included <- rep(TRUE, nrow(df))

## Add info for Flora Incognita
not_in_finc <- c(
  "Taraxacum alpinum aggr.", "Taraxacum officinale aggr.",
  "Hieracium murorum aggr.", "Hieracium prenanthoides aggr.",
  "Centaurea valesiaca (DC.) Jord."
  )

df[
  df$true_taxon_name %in% not_in_finc & df$cv_model == "floraincognita",
]$cv_included <- FALSE

## Add info for FlorID
not_in_fid <- cv_fid$original[!cv_fid$cv_included]
df[
  df$true_taxon_name %in% not_in_fid & df$cv_model %in% c(
    "florid", "florvision"
  ),
]$cv_included <- FALSE

## Add info for iNaturalist
not_in_inat <- cv_inat$original[!cv_inat$cv_included]
df[
  df$true_taxon_name %in% not_in_inat & df$cv_model == "inaturalist",
]$cv_included <- FALSE

## Add info for PlantNet
not_in_pnet <- cv_pnet$original[!cv_pnet$cv_included]
df[
  df$true_taxon_name %in% not_in_pnet & df$cv_model == "plantnet",
]$cv_included <- FALSE

#>----------------------------------------------------------------------------<|
#> Overall: Recognised by at least one plant part or image
#> The figure and table produced in the following paragraph show the best result
#> the CV models achieved per species, i.e., the result they would return if
#> provided with the "best" or most representative image taken of that plant.

# For this analysis, we don't consider lower matches than field ID (usually
# species IDs where an agregate was determined in the field)
df_alt <- df
df_alt[which(df_alt$match_first < 0), "match_first"] <- 0

max_performance <- df_alt %>%
  group_by(cv_model_name, true_taxon_name) %>%
  summarise(
    best_suggestion = min(match_first), cv_included = first(cv_included)
  )

# Set CV model included flag to true where the aggregate is known and the cv
# model returned an ID on aggregate level
max_performance$cv_included[
  which(max_performance$best_suggestion < 5)
] <- TRUE

setwd(file.path(dir_main, "rsc"))
source("Barplot_best_match.R")

# Export figure
f_out <- file.path(dir_fig, "Maximum_scores.pdf")
ggsave(f_out, plot = ideal_gg, width = 5, height = 6, onefile = FALSE)
file.copy(f_out, dir_fig_online, overwrite = TRUE)

write.csv(
  ideal_df,
  file = file.path(dir_main, "out", "Best_match_per_species.csv"),
  row.names = FALSE
)

#-------------------------------------------------------------------------------
# Set variables
florincogagg <- ideal_df$count[
  ideal_df$level == "Aggregate" & ideal_df$cv_model_name == "Flora Incognita"
] / sum(ideal_df$count[ideal_df$cv_model_name == "Flora Incognita"])

set_var("florincogagg", florincogagg * 100, 0)

fidagg <- ideal_df$count[
  ideal_df$level == "Aggregate" & ideal_df$cv_model_name == "FlorID"
] / sum(ideal_df$count[ideal_df$cv_model_name == "FlorID"])

set_var("fidagg", fidagg * 100, 0)

ideal_df_short <- ideal_df %>%
  group_by(cv_model_name, no_cv_model) %>%
  summarise(N = sum(count))

set_var(
  "inatnocv",
  ideal_df_short$N[
    which(
      ideal_df_short$cv_model_name == "iNaturalist" & ideal_df_short$no_cv_model
    )
  ], 0
)

set_var(
  "floridnocv",
  ideal_df_short$N[
    which(
      ideal_df_short$cv_model_name == "FlorID" & ideal_df_short$no_cv_model
    )
  ], 0
)