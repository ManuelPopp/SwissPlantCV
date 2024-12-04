#!/usr/bin/env Rscript
#>------------------------------------<
##
## Script name: Completed habitats to table
##
## Author: Manuel R. Popp
## Email: manuel.popp@wsl.ch
##
## Date Created: 2023-09-04
##
## ---------------------------
##
## Descripton: Create table and kml file containing sampling location info
## Notes: -
##
#>----------------------------------------------------------------------------<|
#> Install/load packages
packages <- c(
    "rstudioapi", "dplyr", "readxl", "xlsx", "dplyr", "sf", "cols4all",
    "xtable"
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

#>----------------------------------------------------------------------------<|
#> Settings
dir_this_file <- get_file_location()

dir_main <- dirname(dir_this_file)
dir_dat <- file.path(dir_main, "dat")
dir_fig <- file.path(dir_main, "pub", "fig")
dir_tab <- file.path(dir_main, "pub", "tab")
p_habitats_table <- file.path(dir_dat, "Habitats.xlsx")

dir_dbx <- "C:/Users/poppman/Dropbox/Apps/Overleaf/SwissPlantCV"

names_eng <- c(
  "Jura Mountains", "Central Plateau", "Northern Alps", "Western Alps",
  "Eastern Alps", "Southern Alps"
)

#>----------------------------------------------------------------------------<|
#> Main
# Get table of all habitats
habitats <- as.data.frame(readxl::read_excel(p_habitats_table, sheet = 1))

for(i in c(1, 2, 3)){
  habitats[, i] <- as.character(habitats[, i])
}

habitats[is.na(habitats)] <- ""
habitats$ID = apply(habitats[, c(1, 2, 3)], 1, paste, collapse = "")

habitats <- habitats %>%
  group_by(ID) %>%
  summarise(name = unique(Habitat_Sci))

# Correct habitat IDs for 4-digit level IDs
for(i in 1:nrow(habitats)){
  current_habitat_ID <- habitats$ID[i]
  N <- length(which(habitats$ID == current_habitat_ID))
  
  if(N > 1){
    habitats[which(habitats$ID == current_habitat_ID), 1] <-
      as.character(
        paste(as.character(habitats$ID[which(habitats$ID == current_habitat_ID)]),
               seq(1, N), sep = "")
      )
  }
}

habitats[which(habitats$ID == "321"), 1] <- "3211"

habitats[which(habitats$ID == "3314"), 1] <- "3315"
habitats[which(habitats$ID == "3313"), 1] <- "3314"
habitats[which(habitats$ID == "3312"), 1] <- "3313"
habitats[which(habitats$ID == "3311"), 1] <- "3312"

habitats[which(habitats$ID == "3412"), 1] <- "3413"
habitats[which(habitats$ID == "3411"), 1] <- "3412"

habitats[which(habitats$ID == "3422"), 1] <- "3423"
habitats[which(habitats$ID == "3421"), 1] <- "3422"

habitats <- habitats[which(habitats$name != ""),]
habitats[which(habitats$name == "0"), 2] <- c(
  "Adlerfarnflur", "Brombeergestr.", "Kastanienwald", "Laubwald mit immergr. Str."
  )

# Get list of finished habitats
kml_file <- file.path(dir_main, "spl", "Completed_habitats.kml")
biogeo_file <- file.path(
    dir_main, "gis", "shp", "BiogeographischeRegionen",
    "N2020_Revision_BiogeoRegion.shp"
    )

completed <- sf::st_read(kml_file)
biogeo <- sf::st_read(biogeo_file)
regions <- biogeo[1]

crs <- sf::st_crs(biogeo)
completed_LV95 <- sf::st_transform(completed, crs)

joined <- sf::st_join(completed_LV95, regions)

# Add completed releves to habitat list
for(region in unique(joined$RegionNumm)){
  habitats[, ncol(habitats) + 1] <- rep(0, nrow(habitats))
  colnames(habitats)[ncol(habitats)] <- paste0(
    "Region_Nr_", as.character(region)
    )
  }

for(i in 1:nrow(completed)){
  habitat_type <- joined$Description[i]
  region_id <- joined$RegionNumm[i]
  
  i <- which(habitats$ID == habitat_type)
  j <- which(colnames(habitats) == paste0(
    "Region_Nr_", as.character(region_id))
    )
  habitats[i, j] <- habitats[i, j] + 1
}

habitats$Sum <- rowSums(habitats[, c(3:ncol(habitats))])

xlsx::write.xlsx(
  as.data.frame(habitats),
  file = file.path(dir_main, "spl", "Completed_habitats.xlsx"),
  sheetName = "Sheet_1"
  )

habitat_export <- habitats[, c(1, 2, 5, 3, 4, 8, 6, 7, 9)]
names(habitat_export) <- c("ID", "Name", names_eng, "Sum")

print(xtable(habitat_export, type = "latex",
             digits = rep(0, ncol(habitat_export) + 1),
             caption = "Number of sampling plots for each habitat type and biogeographic region. Habitat types were classified following TypoCH. Biogeographic regions were assigned according to the 2022 six-region classification by the Swiss Federal Office for the Environment (FOEN).",
             label = "tab:sampledhabitats"
             ),
      file = file.path(dir_tab, "Sampled_habitats.tex"),
      booktabs = TRUE, sanitize.text.function = identity,
      include.rownames = FALSE,
      caption.placement = "top"
)

# Sampling per region
bioregions <- data.frame(
    Number = unique(regions$RegionNumm),
    Area = NA,
    N = NA
    )

for(i in 1:nrow(bioregions)){
  num <- bioregions$Number[i]
  bioregions$Area[i] <- sum(st_area(biogeo[biogeo$RegionNumm == num,]))
  bioregions$N[i] <- length(which(joined$RegionNumm == num))
}

#bioregions$samples_per_tsd_km2 <- bioregions$N / bioregions$Area * 10^9
bioregions$Name <- names_eng

# Export table
export <- bioregions[, c(4, 2, 3)]#, 4)]
export$Area = round(export$Area / 10^6, 0)

names(export) <- c("Biogeographic region", "Area in km\\textsuperscript{2}", "N")#, "Plots per tsd km\\textsuperscript{2}")
print(xtable(export, type = "latex", digits = c(0, 0, 0, 0),#, 2),
             caption = "Sampling sites per biogeographic region. N is the number of sampling plots within the respective region.",
             label = "tab:samplingbyregion"
             ),
      file = file.path(dir_tab, "Sampling_summary.tex"),
      booktabs = TRUE, sanitize.text.function = identity,
      include.rownames = FALSE,
      caption.placement = "top"
)

file.copy(
    file.path(dir_tab, "Sampling_summary.tex"),
    file.path(dir_dbx, "tab", "Sampling_summary.tex"),
    overwrite = TRUE
    )

# Export map
main_regions <- regions %>%
  group_by(RegionNumm) %>%
  summarise(geometry = sf::st_union(geometry))

outline <- sf::st_union(sf::st_geometry(regions))

cols <- cols4all::c4a("brewer.pastel1", length(unique(main_regions$RegionNumm)))

# I changed the colour palette for the other graphics, so I need to adjust it
# here, too:
safe_colorblind_palette <- c(
  "#88CCEE", "#CC6677", "#DDCC77", "#117733", "#332288", "#AA4499", "#44AA99",
  "#999933", "#882255", "#661100", "#6699CC", "#888888"
)
cols <- safe_colorblind_palette[1:length(unique(main_regions$RegionNumm))]
cols1 <- adjustcolor(cols, alpha.f = 0.15)
cols2 <- c4a("brewer.dark2", length(unique(substr(joined$Description, 1, 1))))
cols2 <- safe_colorblind_palette
col_habitats <- cols2[c(1, 5, 12, 3, 6, 4, 2)]
pch_habitats <- c(0, 4, 3, 5, 1, 2, 6, 7)

plot(
    rep(1, 7) ~ seq(1:7), col = col_habitats, pch = pch_habitats,
     xaxt = "n", cex = 1.2, lwd = 3
    )
axis(
    1, at = seq(1:7),
    labels = c(
      "Water", "Wetlands", "Rocks", "Meadows", "Scrubs", "Forest", "Ruderal"
      )
    )

# Get longitude and latitude axis tick labels (more useful to readers)


plot_axes = FALSE
if (plot_axes) {
  pdf(file = file.path(dir_fig, "Sampling_locations_LV95.pdf"),
      width = 4, height = 3)
  par(mar = c(1.5, 1.5, 0.1, 0.1), cex.axis = 0.75, mgp = c(3, 0.5, 0))
  plot(
    sf::st_geometry(main_regions), main = NA,
    col = cols1[main_regions$RegionNumm], lty = 3, lwd = 0.5,
    axes = TRUE
  )
} else {
  pdf(file = file.path(dir_fig, "Sampling_locations_LV95.pdf"),
      width = 4, height = 2.8)
  par(mar = c(0, 0, 0, 0), mgp = c(3, 0.5, 0))
  plot(
    sf::st_geometry(main_regions), main = NA,
    col = cols1[main_regions$RegionNumm], lty = 3, lwd = 0.5,
    axes = FALSE
  )
  box()
}

plot(sf::st_geometry(outline), add = TRUE, lty = 1, lwd = 1.5)
plot(
  st_geometry(joined), col = col_habitats[
    as.numeric(substr(joined$Description, 1, 1))
    ],
  pch = pch_habitats[as.numeric(substr(joined$Description, 1, 1))],
  lwd = 1.5,
  add = TRUE, cex = 1.2
  )
dev.off()

file.copy(
    file.path(dir_fig, "Sampling_locations_LV95.pdf"),
    file.path(dir_dbx, "fig", "Sampling_locations_LV95.pdf"),
    overwrite = TRUE
)
