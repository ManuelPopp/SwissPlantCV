# Part of Data_analysis.R
# This script only works when imported, no standalone functionality.
#>----------------------------------------------------------------------------<|
#> Data preparation
observation_level_single <- df_single %>%
  group_by(observation_id, cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  ) %>%
  gather(
    key = "Measure", value = "Accuracy", -observation_id, -cv_model_name
    ) %>%
  mutate(Aggregate = stringr::str_ends(Measure, "_hl")) %>%
  mutate(Top1 = stringr::str_starts(Measure, "Top1"))

observation_level_multi <- df_multi %>%
  group_by(observation_id, cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  ) %>%
  gather(
    key = "Measure", value = "Accuracy", -observation_id, -cv_model_name
  ) %>%
  mutate(Aggregate = stringr::str_ends(Measure, "_hl")) %>%
  mutate(Top1 = stringr::str_starts(Measure, "Top1"))

#>----------------------------------------------------------------------------<|
#> Statistics
osdfsp <- observation_level_single[
  which(observation_level_single$Top1 & !observation_level_single$Aggregate),
]
osdfsp <- osdfsp[order(osdfsp$observation_id),]

osdfag <- observation_level_single[
  which(observation_level_single$Top1 & observation_level_single$Aggregate),
]
osdfag <- osdfag[order(osdfag$observation_id),]

# Multiple paired Wilcoxon signed rank tests
## Single, no aggregates
osdfspwt <- pairwise.wilcox.test(
  osdfsp$Accuracy, osdfsp$cv_model_name,
  paired = TRUE, alternative = "two.sided",
  p.adjust.method = "holm"
)

### Assumptions: Distribution of differences symmetrical
models <- unique(osdfsp$cv_model_name)
combinations <- combn(models, 2)

pdf(
  file.path(dir_etc, "Pairwise_differences_observation_level_noagg.pdf"),
  width = 15, height = 25
)
r <- ceiling(sqrt(ncol(combinations)))
c <- ceiling(ncol(combinations) / r)
par(mfrow = c(r, c), mar = c(3, 3, 3, 0))

for (i in 1:ncol(combinations)) {
  combi <- combinations[, i]
  differences <- osdfsp[
    which(osdfsp$cv_model_name == combi[1]),
  ][["Accuracy"]] -
    osdfsp[which(osdfsp$cv_model_name == combi[2]),][["Accuracy"]]
  hist(differences, main = paste(combi, collapse = " vs "), cex = 0.5)
}
dev.off()

## Single, aggregates allowed
osdfagwt <- pairwise.wilcox.test(
  osdfag$Accuracy, osdfag$cv_model_name,
  paired = TRUE, alternative = "two.sided",
  p.adjust.method = "holm"
)

models <- unique(osdfag$cv_model_name)
combinations <- combn(models, 2)

pdf(
  file.path(dir_etc, "Pairwise_differences_observation_level_agg.pdf"),
  width = 15, height = 25
)
r <- ceiling(sqrt(ncol(combinations)))
c <- ceiling(ncol(combinations) / r)
par(mfrow = c(r, c), mar = c(3, 3, 3, 0))

for (i in 1:ncol(combinations)) {
  combi <- combinations[, i]
  differences <- osdfag[
    which(osdfag$cv_model_name == combi[1]),
  ][["Accuracy"]] -
    osdfsp[which(osdfag$cv_model_name == combi[2]),][["Accuracy"]]
  hist(differences, main = paste(combi, collapse = " vs "), cex = 0.5)
}
dev.off()

## Print results
sink(file.path(dir_stt, "Observation_level_pairwise_wilcox.txt"))
cat("Species-level comparisons:")
print(osdfspwt)
cat("\n\nAggregate-level comparisons:")
print(osdfagwt)
sink()

file.copy(
  from = file.path(dir_stt, "Observation_level_pairwise_wilcox.txt"),
  to = file.path(dir_stat_online, "Observation_level_pairwise_wilcox.txt")
)

## Export results to LaTeX tables
osdfspwt_df <- data.frame(reduce_p(as.matrix(data.frame(osdfspwt$p.value)))) %>%
  stats::setNames(names(data.frame(osdfspwt$p.value))) %>%
  dplyr::mutate(model = row.names(data.frame(osdfspwt$p.value))) %>%
  dplyr::select(model, dplyr::everything()) %>%
  dplyr::mutate_all(~ replace(., is.na(.), "{-}"))

osdfagwt_df <- data.frame(reduce_p(as.matrix(data.frame(osdfagwt$p.value)))) %>%
  stats::setNames(names(data.frame(osdfagwt$p.value))) %>%
  dplyr::mutate(model = row.names(data.frame(osdfagwt$p.value))) %>%
  dplyr::select(model, dplyr::everything()) %>%
  dplyr::mutate_all(~ replace(., is.na(.), "{-}"))

