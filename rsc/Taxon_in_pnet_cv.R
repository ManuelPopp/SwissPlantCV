packages <- c("httr", "jsonlite", "kewr")

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

check_pnet <- function(api_key) {
  api_endpoint <- "https://my-api.plantnet.org/v2/species?lang=en&type=kt"
  separator <- "&api-key="
  
  # Make a GET request
  response <- GET(paste(api_endpoint, api_key, sep = separator))
  
  # Check the response status code
  status_code <- status_code(response)
  
  if (status_code != 200) {
    stop(paste("Error: Status code", status_code))
  }
  
  # Get the response content
  content <- jsonlite::fromJSON(content(response, "text", encoding = "UTF-8"))
  
  content$full_name <- paste(
    content$scientificNameWithoutAuthor,
    content$scientificNameAuthorship
    )
  
  return(content)
}

pnet_taxa_included <- function(taxa, backbone) {
  in_pnet_bb <- taxa %in% backbone$full_name
  out_df <- data.frame(
    original = taxa,
    alternative = taxa,
    cv_included = in_pnet_bb
    )
  
  for (i in which(!in_pnet_bb)) {
    print(paste("No match for:", taxa[i], "\n"))
    continue <- FALSE
    while(!continue) {
      entry <- readline("Enter official taxon name (from POWO): ")
      confirm <- readline(paste("Continue with", entry, "(y/n): "))
      if (confirm == "y") {
        continue <- TRUE
      }
    }
    
    out_df$alternative[i] <- entry
    out_df$cv_included[i] <- entry %in% backbone$full_name
  }
  
  return(out_df)
}