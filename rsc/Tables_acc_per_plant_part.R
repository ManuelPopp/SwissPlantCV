# Part of Data_analysis.R
# This script only works when imported, no standalone functionality.
#>----------------------------------------------------------------------------<|
#> Data preparation
df_pp <- pp_single %>%
  group_by(cv_model_name, plant_organ) %>%
  summarize(
    Top1_mean = mean(Top1_acc),
    Top1_mean_hl = mean(Top1_acc_hl),
    Top3_mean = mean(Top3_acc),
    Top3_mean_hl = mean(Top3_acc_hl)
  )

pparts <- c("infructescence", "inflorescence", "several", "trunk", "vegetative")
df_pp$plant_organ <- pparts[match(df_pp$plant_organ, c("f", "i", "s", "t", "v"))]

for (i in 3:6) {
  df_pp[, i] <- round(df_pp[, i], 2)
}

#>----------------------------------------------------------------------------<|
#> Top 1 accuracy
df_pp_t1 <- df_pp[
  , c("cv_model_name", "plant_organ", "Top1_mean")
] %>%
  spread("cv_model_name", "Top1_mean")
names(df_pp_t1) <- paste(names(df_pp_t1), "T1")

df_pp_t1_hl <- df_pp[
  , c("cv_model_name", "plant_organ", "Top1_mean_hl")
] %>%
  spread("cv_model_name", "Top1_mean_hl")
names(df_pp_t1_hl) <- paste(names(df_pp_t1_hl), "T1_hl")

df_pp_1 <- cbind(df_pp_t1, df_pp_t1_hl[, -c(1)])
df_pp_1 <- df_pp_1[, c("plant_organ T1", sort(names(df_pp_1)[-1]))]

#>----------------------------------------------------------------------------<|
#> Top 3 accuracy
df_pp_t3 <- df_pp[
  , c("cv_model_name", "plant_organ", "Top3_mean")
] %>%
  spread("cv_model_name", "Top3_mean")
names(df_pp_t3) <- paste(names(df_pp_t3), "T3")

df_pp_t3_hl <- df_pp[
  , c("cv_model_name", "plant_organ", "Top3_mean_hl")
] %>%
  spread("cv_model_name", "Top3_mean_hl")
names(df_pp_t3_hl) <- paste(names(df_pp_t3_hl), "T3_hl")

df_pp_3 <- cbind(df_pp_t3, df_pp_t3_hl[, -c(1)])
df_pp_3 <- df_pp_3[, c("plant_organ T3", sort(names(df_pp_3)[-1]))]

#>----------------------------------------------------------------------------<|
#> Export tables
write.table(
  df_pp_1[, c(1, 2, 3, 4, 5, 6, 9)],
  file = file.path(dir_tab_online, "Plant_parts_t1.tex"),
  sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
  quote = FALSE
)

write.table(
  df_pp_3[, c(1, 2, 3, 4, 5, 6, 9)],
  file = file.path(dir_tab_online, "Plant_parts_t3.tex"),
  sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
  quote = FALSE
)

#>----------------------------------------------------------------------------<|
#> Export dynamic values
cols_a <- seq(2, ncol(df_pp_1), 2)
set_var(
  "mintoponeseveralspec",
  min(df_pp_1[which(df_pp_1[, 1] == "several"), cols_a])
)
set_var(
  "maxtoponeseveralspec",
  max(df_pp_1[which(df_pp_1[, 1] == "several"), cols_a])
)
set_var(
  "mintoponeseveralagg",
  min(df_pp_1[which(df_pp_1[, 1] == "several"), cols_a + 1])
)
set_var(
  "maxtoponeseveralagg",
  max(df_pp_1[which(df_pp_1[, 1] == "several"), cols_a + 1])
)
set_var(
  "mintoponevegetativespec",
  min(df_pp_1[which(df_pp_1[, 1] == "vegetative"), cols_a])
)
set_var(
  "maxtoponevegetativespec",
  max(df_pp_1[which(df_pp_1[, 1] == "vegetative"), cols_a])
)
set_var(
  "mintoponetrunkspec",
  min(df_pp_1[which(df_pp_1[, 1] == "trunk"), cols_a])
)
set_var(
  "fitoponetrunkspec",
  max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 2])
)
set_var(
  "fitoponetrunkagg",
  max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 3])
)
set_var(
  "fidtoponetrunkspec",
  max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 4])
)
set_var(
  "fidtoponetrunkagg",
  max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 5])
)
if (ncol(df_pp_1) == 9) {
  set_var(
    "inattoponetrunkspec",
    max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 6])
  )
  set_var(
    "inattoponetrunkagg",
    max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 7])
  )
} else {
  set_var(
    "inattoponetrunkspec",
    max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 8])
  )
  set_var(
    "inattoponetrunkagg",
    max(df_pp_1[which(df_pp_1[, 1] == "trunk"), 9])
  )
}

set_var(
  "maxtopthreeseveralagg",
  max(df_pp_3[which(df_pp_3[, 1] == "several"), cols_a + 1])
)