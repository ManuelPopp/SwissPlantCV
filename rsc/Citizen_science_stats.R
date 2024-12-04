#!/usr/bin/env Rscript
#>------------------------------------<
##
## Script name: Data analysis
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2024-08-08
##
## ---------------------------
##
## Descripton: Analysis of citizen science data base entries
## Notes: -
##
#>----------------------------------------------------------------------------<|
#> Install/load packages
packages <- c(
  "httr", "jsonlite", "ggplot2", "scales"
)

for (i in 1:NROW(packages)) {
  if (
    !require(packages[i], character.only = TRUE)
  ) {
    install.packages(
      packages[i],
      dependencies = TRUE
    )
    require(
      packages[i],
      character.only = TRUE
    )
  }
}

#>----------------------------------------------------------------------------<|
#> Functions
inat_obs_per_year <- function(taxon = 0) {
  if (taxon == 0) {
    taxon_string <- ""
  } else {
    taxon_string <- paste0("taxon_id=", taxon, "&")
  }
  res = GET(
    paste0(
      "https://api.inaturalist.org/v1/observations/histogram?",
      taxon_string,
      #"created_year=", year,
      "&date_field=created&interval=year"
    )
  )
  
  data = fromJSON(rawToChar(res$content))
  
  return(unlist(data$results[[1]]))
}

#>----------------------------------------------------------------------------<|
#> Observation statistics
## iNaturalist
n_obs <- inat_obs_per_year()
n_plants <- inat_obs_per_year(taxon = 47126)
n_animals <- inat_obs_per_year(taxon = 1)
n_fungi <- inat_obs_per_year(taxon = 47170)
n_other <- n_obs - n_plants - n_animals - n_fungi
y <- as.numeric(sub("-01-01", "", names(n_obs)))

inat_obs <- rbind(
  data.frame(
    year = y, observations = as.numeric(n_plants),
    taxon = rep("Plantae", length(y))
    ),
  data.frame(
    year = y, observations = as.numeric(n_animals),
    taxon = rep("Animalia", length(y))
    ),
  data.frame(
    year = y, observations = as.numeric(n_fungi),
    taxon = rep("Fungi", length(y))
    ),
  data.frame(
    year = y, observations = as.numeric(n_other),
    taxon = rep("Other/undefined", length(y))
    )
  )

inat_obs$taxon <- factor(
  inat_obs$taxon,
  levels = c("Animalia", "Fungi", "Plantae", "Other/undefined")
  )

custom_tick_label <- function(x) {
  str2expression(paste(x, "%*%10^", 7))
}

gg_inat <- ggplot(
  data = inat_obs[which(inat_obs$year > 2007 & inat_obs$year < 2024),],
  aes(x = year, y = observations / 10^7, fill = taxon)
  ) +
  geom_bar(stat = "identity", position = "stack") +
  xlab("Year") +
  ylab("Number of additional records") +
  theme_bw() +
  scale_x_continuous(breaks = c(2010, 2015, 2020)) +
  scale_y_continuous(labels = custom_tick_label) +
  scale_fill_manual(
    name = "Kingdom",
    values = c("#CC6677", "#DDCC77", "#117733", "#88CCEE")
    ) +
  theme(
    legend.position = c(0, 1),
    legend.justification = c(0, 1),
    legend.background = element_blank()#,
    #text = element_text(size = 16)
  )

if (save_plots) {
  f_out <- file.path(dir_fig, "iNat_observations.pdf")
  pdf(file = f_out, height = 5, width = 7)
  gg_inat
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

## Info Flora
tbb <- read.csv(
  file.path(dir_dat, "Taxonomic_backbone_wHier_2022.csv"),
  sep = ",", header = TRUE
) %>%
  dplyr::select(
    ID, Species_level_ID, Name, Genus, Family, Order, Class, Phylum, COMECO_ID
  )

fungi_bb <- read.table(
  file.path(dir_dat, "InfoFLora", "Species_taxonomy_fungi.csv"),
  header = TRUE
  )

info_obs <- read.csv(
  file.path(dir_dat, "InfoFLora", "All_Imgs_4_Manuel_2024_08_09.csv")
) %>%
  dplyr::group_by(Observation_id) %>%
  dplyr::summarise(
    Taxon = first(na.omit(Taxon)),
    Date = first(na.omit(Date)),
    Taxon_id = first(na.omit(Taxon_id))
  ) %>%
  dplyr::mutate(
    Year = format(as.Date(Date, format = "%Y-%m-%d"),"%Y"),
    is_plant = Taxon_id %in% tbb$ID,
    is_fungi = Taxon %in% fungi_bb$original_name
    ) %>%
  dplyr::mutate(is_undefined = !is_plant & !is_fungi)

info_obs$taxon <- NA
info_obs$taxon[which(info_obs$is_plant)] <- "Plantae"
info_obs$taxon[which(info_obs$is_fungi)] <- "Fungi"
info_obs$taxon[which(info_obs$is_undefined)] <- "Other/undefined"
info_sum <- info_obs %>%
  dplyr::group_by(taxon, Year) %>%
  dplyr::summarise(Count = n())

info_sum$taxon <- factor(
  info_sum$taxon, levels = c("Fungi", "Plantae", "Other/undefined")
  )
info_sum$Year <- as.numeric(info_sum$Year)

custom_tick_label <- function(x) {
  str2expression(paste(x, "%*%10^", 4))
}

gg_info <- ggplot(
  data = info_sum[which(info_sum$Year > 2009 & info_sum$Year < 2024),],
  aes(x = Year, y = Count / 10000, fill = taxon)
) +
  geom_bar(stat = "identity", position = "stack") +
  xlab("Year") +
  ylab("Number of additional records") +
  theme_bw() +
  scale_x_continuous(breaks = c(2010, 2015, 2020)) +
  scale_y_continuous(labels = custom_tick_label) +
  scale_fill_manual(
    name = "Kingdom",
    values = c("#DDCC77", "#117733", "#88CCEE")
  ) +
  theme(
    legend.position = c(0, 1),
    legend.justification = c(0, 1),
    legend.background = element_blank()#,
    #text = element_text(size = 16)
  )

if (save_plots) {
  f_out <- file.path(dir_fig, "InfoFlora_observations.pdf")
  pdf(file = f_out, height = 5, width = 7)
  gg_info
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

## Combined plot
if (save_plots) {
  f_out <- file.path(dir_fig, "Citizen_science.pdf")
  pdf(f_out, width = 10, height = 5)
  grid.arrange(
    gg_inat +
      xlab("(a) iNaturalist"),
    gg_info +
      theme(
        #axis.title.x = element_blank(),
        axis.title.y = element_blank()
      ) +
      xlab("(b) Info Flora"),
    ncol = 2, bottom = "Citizen science platform",
    widths = c(1, 0.92)
  )
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}