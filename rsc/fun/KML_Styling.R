#>----------------------------------------------------------------------------<¦
#> Install/load packages
packages <- c("sf", "xml2", "plotKML", "lubridate")
for(i in 1:NROW(packages)){
  if(!require(packages[i], character.only = TRUE)){
    install.packages(packages[i])
    library(packages[i], character.only = TRUE)
  }
}

rgb_to_kml_aged <- function(colour, date){
  this_year <- as.numeric(format(Sys.Date(), "%Y"))
  col <- hex2kml(
    rgb(
      col2rgb(colour)[1],
      col2rgb(colour)[2],
      col2rgb(colour)[3],
      alpha = 255 - 10 * (
        this_year - lubridate::year(date)
      )^(1 - 0.005 * (
        this_year - lubridate::year(date)
      )
      ),
      maxColorValue = 255
    )
  )
  return(col)
}

write_formattet_kml <- function(layer,
                                file_path,
                                name_field,
                                descr_field,
                                colour_by,
                                colour_scheme = NA){
  #' Save a Simple Features object as KML with custom colours and alpha.
  #' Alpha is set proportional to the age (in years) of a point with a date
  #' attribute.
  #' @param layer: An object of type Simple Features (sf).
  #' @param file_path: Path of the output KML file.
  #' @param name_field: Name of the column containing item names.
  #' @param descr_field: Name of the column containing information which shall
  #' be kept in the output KML file, or a vector of item descriptions.
  #' @param colour_by: Name of the column containing integer values based on
  #' which layer items are colored.
  #' @param colour_scheme: Vector of colour values (must contain at least as
  #' many elements as the maximum value of the "colour_by" parameter column).
  
  ## Header
  head_attr <- c("http://www.opengis.net/kml/2.2")
  names(head_attr) <- "xmlns"
  
  ## Set pin colours
  if(length(colour_by) == 1){
    if(is.numeric(layer[[colour_by]])){
      cols <- colour_scheme[layer[[colour_by]]]
    }else{
      cols <- layer[[colour_by]]
    }
  }else{
    if(is.numeric(colour_by)){
      cols <- colour_scheme[colour_by]
    }else{
      cols <- colour_by
    }
  }
  
  ## Set pin style
  ICOURL <- "http://maps.google.com/mapfiles/kml/paddle/wht-blank.png"
  
  default_attr <- c("#default")
  names(default_attr) <- "id"
  
  ## Create raw KML
  dir.create(dirname(file_path))
  sf::st_write(sf::st_as_sf(layer) %>%
                 sf::st_transform(4326) %>%
                 select(Name = !!as.name(name_field)),
               file_path,
               driver = "kml",
               delete_dsn = TRUE)
  
  ## Read KML
  kml_file <- xml2::read_xml(file_path)
  
  ## Set pin colours
  kml_file %>%
    xml2::xml_ns_strip() %>%
    xml2::xml_find_all("//Placemark") %>%
    xml2::xml_add_child("Style") %>%
    xml2::xml_find_all("//Style") %>%
    xml2::xml_add_child("IconStyle") %>%
    xml2::xml_find_all("//IconStyle") %>%
    xml2::xml_add_child(cols, .value = "color")
  
  ## Set pin style
  kml_file %>%
    xml2::xml_ns_strip() %>%
    xml2::xml_find_all("//IconStyle") %>%
    xml2::xml_add_child("Icon") %>%
    xml2::xml_find_all("//Icon") %>%
    xml2::xml_add_child(ICOURL, .value = "href")
  
  ## Add descriptions
  if(length(descr_field) == 1){
    descriptions <- layer[[descr_field]]
  }else{
    descriptions <- descr_field
  }
  
  kml_file %>%
    xml2::xml_find_all("//Placemark") %>%
    xml2::xml_add_child(descriptions, .value = "description", .where = 2)
  
  ## Write header line (this step comes last, since
  ## it re-introduces stripped namespace)
  kml_file %>%
    xml2::xml_find_all("//kml") %>%
    xml2::xml_set_attrs(head_attr)
  
  xml2::write_xml(kml_file, file_path)
}