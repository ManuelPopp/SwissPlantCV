# Part of Data_analysis.R
# This script only works when imported, no standalone functionality.
#>----------------------------------------------------------------------------<|
#> Data preparation
habitat_level_single <- df_single %>%
  group_by(observation_id, cv_model_name, habitat) %>%
  summarise(
    Top1_acc = mean(as.numeric(Top1)),
    Top3_acc = mean(as.numeric(Top3)),
    Top1_acc_hl = mean(as.numeric(Top1_hl)),
    Top3_acc_hl = mean(as.numeric(Top3_hl))
  ) %>%
  group_by(cv_model_name, habitat) %>%
  summarise(
    Top1_acc = mean(Top1_acc),
    Top3_acc = mean(Top3_acc),
    Top1_acc_hl = mean(Top1_acc_hl),
    Top3_acc_hl = mean(Top3_acc_hl)
  ) %>%
  gather(
    key = "Measure",
    value = "Accuracy",
    -cv_model_name, -habitat
  ) %>%
  mutate(Aggregate = stringr::str_ends(Measure, "_hl")) %>%
  mutate(Top1 = stringr::str_starts(Measure, "Top1"))

habitat_level_single <- habitat_level_single[habitat_level_single$Top1,]

#>----------------------------------------------------------------------------<|
#> Statistics
hbdfsp <- habitat_level_single[
  which(habitat_level_single$Top1 & !habitat_level_single$Aggregate),
]
hbdfsp <- hbdfsp[order(hbdfsp$habitat),]

hbdfag <- habitat_level_single[
  which(habitat_level_single$Top1 & habitat_level_single$Aggregate),
]
hbdfag <- hbdfag[order(hbdfag$habitat),]

# Multiple paired Wilcoxon signed rank tests
## Single, no aggregates
hbdfspwt <- pairwise.wilcox.test(
  hbdfsp$Accuracy, hbdfsp$cv_model_name,
  paired = TRUE, alternative = "two.sided",
  p.adjust.method = "holm"
)

### Assumptions: Distribution of differences symmetrical
models <- unique(hbdfsp$cv_model_name)
combinations <- combn(models, 2)

pdf(
  file.path(dir_etc, "Pairwise_differences_habitat_level_noagg.pdf"),
  width = 15, height = 25
)
r <- ceiling(sqrt(ncol(combinations)))
c <- ceiling(ncol(combinations) / r)
par(mfrow = c(r, c), mar = c(3, 3, 3, 0))

for (i in 1:ncol(combinations)) {
  combi <- combinations[, i]
  differences <- hbdfsp[
    which(hbdfsp$cv_model_name == combi[1]),
  ][["Accuracy"]] -
    hbdfsp[which(hbdfsp$cv_model_name == combi[2]),][["Accuracy"]]
  hist(differences, main = paste(combi, collapse = " vs "), cex = 0.5)
}
dev.off()

## Single, aggregates allowed
hbdfagwt <- pairwise.wilcox.test(
  hbdfag$Accuracy, hbdfag$cv_model_name,
  paired = TRUE, alternative = "two.sided",
  p.adjust.method = "holm"
)

models <- unique(hbdfag$cv_model_name)
combinations <- combn(models, 2)

pdf(
  file.path(dir_etc, "Pairwise_differences_habitat_level_agg.pdf"),
  width = 15, height = 25
)
r <- ceiling(sqrt(ncol(combinations)))
c <- ceiling(ncol(combinations) / r)
par(mfrow = c(r, c), mar = c(3, 3, 3, 0))

for (i in 1:ncol(combinations)) {
  combi <- combinations[, i]
  differences <- hbdfag[
    which(hbdfag$cv_model_name == combi[1]),
  ][["Accuracy"]] -
    hbdfsp[which(hbdfag$cv_model_name == combi[2]),][["Accuracy"]]
  hist(differences, main = paste(combi, collapse = " vs "), cex = 0.5)
}
dev.off()

## Print results
sink(file.path(dir_stt, "Habitat_level_pairwise_wilcox.txt"))
cat("Species-level comparisons:")
print(hbdfspwt)
cat("\n\nAggregate-level comparisons:")
print(hbdfagwt)
sink()

file.copy(
  from = file.path(dir_stt, "Habitat_level_pairwise_wilcox.txt"),
  to = file.path(dir_stat_online, "Habitat_level_pairwise_wilcox.txt")
)

## Export results to LaTeX tables
hbdfspwt_df <- data.frame(reduce_p(as.matrix(data.frame(hbdfspwt$p.value)))) %>%
  stats::setNames(names(data.frame(hbdfspwt$p.value))) %>%
  dplyr::mutate(model = row.names(data.frame(hbdfspwt$p.value))) %>%
  dplyr::select(model, dplyr::everything()) %>%
  dplyr::mutate_all(~ replace(., is.na(.), "{-}"))

hbdfagwt_df <- data.frame(reduce_p(as.matrix(data.frame(hbdfagwt$p.value)))) %>%
  stats::setNames(names(data.frame(hbdfagwt$p.value))) %>%
  dplyr::mutate(model = row.names(data.frame(hbdfagwt$p.value))) %>%
  dplyr::select(model, dplyr::everything()) %>%
  dplyr::mutate_all(~ replace(., is.na(.), "{-}"))

if (save_tables) {
  write.table(
    hbdfspwt_df,
    file = file.path(dir_tab_online, "Hab_pair_Wilcox_spp.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )
  write.table(
    hbdfagwt_df,
    file = file.path(dir_tab_online, "Hab_pair_Wilcox_agg.tex"),
    sep = " & ", eol = "\\\\\n", col.names = FALSE, row.names = FALSE,
    quote = FALSE
  )
}

## Non significant differences
nonsignifnoagg <- hbdfspwt$p.value > 0.05
nonsignifagg <- hbdfagwt$p.value > 0.05

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
habitat_level_single$labels <- lettering[
  match(
    paste(
      habitat_level_single$cv_model_name,
      habitat_level_single$Aggregate
    ),
    paste(cv_mods, rep(c(FALSE, TRUE), length(cv_mods) / 2))
  )
]

gg_hablvl_single <- ggplot(
  data = habitat_level_single,
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
  theme(
    legend.position = "None",
    axis.text.x = element_text(size = 11)
  )

gg_hablvl_single
