p <- "D:/switchdrive/PlantApp/out/Responses.xlsx"
require("readxl")

results <- read_excel(p, sheet = 2)
sampled <- results$image_files

sampled_images <- list()
for(s in 1:length(sampled)){
  x <- c(strsplit(sampled[s], "\\\\|[^[:print:]]")[[1]])[c(2, 3, 4)]
  sampled_images[[s]] <- x
}

df <- as.data.frame(do.call(rbind, sampled_images))
names(df) <- c("releve", "observation", "image")

r <- "D:/switchdrive/PlantApp/spl/Releve_table.xlsx"
planned <- as.data.frame(read_excel(r, sheet = 2))
planned <- planned[which(planned$include == "TRUE"),]

for(p in 1:nrow(planned)){
  releve_id <- planned$id[p]
  image_files <- list.files(file.path("N:/prj/COMECO/img", releve_id),
                            "*/*.jpg", full.names = FALSE, recursive = TRUE)
  
  for(image_file in image_files){
    splitted <- c(strsplit(image_file, "/")[[1]])
    
    obs <- splitted[1]
    img <- splitted[2]
    
    subs <- which(df$releve == as.character(releve_id) &
                    df$observation == as.character(obs) &
                    df$image == as.character(img))
    
    if(length(subs) == 0){
      print("Error")
      print(releve_id)

    }else{
      a <- 0
    }
  }
}
