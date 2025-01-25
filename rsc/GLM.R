# Create clusters for parametric bootstrapping
(nc <- parallel::detectCores())
cl <- parallel::makeCluster(rep("localhost", nc))

# Number of simulations
N <- 1000

# Set seed
seed <- 42

# Level of ID ("species" or "agg")
level <- "species"

#===============================================================================
# Create a subset that contains only single image requests
ss <- df_single[
  which(
    !df_single$habitat_main %in% c(
      "Glaciers, rock, rubble and scree", "Aquatic"
    )
  ),
]

ss$habitat_main <- factor(ss$habitat_main)

if (level == "species") {
  ss$response <- as.numeric(ss$Top1)
} else {
  ss$response <- as.numeric(ss$Top1_hl)
}

#===============================================================================
# Specific tests
#-------------------------------------------------------------------------------
# Recommendations to photographers
models <- list()
signif_pairw_diffs <- list()
times <- c()
i <- 1
all_models <- unique(ss$cv_model_name)
for (model in sort(all_models[! all_models %in% c("FlorID vision")])) {
  start <- Sys.time()
  mod <- glm(
    response ~ growth_form * plant_organ_name,
    data = ss[ss$cv_model_name == model,],
    family = binomial(link = "logit")
  )
  
  em <- emmeans::emmeans(
    mod, ~ growth_form * plant_organ_name, type = "response"
    )
  prs <- pairs(em, reverse = TRUE)
  sprs <- summary(prs, adjust = "tukey")
  # Note: negative z ratios indicate the mean of the first level is [z.ratio]
  # standard deviations below the mean of the second level, positive values indi-
  # cate higher means for the second factor (first factor / second)
  
  models[[i]] <- mod
  signif_pairw_diffs[[i]] <- sprs[which(sprs[, 7] < 0.05),]
  names(signif_pairw_diffs)[i] <- model
  end <- Sys.time()
  delta <- end - start
  times <- c(times, delta)
  i <- i + 1
}

#-------------------------------------------------------------------------------
# Differences that were significant for all models
common_diffs <- function(x) {
  alphabetical <- function(x_i, mode = "commons") {
    contrasts <- x_i$contrast
    splitted <- strsplit(as.vector(contrasts), " / ")
    sorted <- lapply(splitted, sort)
    pasted <- lapply(sorted, FUN = paste, collapse = " - ")
    
    return(unlist(pasted))
  }
  
  get_values <- function(x_i, s_contrasts, commons, c = 6) {
    x_i[
      which(mapply(FUN = "!=", x_i$contrast, sub("-", "/", s_contrasts))), c
    ] <- x_i[
      which(mapply(FUN = "!=", x_i$contrast, sub("-", "/", s_contrasts))), c
    ] * (-1)
    out <- x_i[match(commons, s_contrasts), c]
    
    return(out)
  }
  
  s_contrasts <- lapply(x, FUN = alphabetical)
  commons <- Reduce(intersect, s_contrasts)
  commons <- commons[order(commons)]
  
  z_ratios <- mapply(
    FUN = get_values, x, s_contrasts,
    MoreArgs = list(commons = commons, c = 6)
  )
  z_ratios <- z_ratios[, order(colnames(z_ratios))]
  
  p_values <- mapply(
    FUN = get_values, x, s_contrasts,
    MoreArgs = list(commons = commons, c = 7)
    )
  p_values <- p_values[, order(colnames(p_values))]
  
  out <- list(commons, z_ratios, p_values)
  names(out) <- c("common_contrasts", "z_ratios", "p_values")
  
  return(out)
}

common_signif <- common_diffs(signif_pairw_diffs)
common_signif$z_ratios <- signif_digits(common_signif$z_ratios, 3)
common_signif$p_values <- reduce_p(common_signif$p_values)

emm_comp_tab <- do.call(cbind, common_signif)

if (save_tables) {
  sink(file.path(dir_tab_online, "Organ_growth_form_glm.tex"))
  write.table(
    emm_comp_tab,
    quote = FALSE, row.names = FALSE, col.names = FALSE,
    sep = " & ", eol = "\\\\\n"
  )
  sink()
}

