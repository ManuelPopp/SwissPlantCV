#!/usr/bin/env Rscript
#>----------------------------------------------------------------------------<?
#> Install/load packages
packages <- c("WorldFlora")

for (i in 1:NROW(packages)) {
  if (!require(packages[i], character.only = TRUE)) {
    install.packages(packages[i])
    library(packages[i], character.only = TRUE)
  }
}

#>----------------------------------------------------------------------------<?
#> Settings
searchstring <- paste(
  as.character(commandArgs(trailingOnly = TRUE)),
  collapse = " "
)

wfo_file <- "../dat/wfo/classification.csv"

synonyms <- WFO.synonyms(searchstring, WFO.file = wfo_file)
synonym <- paste(synonyms[1, 2], synonyms[1, 3])
print(synonym)
