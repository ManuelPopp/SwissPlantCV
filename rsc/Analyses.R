#!/usr/bin/Rscript
#>------------------------------------<?
##
## Script name: Flowering periods
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2023-06-06
##
## ---------------------------
##
## Notes: Add flowering periods to habitats data
##
##
#>------------------------------------<?

#>----------------------------------------------------------------------------<?
#> Install/load packages
packages <- c("tidyr", "tibble", "rstudioapi", "WorldFlora", "readxl")

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
dir_this_file <- get_file_location()
dir_main = dirname(dir_this_file)
dir_dat <- file.path(dir_main, "dat")

wfo_bb <- file.path(dir_dat, "wfo", "classification.csv")

#>----------------------------------------------------------------------------<?
#> Load data
responses <- read_excel(file.path(dir_main, "out", "Responses.xlsx"), sheet = 1)

# Show all the fuzzy matches, which included those at infraspecifc level
e1 <- WFO.match(spec.data = c("Ranunculus ficaria L."), WFO.file = wfo_bb, counter=1, Fuzzy.min=FALSE, Fuzzy.shortest=FALSE, verbose=TRUE)
WFO.one(e1, spec.name = "FIcaria verna")
