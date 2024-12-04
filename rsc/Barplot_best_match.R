# Part of Data_analysis.R
# This script only works when imported, no standalone functionality.
#>----------------------------------------------------------------------------<|
#> Data preparation
# max_performance$best_suggestion[
#   which(max_performance$best_suggestion > 1 & !max_performance$cv_included)
#   ] <- max_performance$best_suggestion[
#     which(max_performance$best_suggestion > 1 & !max_performance$cv_included)
#   ] + 1

max_performance <- max_performance[
  which(max_performance$cv_model_name != "FlorID vision"),
]

ideal_df <- max_performance %>%
  group_by(cv_model_name, best_suggestion, cv_included) %>%
  summarise(count = n())

# flevels <- c(
#   "Subspecies",
#   "Species",
#   "Aggregate",
#   "Same aggregate",
#   "Same agg. no CV",
#   "Same genus",
#   "Same genus no CV",
#   "No match",
#   "No match no CV"
#   )

flevels <- c(
  "Subspecies",
  "Species",
  "Aggregate",
  "Same aggregate",
  "Same genus",
  "No match"
)

ideal_df$level <- flevels[match(
  ideal_df$best_suggestion, c(-1, 0, 1, 5, 10, 100)
)]
# ideal_df$level <- flevels[match(
#   ideal_df$best_suggestion, c(-1, 0, 1, 5, 6, 10, 11, 100, 101)
# )]

ideal_df$level <- factor(ideal_df$level, levels = rev(flevels))
ideal_df$no_cv_model <- !(ideal_df$cv_included)

#>----------------------------------------------------------------------------<|
#> Figures
# ideal_gg <- ggplot(
#   data = ideal_df, aes(x = cv_model_name, y = count, fill = level)
#   ) +
#   geom_bar(position = "stack", stat = "identity") +
#   xlab("Identification provider") +
#   ylab("Number of species") +
#   scale_fill_manual(name = legend_title, values = safe_colorblind_palette) +
#   guides(title = legend_title, overwrite.aes = list(fill = c()))

ideal_gg <- ggplot(
  data = ideal_df,
  aes(
    x = cv_model_name,
    y = count,
    fill = level,
    alpha = as.factor(cv_included)
    ),
  pattern = "stripe", pattern_angle = 0
) +
  geom_bar(position = "stack", stat = "identity") +
  xlab("Identification provider") +
  ylab("Number of species") +
  scale_fill_manual("Best match", values = safe_colorblind_palette) +
  scale_alpha_manual("CV model included", values = c(0.5, 1)) +
  scale_y_break(c(100, 400)) +
  scale_x_discrete(
    labels = c("Flora\nIncognita", "FlorID", "iNaturalist", "Pl@ntNet")
    ) +
  theme_bw()

ideal_gg

# require("tidyr")
# reshaped <- ideal_df %>%
#   group_by(cv_model_name, best_suggestion) %>%
#   summarise(n = count) %>%
#   spread(cv_model_name, n, fill = 0)
# 
# safe_colorblind_rgb <- col2rgb(safe_colorblind_palette)
# barplot_colours <- safe_colorblind_rgb[, c(4, 8, 11, 11, 5, 5, 2, 2)]
# barplot_colours <- rgb(
#   t(barplot_colours),
#   alpha = c(255, 255, 255, 150, 255, 150, 255, 150),
#   maxColorValue = 255
#   )
# 
# barplot(as.matrix(reshaped)[, 2:ncol(reshaped)], col = barplot_colours)
# legend("topright", legend = c(1, 2, 3, 4), density = 16, angle = 45, fill = "red")