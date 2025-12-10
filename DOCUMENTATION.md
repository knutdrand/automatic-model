# Building CHAP-Compatible Models: A Complete Guide

This guide documents how to use **chapkit**, **chap-python-sdk**, and **chap-core** together to build, test, and evaluate spatio-temporal disease prediction models.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Model Development Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREATE           2. TEST              3. EVALUATE            │
│  ┌──────────┐       ┌──────────────┐     ┌────────────────┐     │
│  │ chapkit  │  ───▶ │ chap-python- │ ───▶│   chap-core    │     │
│  │  init    │       │     sdk      │     │   evaluate2    │     │
│  └──────────┘       └──────────────┘     └────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Create a New Model with chapkit

### Initialize Project

```bash
cd your-project-directory
uvx chapkit init my-model --template ml
cd my-model
```

This creates:
- `main.py` - FastAPI service with model runner
- `pyproject.toml` - Dependencies
- `Dockerfile` - Container build file

### Implement Your Model

Edit `main.py` to implement:

1. **Configuration** (pydantic model):
```python
class MyModelConfig(BaseConfig):
    lags: int = 12
    n_samples: int = 100
```

2. **Training function**:
```python
async def on_train(
    config: MyModelConfig,
    data: DataFrame,
    geo: FeatureCollection | None = None,
) -> Any:
    df = data.to_pandas()
    # Train your model here
    return {"model": trained_model}
```

3. **Prediction function**:
```python
async def on_predict(
    config: MyModelConfig,
    model: Any,
    historic: DataFrame,
    future: DataFrame,
    geo: FeatureCollection | None = None,
) -> DataFrame:
    # Generate predictions with samples
    # IMPORTANT: Return format with sample_0, sample_1, etc. columns
    return DataFrame.from_pandas(result_df)
```

### Critical: Output Format

Predictions MUST have this format:

```
time_period | location | sample_0 | sample_1 | sample_2 | ...
2019-01-21  | Bokeo    | 1.2      | 3.4      | 5.6      | ...
```

NOT this (will fail):
```
time_period | location | samples
2019-01-21  | Bokeo    | [1.2, 3.4, 5.6, ...]
```

### Handling Data Issues

#### Issue: String columns instead of numeric
```python
def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = ["rainfall", "mean_temperature", "disease_cases"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
```

#### Issue: Weekly date ranges
```python
def _parse_time_period(time_str: str) -> pd.Timestamp:
    if "/" in str(time_str):
        start_date = time_str.split("/")[0]
        return pd.to_datetime(start_date)
    return pd.to_datetime(time_str)
```

## Step 2: Test with chap-python-sdk

### Add to Dependencies

```toml
[dependency-groups]
dev = [
    "chap-python-sdk",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[tool.uv.sources]
chap-python-sdk = { path = "../chap-python-sdk", editable = true }
```

### Write Tests

```python
import pytest
from chap_python_sdk.testing import get_example_data, validate_model_io
from main import runner, MyModelConfig

class TestMyModel:
    @pytest.mark.asyncio
    async def test_model_validation(self) -> None:
        example_data = get_example_data(country="laos", frequency="monthly")
        config = MyModelConfig(lags=6, n_samples=10)

        result = await validate_model_io(runner, example_data, config)

        assert result.success, f"Validation failed: {result.errors}"
```

### Run Tests

```bash
uv run pytest tests/ -v
```

## Step 3: Evaluate with chap-core

### Start Your Model Service

```bash
uv run uvicorn main:app --port 8080
```

### Run Evaluation

```bash
chap evaluate2 http://localhost:8080 \
    --dataset-csv path/to/data.csv \
    --output-file results/evaluation.nc \
    --run-config.is-chapkit-model
```

### Export Metrics

```bash
chap export-metrics results/evaluation.nc \
    --output-file results/metrics.csv
```

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| RMSE | Root Mean Square Error | Lower is better |
| MAE | Mean Absolute Error | Lower is better |
| CRPS | Continuous Ranked Probability Score | Lower is better |
| Coverage 10th-90th | % predictions in 80% interval | ~80% |
| Coverage 25th-75th | % predictions in 50% interval | ~50% |

## Dataset Format

CSV files must have:

```csv
time_period,disease_cases,rainfall,mean_temperature,population,location,parent
2019-01,10,100.5,25.3,50000,Bokeo,-
```

Required columns:
- `time_period` - Date or date range
- `disease_cases` - Target variable
- `location` - Spatial identifier
- `population` - Population count (for some models)

Optional covariates:
- `rainfall` - Precipitation
- `mean_temperature` - Temperature

## Common Issues and Solutions

### "Could not convert string to numeric"
CSV data loaded as strings. Add numeric conversion in your model.

### "invalid tzoffset" error
Weekly date ranges like "2019-01-21/2019-01-27". Parse start date only.

### "All fields must be same length"
Wrong prediction format. Use `sample_0`, `sample_1`, etc. columns.

### Port already in use
```bash
lsof -ti:8080 | xargs kill -9
```

## Example Project Structure

```
my-model/
├── main.py                 # Model service
├── pyproject.toml          # Dependencies
├── Dockerfile              # Container build
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Test fixtures
│   └── test_model.py       # Model tests
├── data/
│   └── example.csv         # Test data
└── results/
    ├── evaluation.nc       # Evaluation results
    └── metrics.csv         # Exported metrics
```

## Next Steps for Model Improvement

1. **Better uncertainty quantification** - Use proper probabilistic models
2. **Add more covariates** - Population density, land use, etc.
3. **Seasonal modeling** - Explicit seasonal components
4. **Spatial modeling** - Account for spatial autocorrelation
5. **Ensemble methods** - Combine multiple models