#------------------------------------------------------------------------------
# Evaluation for FlorID
mod <- glm(
  response ~ growth_form * plant_organ_name,
  data = ss[ss$cv_model_name == "FlorID",],
  family = binomial(link = "logit")
)

em <- emmeans::emmeans(
  mod, ~ growth_form * plant_organ_name, type = "response"
)

simp <- pairs(em, simple = "each")
summarised <- simp["simple contrasts for plant_organ_name"][[1]]
t <- tempfile()
sink(file = t)
summary(summarised, adjust = "tukey")
sink()

tables <- list()
i <- 0
for (line in readLines(t)) {
  if (startsWith(line, "growth_form")) {
    i <- i + 1
    tab_name <- sub(":", "", sub("growth_form = ", "", line))
  } else if (startsWith(line, " contrast")) {
    tables[[i]] <- data.frame(
      Contrast = c(), OddsRatio = c(), SE = c(), df = c(), null = c(),
      zRatio = c(), pValue = c()
    )
    names(tables)[i] <- tab_name
  } else if (startsWith(line, " ")) {
    line <- gsub("[ ]+", "_", line)
    values <- str_split(line, "_")[[1]]
    
    if (!(grepl("Trunk", line) & tab_name != "Woody")) {
      tables[[i]] <- rbind(
        tables[[i]],
        data.frame(
          Contrast = c(paste(values[c(2, 3, 4)], collapse = " ")),
          OddsRatio = c(values[5]), SE = c(values[6]), df = c(values[7]),
          null = c(values[8]), zRatio = c(values[9]), pValue = c(values[10])
        )
      )
    }
  }
}

tables <- lapply(
  tables,
  FUN = function(x) {return(x[which(x$zRatio != "NA"),])}
  )

for (i in 1:length(tables)) {
  write.table(
    tables[[i]][, c(1, 6, 7)], file = file.path(
      dir_tab_online, paste0("Pair_parts_", names(tables[i]), ".tex")
      ),
    quote = FALSE, row.names = FALSE, col.names = FALSE, sep = " & ",
    eol = "\\\\\n"
    )
}

#-------------------------------------------------------------------------------
# Performance in biogeographic regions
# Automated approach from afex (uses pbkrtest::PBmodcomp in "PB" mode)
barplot(
  n ~ id,
  data = ss[ss$cv_model_name == model,] %>%
    dplyr::group_by(biogeo_region, growth_form) %>%
    dplyr::tally() %>%
    dplyr::ungroup() %>%
    mutate(id = row_number()),
  main = paste(
    "Number of observations per combination of biogeographical region,",
    "growth form, and habitat type."
  ), cex.main = 0.5
)

ggplot(
  data = ss[ss$cv_model_name == model & ss$plant_organ != "t",] %>%
    dplyr::group_by(biogeo_region, plant_organ) %>%
    dplyr::tally() %>%
    dplyr::ungroup() %>%
    mutate(id = row_number()),
  aes(x = plant_organ, y = n, fill = plant_organ, group = biogeo_region)
) +
  geom_bar(stat = "identity") +
  facet_grid(.~biogeo_region)

ggplot(
  data = ss[ss$cv_model_name == model & ss$plant_organ != "t",] %>%
    dplyr::group_by(biogeo_region, growth_form) %>%
    dplyr::tally() %>%
    dplyr::ungroup() %>%
    mutate(id = row_number()),
  aes(x = growth_form, y = n, fill = growth_form, group = biogeo_region)
) +
  geom_bar(stat = "identity") +
  facet_grid(.~biogeo_region)

# Observation frequency is obviously strongly different for factor level combi-
# nations. The particular species found in each region are a property inherent
# to the region. Similarly, growth form might be viewed as something that
# is typical for the biogeographic region. I chose to correct for plant organ,
# because imbalances in the sampling frequency of plant organs may not only
# be related to the species within each region, but also, e.g., to the time of
# year at which I visited a region.

