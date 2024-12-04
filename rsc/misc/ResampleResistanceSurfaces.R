require(terra)
require(tools)

path <- "L:/poppman/rca/dat/res"
template_file <- "L:/poppman/rca/dat/pat/Kerngebiete_trocken_coarse.tif"
files <- list.files(path, pattern = ".tif", full.names = TRUE)

for (f in files) {
  basename <- tools::file_path_sans_ext(f)
  
  if (!endsWith(basename, "_coarse")) {
    outname <- paste0(basename, "_coarse.tif")
    
    raster <- terra::rast(f)
    template <- terra::rast(template_file)
    
    terra::resample(
      raster,
      template,
      method = "average",
      filename = outname,
      overwrite = TRUE,
      wopt = list(
        datatype = "INT2S",
        gdal = c("COMPRESS=DEFLATE", "TFW=YES")
      )
      )
  }
}