if (save_tables) {
  write.table(
    osdfspwt_df,
    file = file.path(dir_tab_online, "Obs_pair_Wilcox_spp.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )
  write.table(
    osdfagwt_df,
    file = file.path(dir_tab_online, "Obs_pair_Wilcox_agg.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )
}

## Non significant differences
nonsignifnoagg <- osdfspwt$p.value > 0.05
nonsignifagg <- osdfagwt$p.value > 0.05

cv_mods <- rep(
  sort(unique(c(row.names(nonsignifnoagg), colnames(nonsignifnoagg)))),
  each = 2
)

used_letters <- 0
used_cletters <- 0
lettering <- rep("", length(cv_mods))
for (i in 1:nrow(nonsignifnoagg)) {
  for (j in 1:ncol(nonsignifnoagg)) {
    # No agg.
    if (is.na(nonsignifnoagg[i, j])) {
      nonsignifnoagg[i, j] <- FALSE
    }
    
    if (nonsignifnoagg[i, j]) {
      used_cletters <- used_cletters + 1
      lettering[
        which(cv_mods == row.names(nonsignifnoagg)[i])[1]
      ] <- paste0(
        lettering[
          which(cv_mods == row.names(nonsignifnoagg)[i])[1]
        ],
        LETTERS[used_cletters]
      )
      
      lettering[
        which(cv_mods == colnames(nonsignifnoagg)[j])[1]
      ] <- paste0(
        lettering[
          which(cv_mods == colnames(nonsignifnoagg)[j])[1]
        ],
        LETTERS[used_cletters]
      )
    }
    # Agg. allowed
    if (is.na(nonsignifagg[i, j])) {
      nonsignifagg[i, j] <- FALSE
    }
    
    if (nonsignifagg[i, j]) {
      used_letters <- used_letters + 1
      lettering[
        which(cv_mods == row.names(nonsignifagg)[i])[2]
      ] <- paste0(
        lettering[
          which(cv_mods == row.names(nonsignifagg)[i])[2]
        ],
        letters[used_letters]
      )
      
      lettering[
        which(cv_mods == colnames(nonsignifagg)[j])[2]
      ] <- paste0(
        lettering[
          which(cv_mods == colnames(nonsignifagg)[j])[2]
        ],
        letters[used_letters]
      )
    }
  }
}

#>----------------------------------------------------------------------------<|
#> Figures
## Single
observation_level_single$labels <- lettering[
  match(
    paste(
      observation_level_single$cv_model_name,
      observation_level_single$Aggregate
      ),
    paste(cv_mods, rep(c(FALSE, TRUE), length(cv_mods) / 2))
    )
  ]

gg_obslvl_single <- ggplot(
  data = observation_level_single[which(observation_level_single$Top1),],
  aes(x = cv_model_name, y = Accuracy, fill = Aggregate)
) +
  geom_boxplot() +
  stat_summary(
    fun = function(x) max(x, na.rm = TRUE),
    geom = "text",
    aes(label = labels, group = Aggregate),
    position = position_dodge(width = 0.8),
    vjust = -0.5,
    show.legend = FALSE
  ) +
  xlab("Identification provider") +
  ylab("Top 1 accuracy") +
  theme_bw() +
  theme(legend.position = "None")

gg_obslvl_single

gg_obslvl_single_v <- ggplot(
  data = observation_level_single[which(observation_level_single$Top1),],
  aes(x = cv_model_name, y = Accuracy, fill = Aggregate)
) +
  geom_violin() +
  geom_boxplot(width = 0.9, alpha = 0) +
  xlab("Identification provider") +
  ylab("Top 1 accuracy") +
  theme_bw()

## Multi
gg_obslvl_multi <- ggplot(
  data = observation_level_multi[which(observation_level_multi$Top1),],
  aes(x = cv_model_name, y = Accuracy, fill = Aggregate)
) +
  geom_boxplot() +
  xlab("Identification provider") +
  ylab("Top 1 accuracy") +
  theme_bw()

gg_obslvl_multi

#>----------------------------------------------------------------------------<|
#> Tables
observation_level_single_summary <- df_single %>%
  group_by(observation_id, cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  ) %>%
  group_by(cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1_acc)),
    Top3_acc = mean(as.numeric(Top3_acc)),
    Top1_acc_hl = mean(as.numeric(Top1_acc_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_acc_hl))
  )

observation_level_multi_summary <- df_multi %>%
  group_by(observation_id, cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  ) %>%
  group_by(cv_model_name) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1_acc)),
    Top3_acc = mean(as.numeric(Top3_acc)),
    Top1_acc_hl = mean(as.numeric(Top1_acc_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_acc_hl))
  )