start <- Sys.time()
mod <- afex::mixed(
  response ~ cv_model_name * biogeo_region + (1|plant_organ),
  data = ss[which(ss$plant_organ != "t"),], family = binomial(link = "logit"),
  type = afex::afex_options(type = 3),
  method = "PB",
  return = "mixed",
  cl = cl,
  control = lme4::glmerControl(optimizer = "bobyqa"),
  args_test = list(nsim = N, seed = seed)
)

end <- Sys.time()
delta <- end - start
save(mod, file = file.path(dir_out, "GLMM.Rdata"))

coefs <- summary(mod)$coefficients

for (i in 1:length(levels(ss$cv_model_name))) {
  row.names(coefs) <- gsub(
    paste0("cv_model_name", i), levels(ss$cv_model_name)[i], row.names(coefs)
    )
}

for (i in 1:length(levels(ss$biogeo_region))) {
  row.names(coefs) <- gsub(
    paste0("biogeo_region", i), levels(ss$biogeo_region)[i], row.names(coefs)
  )
}

biogeotab <- data.frame(
  Factor = row.names(coefs),
  Estimate = signif_digits(coefs[, 1], 2),
  StdError = signif_digits(coefs[, 2], 2),
  zValue = signif_digits(coefs[, 3], 3),
  pValue = reduce_p(coefs[, 4])
)

#biogeotab <- biogeotab[order(biogeotab$Factor),]

if (save_tables) {
  sink(file.path(dir_tab_online, "Biogeo_model_glmm.tex"))
  write.table(
    biogeotab,
    quote = FALSE, row.names = FALSE, col.names = FALSE,
    sep = " & ", eol = "\\\\\n"
  )
  sink()
}

# Pairwise comparisons
emm <- emmeans::emmeans(
  mod, ~ cv_model_name * biogeo_region, type = "response"
)

prsm <- summary(pairs(emm,adjust = "tukey"))
prsms <- as.data.frame(prsm[prsm$p.value < 0.05,])
comparisons <- do.call(rbind, str_split(prsms$contrast, " / "))
comparisons[which(prsms$z.ratio < 0),] <- comparisons[
  which(prsms$z.ratio < 0), c(2, 1)
  ]

combined <- data.frame(
  Contrast0 = comparisons[, 1],
  Contrast1 = comparisons[, 2],
  SE = prsms$SE,
  zRatio = abs(prsms$z.ratio),
  pValue = prsms$p.value
)

combined <- combined[order(combined$Contrast0, combined$Contrast1), ]

emm_df <- as.data.frame(emm)
emm_df <- emm_df %>%
  dplyr::mutate(
    biogeo_en = dplyr::recode(
      biogeo_region,
      "Alpennordflanke" = "Northern Alps",
      "Alpensüdflanke" = "Southern Alps",
      "Jura" = "Jura Mountains",
      "Mittelland" = "Central Plateau",
      "Östliche Zentralalpen" = "Eastern Alps",
      "Westliche Zentralalpen" = "Western Alps"
    )
  )

ggglmm <- ggplot(
  data = emm_df,
  aes(
    x = cv_model_name, y = prob,
    colour = cv_model_name, fill = cv_model_name, shape = cv_model_name,
    group = biogeo_en
    )
  ) +
  geom_errorbar(aes(ymin = asymp.LCL, ymax = asymp.UCL), width = 0.5) +
  geom_point() +
  ylab("Probability of correct first suggestion") +
  theme_bw() +
  facet_grid(~ biogeo_en) +
  scale_color_manual(
    values = safe_colorblind_palette
    ) +
  scale_shape_manual(values = c(15, 21, 24, 5, 25)) +
  labs(
    colour = "Computer vision model:",
    fill = "Computer vision model:",
    shape = "Computer vision model:"
    ) +
  theme(
    axis.title.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.text.x = element_blank(),
    legend.position = "bottom"
  )

if (save_plots) {
  f_out <- file.path(dir_fig, "GLMM_biogeo_model.pdf")
  pdf(file = f_out, height = 4, width = 9)
  print(ggglmm)
  dev.off()
  file.copy(f_out, dir_fig_online, overwrite = TRUE)
}

#-------------------------------------------------------------------------------
# Stop clusters
parallel::stopCluster(cl)