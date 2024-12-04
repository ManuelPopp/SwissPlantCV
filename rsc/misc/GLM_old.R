# Create clusters for parametric bootstrapping
(nc <- parallel::detectCores())
cl <- parallel::makeCluster(rep("localhost", nc))

# Number of simulations
N <- 1000

# Set seed
seed <- 42

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
ss$response <- as.numeric(ss$Top1_hl)

#===============================================================================
# Print some general GLM model summaries
for (model in c("florid", "floraincognita", "inaturalist", "plantnet")) {
  glmod <- glm(
    response ~ biogeo_region + habitat_main + Family * plant_organ,
    data = ss[ss$cv_model == model,],
    family = binomial(link = "logit")
  )
  
  aic_select <- MASS::stepAIC(glmod, direction = "both")
  sink(file.path(dir_out, "stat", paste0("aic_glm_", model, ".txt")))
  print(summary(aic_select))
  sink()
}

if (save_tables) {
  sink(file.path(dir_out, "stat", paste0("Factor_combinations.txt")))
  table(ss[which(ss$cv_model == "florid"), c("biogeo_region", "habitat_main")])
  sink()
}

ssfid <- ss[which(ss$cv_model_name %in% c("FlorID", "FlorID vision")),]

glmod <- glm(
  response ~ cv_model + biogeo_region + habitat_main + growth_form * plant_organ,
  data = ssfid,
  family = binomial(link = "logit")
)

#===============================================================================
# Specific tests
#-------------------------------------------------------------------------------
# Recommendations to photographers
## Generalized linear mixed model with interaction
glmm_pp_i <- lme4::glmer(
  response ~ growth_form * plant_organ_name + (1|cv_model_name),
  data = ss, family = binomial(link = "logit"),
  control = lme4::glmerControl(optimizer = "Nelder_Mead")
)
glmm_pp_i_s <- summary(glmm_pp_i)
glmm_pp_i_c <- glmm_pp_i_s$coefficients
row.names(glmm_pp_i_c) <- sub("growth_form", "", row.names(glmm_pp_i_c))
row.names(glmm_pp_i_c) <- sub("plant_organ_name", "", row.names(glmm_pp_i_c))

### Export
sink(file.path(dir_out, "stat", "glmm_growth_form_and_organ_interact.txt"))
cat("Summary GLM\n")
print(glmm_pp_i_s)
cat("\nTest on estimated marginal means\n")
print(test_pp_i)
sink()

out_tab <- test_pp_i[, -c(5, 6)]
out_tab[, 3] <- round(out_tab[, 3], 2)
out_tab[, 4] <- round(out_tab[, 4], 2)
out_tab[, 5] <- as.character(round(out_tab[, 5], 2))

sink(file.path(dir_tab_online, "glmm_growth_form_and_organ_interact.tex"))
write.table(
  out_tab,
  quote = FALSE, row.names = TRUE, col.names = FALSE,
  sep = " & ", eol = "\\\\\n"
)
sink()

x11()
par(mfrow = c(1, 2))
plot(residuals(glmm_pp_i) ~ fitted(glmm_pp_i), main = "residuals v.s. Fitted")
qqnorm(residuals(glmm_pp_i))

#-------------------------------------------------------------------------------
## Generalized linear mixed model without interaction
glmm_pp_a <- lme4::glmer(
  response ~ growth_form + plant_organ_name + (1|cv_model_name) + (1|Name),
  data = ss, family = binomial(link = "logit")
)
glmm_pp_a_s <- summary(glmm_pp_a)

glmm_pp_a_c <- glmm_pp_a_s$coefficients
row.names(glmm_pp_a_c) <- sub("growth_form", "", row.names(glmm_pp_a_c))
row.names(glmm_pp_a_c) <- sub("plant_organ_name", "", row.names(glmm_pp_a_c))

### Export
sink(file.path(dir_out, "stat", "glmm_growth_form_and_organ_no_interact.txt"))
print(glmm_pp_a_c)
sink()

colnames(glmm_pp_a_c)[4] <- "p-value"
for (c in 1:(ncol(glmm_pp_a_c) - 1)) {
  glmm_pp_a_c[, c] <- round(glmm_pp_a_c[, c], 2)
}

p <- as.character(round(glmm_pp_a_c[, ncol(glmm_pp_a_c)], 2))
p[which(glmm_pp_a_c[, ncol(glmm_pp_a_c)] < 0.01)] <- "< 0.01"
glmm_pp_a_c[, ncol(glmm_pp_a_c)] <- p

if (save_tables) {
  sink(file.path(dir_tab_online, "glmm_growth_form_and_organ_no_interact.tex"))
  write.table(
    glmm_pp_a_c,
    quote = FALSE, row.names = TRUE, col.names = FALSE,
    sep = " & ", eol = "\\\\\n"
  )
  sink()
}

x11()
par(mfrow = c(1, 2))
plot(residuals(glmm_pp_a) ~ fitted(glmm_pp_a), main = "residuals v.s. Fitted")
qqnorm(residuals(glmm_pp_a))

# Model comparisons
pboot <- pbkrtest::PBmodcomp(glmm_pp_i, glmm_pp_a, nsim = N, seed = seed, cl = cl)

# Automatic approach from afex (uses pbkrtest::PBmodcomp in "PB" mode)
start <- Sys.time()
mod <- afex::mixed(
  response ~ growth_form + plant_organ_name + (1|cv_model_name),
  data = ss, family = binomial(link = "logit"),
  type = afex::afex_options("type"),
  method = "PB",
  return = "mixed",
  cl = cl,
  control = lme4::glmerControl(optimizer = "bobyqa"),
  args_test = list(nsim = N, seed = seed)
)

end <- Sys.time()
delta <- end - start

#-------------------------------------------------------------------------------
# Performance in biogeographic regions
glm_bg_i <- lme4::glmer(
  response ~ cv_model_name * biogeo_region + (1|growth_form) + (1|plant_organ_name),
  data = ss, family = binomial(link = "logit")
)
glm_bg_i_s <- summary(glm_bg_i)
glm_bg_i_s$coefficients

glm_bg_a <- lme4::glmer(
  response ~ cv_model_name + biogeo_region + (1|growth_form) + (1|plant_organ_name),
  data = ss, family = binomial(link = "logit")
)
glm_bg_a_s <- summary(glm_bg_a)
glm_bg_a_s$coefficients

start <- Sys.time()
mod <- afex::mixed(
  response ~ cv_model_name + biogeo_region + (1|growth_form) + (1|plant_organ_name),
  data = ss, family = binomial(link = "logit"),
  type = afex::afex_options("type"),
  method = "PB",
  return = "mixed",
  cl = cl,
  control = lme4::glmerControl(optimizer = "bobyqa"),
  args_test = list(nsim = N, seed = seed)
)

end <- Sys.time()
delta <- end - start

#-------------------------------------------------------------------------------
# Stop clusters
parallel::stopCluster(cl)