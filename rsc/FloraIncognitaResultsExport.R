florincog <- df[which(df$cv_model == "floraincognita" & df$match_first > 1),]

other_models <- c()
n_other_models_correct <- c()
for (i in 1:nrow(florincog)) {
  file <- florincog$image_files[i]
  sset <- df[which(df$image_files == file & df$cv_model != "floraincognita"),]
  other_models <- c(other_models, paste(sset$first, collapse = " + "))
  n_other_models_correct <- c(
    n_other_models_correct, sum(sset$match_first < 10)
    )
}

florincog$other_models <- other_models
florincog$n_other_models_correct <- n_other_models_correct

florincog$files <- gsub(
  "N__prj_COMECO_img_", "", gsub("[^0-9A-Za-z.;]", "_", florincog$image_files)
  )

florincog$image_files <- gsub("[^0-9A-Za-z.:_;]", "/", florincog$image_files)
main <- "C:/Users/poppman/Desktop/FloraIncognita"

write.csv(
  florincog[, c(
    2, 8, 9, 11, 12, 13, 14, 15, 41, 36, 37, 38
    )], file = file.path(main, "info.csv"), row.names = FALSE)

for (i in 1:nrow(florincog)) {
  in_file <- florincog$image_files[i]
  if (file.exists(in_file)){
    out_file <- file.path(main, florincog$files[i])
    file.copy(in_file, out_file)
  }
}