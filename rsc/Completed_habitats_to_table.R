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
    "rstudioapi", "dplyr", "readxl", "xlsx", "dplyr", "sf",# "cols4all",
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
dir_fig <- file.path(dir_main)
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
kml_file <- file.path(dir_main, "dat", "Completed_habitats.kml")
biogeo_file <- file.path(
    dir_main, "dat", "BioGeoRegionen", "BiogeographischeRegionen",
    "N2020_Revision_BiogeoRegion.shp"
    )

if (exists("df")) {
  completed <- df %>%
    mutate(
      geometry = stringr::str_remove_all(location, "[()]"),
      lat = as.numeric(stringr::str_split_fixed(geometry, ", ", 2)[,1]),
      lon = as.numeric(stringr::str_split_fixed(geometry, ", ", 2)[,2])
    ) %>%
    dplyr::group_by(releve_id) %>%
    dplyr::summarise(
      Name = first(releve_id), Description = first(habitat),
      lat = first(lat),
      lon = first(lon)
    ) %>%
    sf::st_as_sf(coords = c("lon", "lat"), crs = 4326)
} else {
  completed <- sf::st_read(kml_file)
}

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

print(
  xtable(
    habitat_export, type = "latex",
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
print(
  xtable(
    export, type = "latex", digits = c(0, 0, 0, 0),#, 2),
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
  dplyr::group_by(RegionNumm) %>%
  dplyr::summarise(geometry = sf::st_union(geometry))

outline <- sf::st_union(sf::st_geometry(regions))

#cols <- cols4all::c4a("brewer.pastel1", length(unique(main_regions$RegionNumm)))

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
#pch_habitats <- c(0, 4, 3, 5, 1, 2, 6, 7)
pch_habitats <- c(15, 4, 3, 18, 16, 17, 25, 7)
cex_dict <- c(
  "15" = 1,
  "4" = 0.7,
  "3" = 0.7,
  "18" = 1.2,
  "16" = 1,
  "17" = 0.9,
  "25" = 0.7,
  "6" = 0.7,
  "7" = 1
)

plot(
    rep(1, 7) ~ seq(1:7), col = col_habitats, bg = col_habitats,
    pch = pch_habitats, xaxt = "n", cex = cex_dict, lwd = 1
    )
axis(
    1, at = seq(1:7),
    labels = c(
      "Water", "Wetlands", "Rocks", "Meadows", "Scrubs", "Forest", "Ruderal"
      )
    )

# Get non-overlapping label positions-------------------------------------------

## Function to generate non-overlapping labels
# optimise_label_positions <- function(
#     points, label_diameter = 12000, max_distance = 20000
#     ) {
#   label_radius <- label_diameter / 2
#   clusters <- sf::st_buffer(points, dist = label_radius) %>%
#     sf::st_union() %>%
#     sf::st_cast("POLYGON")
#   
#   # Sort decreasing so the ones with fewer points are clipped by
#   # the ones with more points.
#   clusters <- clusters[
#     order(lengths(sf::st_intersects(clusters, points)), decreasing = TRUE),
#     ]
#   
#   search_buffers <- sf::st_buffer(
#     clusters, dist = max_distance - label_diameter
#     ) %>%
#     sf::st_difference()
#   
#   # Loop through buffers. Start with the small ones and resize them
#   # in case they contain only one point.
#   out <- sf::st_sfc(crs = sf::st_crs(points)) %>%
#     sf::st_cast("POINT") %>%
#     sf::st_sf()
#   
#   cluster_df <- data.frame()
#   for (i in length(search_buffers):1) {
#     buffer <- search_buffers[i, ]
#     
#     idx_points <- which(sf::st_intersects(points, buffer, sparse = FALSE))
#     n_points <- length(idx_points)
#     cluster_df <- rbind(
#       cluster_df, data.frame(buff_id = rep(i, n_points), point_id = idx_points)
#     )
#     
#     if (n_points == 1) {
#       anchor_points <- sf::st_intersection(points, buffer)
#       search_buffers[i] <- sf::st_buffer(
#         anchor_points, dist = label_radius * 1.25
#         )
#       sf::st_crs(anchor_points) <- sf::st_crs(points)
#       new_points <- sf::st_cast(anchor_points, "POINT") %>% sf::st_sf()
#       if (any(sf::st_is_empty(new_points))) {
#         new_points <- new_points[-which(sf::st_is_empty(new_points)), ]
#       }
#       out <- rbind(out, new_points)
#     } else {
#       cluster <- sf::st_intersection(clusters, buffer)
#       outlines <- sf::st_cast(buffer, "LINESTRING") %>%
#         sf::st_difference(
#           search_buffers[-i, ] %>%
#             sf::st_union()
#         ) %>%
#         st_cast("LINESTRING")
#       
#       seg_lengths <- as.numeric(sf::st_length(outlines))
#       tot_length <- sum(seg_lengths)
#       n_per_seg <- round(n_points / tot_length * seg_lengths)
#       
#       while (sum(n_per_seg) < n_points) {
#         max_idx <- which(seg_lengths == max(seg_lengths))
#         n_per_seg[max_idx] <- n_per_seg[max_idx] + 1
#         seg_lengths[max_idx] <- 0
#       }
#       
#       while (sum(n_per_seg) > n_points) {
#         max_idx <- which(n_per_seg == max(n_per_seg))
#         n_per_seg[max_idx] <- n_per_seg[max_idx] - 1
#       }
#       
#       for (j in 1:length(outlines)) {
#         outline <- outlines[[j]]
#         N <- n_per_seg[j]
#         anchor_points <- sf::st_line_sample(outline, n = N, type = "regular")
#         sf::st_crs(anchor_points) <- sf::st_crs(points)
#         new_points <- sf::st_cast(anchor_points, "POINT") %>% sf::st_sf()
#         if (any(sf::st_is_empty(new_points))) {
#           new_points <- new_points[-which(sf::st_is_empty(new_points)), ]
#         }
#         out <- rbind(out, new_points)
#       }
#     }
#   }
#   
#   # Get index of closest point
#   out$join_id <- rep(NA, nrow(out))
#   for (i in 1:length(search_buffers)) {
#     in_idxs <- cluster_df$point_id[which(cluster_df$buff_id == i)]
#     opt_idxs <- which(cluster_df$buff_id == i)
#     
#     in_to_match <- points[in_idxs, ]
#     opt_to_match <- out[opt_idxs, ]
#     
#     distances <- sf::st_distance(opt_to_match, in_to_match)
#     max_order <- order(
#       apply(X = distances, MARGIN = 1, FUN = min, na.rm = TRUE),
#       decreasing = FALSE
#       )
#     distances_remaining <- distances
#     idxs <- c()
#     for (j in max_order) {
#       if (!is.null(ncol(distances_remaining))) {
#         idx <- which(distances[j,] == min(distances_remaining[j,]))
#         idy <- which(distances_remaining[j,] == min(distances_remaining[j,]))
#         distances_remaining <- distances_remaining[, -idy]
#       } else {
#         idx <- which(!1:ncol(distances) %in% idxs)
#       }
#       
#       idxs <- c(idxs, idx)
#     }
#     out$join_id[opt_idxs] <- in_idxs[idxs]
#   }
#   return(out)
# }
# 
# optimised <- optimise_label_positions(
#   points = sf::st_geometry(joined),
#   label_diameter = 12000, max_distance = 20000
#   )
# optimised <- optimised[order(optimised$join_id),]
# optimised$Description <- joined$Description
# 
# callouts <- list()
# for (i in 1:nrow(optimised)) {
#   start <- sf::st_coordinates(optimised[i, ])
#   end <- sf::st_coordinates(joined[i, ])
#   line <- sf::st_linestring(rbind(start[, c(1, 2)], end[, c(1, 2)]))
#   callouts[[i]] <- line
# }
# 
# callouts <- sf::st_sfc(callouts)
# sf::st_crs(callouts) <- sf::st_crs(joined)

## Newer version: Arrange clustered locations in grids
grid_label_positions <- function(
    points, label_diameter = 8000, spacing = 5000, rotate = c()
) {
  label_radius <- label_diameter / 2
  clusters <- sf::st_buffer(points, dist = label_radius) %>%
    sf::st_union() %>%
    sf::st_cast("POLYGON")
  
  cluster_df <- data.frame()
  for (i in 1:length(clusters)) {
    cluster <- clusters[i, ]
    centroid <- sf::st_centroid(cluster)
    idx_points <- which(sf::st_intersects(points, cluster, sparse = FALSE))
    n_points <- length(idx_points)
    
    if (!i %in% rotate) {
      rows <- floor(sqrt(n_points))
      cols <- ceiling(n_points / rows)
    } else {
      cols <- floor(sqrt(n_points))
      rows <- ceiling(n_points / cols)
    }
    
    left <- sf::st_coordinates(centroid)[1] - spacing * (cols - 1) / 2
    top <- sf::st_coordinates(centroid)[2] + spacing * (rows - 1) / 2
    
    df_grid <- expand.grid(
      x = (0:(cols - 1)) * spacing + left,
      y = top - (0:(rows - 1)) * spacing
    )[1:n_points, ]
    
    df_grid$Description <- sort(points$Description[idx_points])
    
    cluster_df <- rbind(cluster_df, df_grid)
  }
  
  grid <- sf::st_as_sf(
    cluster_df, coords = c("x", "y"), crs = sf::st_crs(points)
  )
  return(grid)
}

optimised <- grid_label_positions(
  points = joined,
  label_diameter = 8000, spacing = 7000, rotate = c(6, 13, 21, 28, 29)
)
#-------------------------------------------------------------------------------

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
    col = cols1[main_regions$RegionNumm], lty = 1, lwd = 0.5,
    axes = FALSE
  )
  box()
}

#plot(callouts, col = "gray", add = TRUE)
idxs <- as.numeric(substr(optimised$Description, 1, 1))
lwds <- rep(0, length(idxs))
lwds[which(idxs %in% c(2, 3))] <- 1
plot(
  sf::st_geometry(optimised),
  col = col_habitats[idxs],
  bg = col_habitats[idxs],
  pch = pch_habitats[idxs],
  lwd = lwds,
  add = TRUE,
  cex = cex_dict[
    as.character(pch_habitats[as.numeric(substr(optimised$Description, 1, 1))])
    ] * 0.7
  )
dev.off()

file.copy(
    file.path(dir_fig, "Sampling_locations_LV95.pdf"),
    file.path(dir_dbx, "fig", "Sampling_locations_LV95.pdf"),
    overwrite = TRUE
)
