packages <- c("httr", "jsonlite")

for(i in 1:NROW(packages)){
  if(!require(
    packages[i], character.only = TRUE
  )){
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

check_inat <- function(taxon) {
  api_endpoint <- "https://api.inaturalist.org/v1/taxa"
  
  if (is.numeric(taxon)) {
    separator <- "/"
  }else{
    separator <- "?q="
  }
  # Make a GET request
  response <- GET(paste(api_endpoint, gsub(" ", "-", taxon), sep = separator))
  
  # Check the response status code
  status_code <- status_code(response)
  
  if (status_code != 200) {
    stop(paste("Error: Status code", status_code))
  }
  
  # Get the response content
  content <- jsonlite::fromJSON(content(response, "text", encoding = "UTF-8"))
  
  results <- content$results
  
  if (is.numeric(taxon)) {
  return(results$vision)
  
  }else{
    species <- results[, c("id", "name")]
    match <- which(species$name == taxon)
    if (length(match) == 1) {
      return(species$id[match])
    }else{
      return(species)
    }
  }
}

inat_taxon_included <- function(taxon) {
  # Make sure the taxon contains only Genus and epithethon
  taxon_split <- strsplit(taxon, " ")
  taxon <- paste(
    taxon_split[[1]][1:min(2, length(taxon_split[[1]]))],
    collapse = " "
  )
  
  # Get taxon ID
  match <- check_inat(taxon)
  new_taxon <- taxon
  
  while (is.data.frame(match)) {
    print(match)
    cat(paste0("Input: ", taxon, "\n"))
    entry <- readline("Select entry or enter alternative taxon name: ")
    
    if (!is.na(as.numeric(entry))) {
      index <- as.numeric(entry)
      if (index > 1000) {
        selection <- index
      }else{
        new_taxon <- match$name[index]
        selection <- match$id[index]
        
        print(
          paste("Selected entry", entry, "=", match$name[as.numeric(entry)])
          )
      }
      
      confirm <- readline("Continue? [y/n] ")
      
      if (confirm == "y") {
        match <- selection
      }
    }else{
      match <- check_inat(entry)
    }
  }
  
  # Get taxon CV status
  cv <- check_inat(match)
  
  output <- data.frame(
    original = c(taxon),
    alternative = c(new_taxon),
    cv_included = as.logical(cv)
    )
  
  return(output)
}

inat_taxa_included <- function(taxa) {
  for (taxon in taxa) {
    response <- inat_taxon_included(taxon)
    
    if (!exists("output")) {
      output <- response
    }else{
      output <- rbind(output, response)
    }
  }
  
  return(output)
}