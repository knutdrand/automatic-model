# Model Improvement Metrics Log

This file tracks model iterations and their evaluation metrics.

## Metrics Tracked
- **RMSE**: Root Mean Square Error (lower is better)
- **MAE**: Mean Absolute Error (lower is better)
- **CRPS**: Continuous Ranked Probability Score (lower is better)
- **Cov 10-90**: Coverage within 10th-90th percentile (target: ~80%)
- **Cov 25-75**: Coverage within 25th-75th percentile (target: ~50%)

---

## Iteration Log

| Commit | Model | RMSE | MAE | CRPS | Cov 10-90 | Cov 25-75 | Notes |
|--------|-------|------|-----|------|-----------|-----------|-------|
| (baseline) | LinearRegression + Poisson | 4.99 | 3.48 | 2.15 | 59.6% | 41.2% | Initial darts model with climate covariates |

---

## Detailed Iteration Notes

### Baseline (2024-12-10)
- **Model**: darts LinearRegressionModel
- **Features**: rainfall, mean_temperature (12 lags each)
- **Uncertainty**: Poisson sampling from point predictions
- **Issues**: Coverage too low - uncertainty is overconfident
- **Next**: Try negative binomial for overdispersion
