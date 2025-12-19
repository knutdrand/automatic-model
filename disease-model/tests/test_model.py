"""Tests for disease model using chap-python-sdk."""

import pytest
from chapkit.ml import RunInfo

from main import DiseaseModelConfig, info, on_predict, on_train


class TestDiseaseModel:
    """Tests for the disease model implementation."""

    @pytest.mark.asyncio
    async def test_model_with_sdk_validation(self) -> None:
        """Test model validation using chap-python-sdk."""
        from chap_python_sdk.testing import get_example_data, validate_model_io

        example_data = get_example_data(country="laos", frequency="monthly")
        config = DiseaseModelConfig(lags=6, lags_past_covariates=6, n_samples=10)

        result = await validate_model_io(on_train, on_predict, example_data, config)

        assert result.success, f"Validation failed: {result.errors}"
        assert result.n_predictions > 0, "No predictions generated"
        assert result.n_samples >= 1, "No samples in predictions"

    @pytest.mark.asyncio
    async def test_train_produces_models(self) -> None:
        """Test that training produces models for locations."""
        from chap_python_sdk.testing import get_example_data

        example_data = get_example_data(country="laos", frequency="monthly")
        config = DiseaseModelConfig(lags=6, lags_past_covariates=6, n_samples=10)
        run_info = RunInfo(prediction_length=3)

        trained_model = await on_train(config, example_data.training_data, run_info, None)

        assert "models" in trained_model, "No models in training output"
        assert "training_stats" in trained_model, "No training stats"
        assert len(trained_model["models"]) > 0, "No models trained"

    @pytest.mark.asyncio
    async def test_predictions_have_correct_format(self) -> None:
        """Test that predictions have correct output format."""
        from chap_python_sdk.testing import get_example_data

        example_data = get_example_data(country="laos", frequency="monthly")
        config = DiseaseModelConfig(lags=6, lags_past_covariates=6, n_samples=10)
        run_info = RunInfo(prediction_length=3)

        trained_model = await on_train(config, example_data.training_data, run_info, None)
        predictions = await on_predict(
            config,
            trained_model,
            example_data.historic_data,
            example_data.future_data,
            run_info,
            None,
        )

        pred_df = predictions.to_pandas()

        assert "time_period" in pred_df.columns, "Missing time_period column"
        assert "location" in pred_df.columns, "Missing location column"
        assert "sample_0" in pred_df.columns, "Missing sample_0 column"

        # Check correct number of sample columns
        sample_cols = [c for c in pred_df.columns if c.startswith("sample_")]
        assert len(sample_cols) == config.n_samples, f"Expected {config.n_samples} sample columns"

    @pytest.mark.asyncio
    async def test_model_with_generated_data(self) -> None:
        """Test model using generated data based on MLServiceInfo."""
        from chap_python_sdk.testing import (
            MLServiceInfo,
            PeriodType,
            generate_test_data,
            validate_model_io,
        )

        # Create MLServiceInfo matching the model's declared requirements
        service_info = MLServiceInfo(
            required_covariates=list(info.required_covariates),
            allow_free_additional_continuous_covariates=info.allow_free_additional_continuous_covariates,
            supported_period_type=PeriodType(info.supported_period_type.value),
        )

        # Generate test data based on model requirements
        example_data = generate_test_data(
            service_info,
            prediction_length=3,
            n_locations=3,
            n_training_periods=24,
            seed=42,
        )

        config = DiseaseModelConfig(lags=6, lags_past_covariates=6, n_samples=10)

        result = await validate_model_io(on_train, on_predict, example_data, config)

        assert result.success, f"Validation failed: {result.errors}"
        assert result.n_predictions > 0, "No predictions generated"
        assert result.n_samples == 10, f"Expected 10 samples, got {result.n_samples}"
