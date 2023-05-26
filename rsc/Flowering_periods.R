#!/usr/bin/Rscript
#>------------------------------------<?
##
## Script name: Flowering periods
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2023-04-18
##
## ---------------------------
##
## Notes: Add flowering periods to habitats data
##
##
#>------------------------------------<?

#>----------------------------------------------------------------------------<?
#> Install/load packages
packages <- c("readxl", "tidyr", "tibble", "dplyr", "rstudioapi", "ggplot2",
              "egg")
for(i in 1:NROW(packages)){
  if(!require(packages[i], character.only = TRUE)){
    install.packages(packages[i])
    library(packages[i], character.only = TRUE)
  }
}

#>----------------------------------------------------------------------------<?
#> Functions
get_file_location <-  function(){
  this_file <- commandArgs() %>% 
    tibble::enframe(name = NULL) %>%
    tidyr::separate(col = value,
                    into = c("key", "value"), sep = "=", fill = "right") %>%
    dplyr::filter(key == "--file") %>%
    dplyr::pull(value)
  
  if (length(this_file) == 0)
  {
    this_file <- rstudioapi::getSourceEditorContext()$path
  }
  return(dirname(this_file))
}

#>----------------------------------------------------------------------------<?
#> Settings
dir_rsc <- get_file_location()
dir_main <- dirname(dir_rsc)
dir_dat <- file.path(dir_main, "dat")
dir_fig <- file.path(dir_main, "fig")

#>----------------------------------------------------------------------------<?
#> Load data
## Load habitat list
dir_habitats <- file.path(dir_dat, "Habitats.xlsx")
habitats <- readxl::read_excel(dir_habitats, sheet = 1, col_names = TRUE)
habitats$Habitat_Sci[habitats$Habitat_Sci == "0"] <- NA

## Load flowering dates
dir_floweringperiods <- file.path(dir_dat, "Flowering_periods.xlsx")
flowering <- readxl::read_excel(dir_floweringperiods, sheet = 1, cell_cols("G:W"))

## Load observation data
dir_obs <- file.path(dir_dat, "Single_obs.csv")
observations <- read.table(dir_obs, sep = ",", header = TRUE,
                           colClasses = c(rep("NULL", 8), "character", "NULL"))

species_single <- as.vector(unlist(unique(observations[1])))

dir_obs <- file.path(dir_dat, "Observed_habitats_Apr2023.csv")
observations <- read.table(dir_obs, sep = ",", header = TRUE,
                           colClasses = c(rep("NULL", 16), "character", "NULL"))

species_habitat <- as.vector(unlist(unique(observations[1])))

observed_species <- as.vector(unlist(union(species_single, species_habitat)))

#>----------------------------------------------------------------------------<?
#> Combine data
char_specs <- habitats[habitats$Charakterart == 1, ]

char_specs$flowering_from <- rep(NA, nrow(char_specs))
char_specs$flowering_to <- rep(NA, nrow(char_specs))
char_specs$in_data <- rep(NA, nrow(char_specs))

for(i in 1:nrow(char_specs)){
  species_name <- char_specs$Species[i]
  
  if(species_name %in% flowering$scientific_name_DE){
    char_specs$flowering_from[i] <- flowering$flowering_period_from[
      flowering$scientific_name_DE == species_name
      ][1]
    char_specs$flowering_to[i] <- flowering$flowering_period_to[
      flowering$scientific_name_DE == species_name
    ][1]
  }
  
  char_specs$in_data[i] <- species_name %in% observed_species
}

#>----------------------------------------------------------------------------<?
#> Plot
habitats$Habitat_Sci[which(is.na(habitats$Habitat_Sci))] <-
  habitats$Habitat_Ger[which(is.na(habitats$Habitat_Sci))]

char_specs$Habitat_Sci[which(is.na(char_specs$Habitat_Sci))] <-
  char_specs$Habitat_Ger[which(is.na(char_specs$Habitat_Sci))]

char_specs <- char_specs %>%
  drop_na("flowering_from") %>%
  drop_na("flowering_to")

habitats <- as.data.frame(habitats)
char_specs <- as.data.frame(char_specs)

habitat_types <- unique(habitats$Habitat_Sci)

length(habitat_types)

par(mfrow = c(10, 16))

plot_list = list()
for(h in habitat_types){
  subs <- char_specs[char_specs$Habitat_Sci == h, c("Species", "flowering_from",
                                                "flowering_to", "in_data")]
  subs$flowering_from <- as.numeric(subs$flowering_from)
  subs$flowering_to <- as.numeric(subs$flowering_to)
  subs$Species <- factor(subs$Species)
  
  gg <- ggplot(data = subs, aes(x = Species)) +
    geom_errorbar(aes(ymin = flowering_from, ymax = flowering_to,
                      alpha = in_data)) +
    scale_alpha_discrete(range = c(0.5, 1)) +
    coord_flip() +
    xlab(element_blank()) +
    scale_y_continuous(name = element_blank(),
                     breaks = seq(1, 12), labels = as.character(seq(1, 12)),
                     limits = c(1, 12)) +
    theme_bw() +
    theme(legend.position = "None") +
    scale_color_manual(values = c("green")) +
    ggtitle(h)
  
  plot_list[[h]] <- gg
}

pdf(file = file.path(dir_fig, "Flowering_periods.pdf"), width = 8, height = 400)
#layout(mat = matrix(rep(seq(1:160), each = 2), ncol = 10, byrow = TRUE),
#       heights = rep(2, 160), widths = rep(3, 160))
egg::ggarrange(plots = plot_list, ncol = 1)
dev.off()

