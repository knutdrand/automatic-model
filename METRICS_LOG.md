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
| e29e3b5 | LinearRegression + NegBin | 6.31 | 4.00 | 2.00 | 68.4% | 53.6% | Negative binomial with estimated dispersion |

---

## Detailed Iteration Notes

### Baseline (2024-12-10)
- **Model**: darts LinearRegressionModel
- **Features**: rainfall, mean_temperature (12 lags each)
- **Uncertainty**: Poisson sampling from point predictions
- **Issues**: Coverage too low - uncertainty is overconfident
- **Next**: Try negative binomial for overdispersion

### v1.1.0 - Negative Binomial (2024-12-10)
- **Model**: darts LinearRegressionModel
- **Features**: rainfall, mean_temperature (12 lags each)
- **Uncertainty**: Negative binomial with dispersion estimated from training residuals
- **Changes**:
  - Estimate overdispersion during training using Var(Y) = mu + mu^2/r formula
  - Use negative binomial distribution instead of Poisson for sampling
  - Clamp dispersion between 1.0 and 100.0
- **Results**:
  - CRPS improved: 2.15 → 2.00 (-7%)
  - Coverage 10-90 improved: 59.6% → 68.4% (+8.8pp, closer to 80% target)
  - Coverage 25-75 improved: 41.2% → 53.6% (+12.4pp, now close to 50% target!)
  - RMSE/MAE got worse - trade-off for better calibration
- **Next**: Add seasonal features to improve point predictions

### v1.2.0 - Seasonal Features (2024-12-10)
- **Model**: darts LinearRegressionModel
- **Features**: rainfall, mean_temperature + Fourier seasonal features (sin/cos of month, 1st and 2nd harmonics)
- **Uncertainty**: Negative binomial with dispersion estimated from training residuals
- **Changes**:
  - Added `_add_seasonal_features()` function for Fourier encoding
  - 4 new covariates: month_sin, month_cos, month_sin2, month_cos2
  - First harmonic captures annual cycle, second captures semi-annual patterns
- **Dataset**: ewars_weekly.csv (different from previous - 17 locations, 301 weeks)
- **Results** (new dataset, not directly comparable):
  - RMSE: 6.99
  - MASE: 0.57 (good - below 1.0 beats seasonal naive)
  - Coverage[0.9]: 50.6% (target 90% - still underconfident)
- **Issues**:
  - GAP-004 discovered: Published chap-core incompatible with chapkit API
  - Workaround: Use local chap-core from source
- **Next**: Try more advanced darts models (TBATS, Prophet, etc.)

### v1.3.0 - Dispersion Calibration Attempt (2024-12-10)
- **Model**: darts LinearRegressionModel with dispersion_scale parameter
- **Changes**:
  - Added `dispersion_scale` config parameter (default 0.1)
  - Scales down dispersion to widen prediction intervals
- **Results**:
  - Coverage[0.9]: 51.9% (still ~50%, unchanged)
  - ND: 0.76 (high normalized deviation)
- **Analysis**:
  - Coverage doesn't improve with wider variance - problem is systematic underprediction
  - Model's point predictions are biased low (ND = 76%)
  - Need better point predictions, not just wider intervals
- **Next**: Try different darts models or feature engineering
