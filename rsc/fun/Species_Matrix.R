species_matrix <- function(df,
                           taxon.col,
                           sample.col,
                           abundance.col,
                           mode = "abundance",
                           summarise = "mean"){
  #' Creates a presence-absence or abundance matrix from a long tibble
  #' @param df: A tibble or data.frame.
  #' @param taxon.col: A character string indicating the taxon name column.
  #' @param sample.col: A character string indicating the sample ID column.
  #' @param abundance.col: A character string indicating the presense
  #' or abundance data column.
  #' @param mode: Either "abundance" or "pa". Select whether the output is
  #' qualitative or quantitative.
  #' @param summarise: Either "mean" or "sum". Select how values are summarised
  #' in case multiple records exist for some combination of sample ID and taxon
  #' name.
  
  out_long <- tibble(df) %>%
    complete(!!!syms(sample.col), !!!syms(taxon.col)) %>%
    arrange(!!!syms(sample.col), !!!syms(taxon.col)) %>%
    group_by(!!!syms(sample.col), !!!syms(taxon.col)) %>%
    summarise(mean = mean(!!!syms(abundance.col), na.rm = TRUE),
              sum = sum(!!!syms(abundance.col), na.rm = TRUE))
  
  if(mode == "pa"){
    out_long["value"] <- !is.na(out_long["mean"])
  }else{
    if(summarise == "mean"){
      out_long["value"] <- out_long["mean"]
    }else{
      out_long["value"] <- out_long["sum"]
    }
    
    out_long <- out_long %>%
      replace_na(list(value = 0, y = "unknown"))
  }
  
  nr <- nrow(unique(out_long[sample.col]))
  nc <- nrow(unique(out_long[taxon.col]))
  out <- matrix(pull(out_long, "value"),
                nrow = nr,
                ncol = nc,
                byrow = TRUE)
  colnames(out) <- pull(out_long, taxon.col)[1:nc]
  row.names(out) <- unique(pull(out_long, sample.col))
  return(out)
}