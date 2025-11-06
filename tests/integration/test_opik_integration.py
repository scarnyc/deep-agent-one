"""
Integration tests for Opik client.

Tests real Opik SDK integration with mocked API calls.
Marks tests with @pytest.mark.integration for selective execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deep_agent.config.settings import Settings
from deep_agent.integrations.opik_client import (
    ALGORITHM_SELECTION_GUIDE,
    OpikClient,
    OptimizerAlgorithm,
    get_opik_client,
)


@pytest.fixture
def mock_settings():
    """Create mock settings with Opik configuration."""
    settings = MagicMock(spec=Settings)
    settings.OPIK_API_KEY = "test-api-key"
    settings.OPIK_WORKSPACE = "test-workspace"
    settings.OPIK_PROJECT = "test-project"
    return settings


@pytest.fixture
def mock_opik_sdk():
    """Mock the Opik SDK."""
    with patch("deep_agent.integrations.opik_client.opik") as mock_opik, \
         patch("deep_agent.integrations.opik_client.opik_optimizer") as mock_optimizer:

        # Mock Opik client
        mock_client = MagicMock()
        mock_opik.Opik.return_value = mock_client

        # Mock dataset
        mock_dataset = MagicMock()
        mock_client.get_or_create_dataset.return_value = mock_dataset

        # Mock optimizers
        mock_optimizer.HierarchicalReflectiveOptimizer.return_value = MagicMock()
        mock_optimizer.FewShotBayesianOptimizer.return_value = MagicMock()
        mock_optimizer.EvolutionaryOptimizer.return_value = MagicMock()
        mock_optimizer.MetaPromptOptimizer.return_value = MagicMock()
        mock_optimizer.GepaOptimizer.return_value = MagicMock()
        mock_optimizer.ParameterOptimizer.return_value = MagicMock()

        # Mock ChatPrompt
        mock_optimizer.ChatPrompt.return_value = MagicMock()

        yield {
            "opik": mock_opik,
            "optimizer": mock_optimizer,
            "client": mock_client,
            "dataset": mock_dataset,
        }


@pytest.mark.integration
class TestOpikClientInitialization:
    """Test suite for OpikClient initialization."""

    def test_opik_client_init_success(self, mock_settings, mock_opik_sdk):
        """Test successful OpikClient initialization."""
        # Act
        client = OpikClient(settings=mock_settings)

        # Assert
        assert client.settings == mock_settings
        assert client.project_name == "test-project"
        mock_opik_sdk["opik"].Opik.assert_called_once_with(
            api_key="test-api-key",
            workspace="test-workspace",
        )

    def test_opik_client_init_no_api_key(self):
        """Test that OpikClient raises error if API key missing."""
        # Arrange
        settings = MagicMock(spec=Settings)
        settings.OPIK_API_KEY = None

        # Act & Assert
        with pytest.raises(ValueError, match="OPIK_API_KEY not configured"):
            OpikClient(settings=settings)

    def test_opik_client_init_default_settings(self, mock_opik_sdk):
        """Test OpikClient with default settings."""
        # Arrange
        with patch("deep_agent.integrations.opik_client.get_settings") as mock_get_settings:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.OPIK_API_KEY = "default-key"
            mock_settings.OPIK_WORKSPACE = "default-workspace"
            mock_settings.OPIK_PROJECT = "default-project"
            mock_get_settings.return_value = mock_settings

            # Act
            client = OpikClient()

            # Assert
            assert client.settings == mock_settings
            mock_get_settings.assert_called_once()


@pytest.mark.integration
class TestOpikClientDataset:
    """Test suite for OpikClient dataset operations."""

    def test_get_or_create_dataset_new(self, mock_settings, mock_opik_sdk):
        """Test creating a new dataset."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        dataset_name = "test-dataset"
        items = [
            {"input": "test", "output": "result"},
            {"input": "test2", "output": "result2"},
        ]

        # Act
        dataset = client.get_or_create_dataset(name=dataset_name, items=items)

        # Assert
        assert dataset is not None
        mock_opik_sdk["client"].get_or_create_dataset.assert_called_once_with(
            name=dataset_name
        )
        mock_opik_sdk["dataset"].insert.assert_called_once_with(items)

    def test_get_or_create_dataset_existing(self, mock_settings, mock_opik_sdk):
        """Test getting existing dataset."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        dataset_name = "existing-dataset"

        # Act
        dataset = client.get_or_create_dataset(name=dataset_name)

        # Assert
        assert dataset is not None
        mock_opik_sdk["client"].get_or_create_dataset.assert_called_once_with(
            name=dataset_name
        )
        # Should not insert if no items provided
        mock_opik_sdk["dataset"].insert.assert_not_called()

    def test_get_or_create_dataset_error(self, mock_settings, mock_opik_sdk):
        """Test error handling in dataset creation."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        mock_opik_sdk["client"].get_or_create_dataset.side_effect = Exception(
            "API error"
        )

        # Act & Assert
        with pytest.raises(Exception, match="API error"):
            client.get_or_create_dataset(name="test")


@pytest.mark.integration
class TestOpikClientOptimizers:
    """Test suite for OpikClient optimizer creation."""

    def test_get_optimizer_hierarchical_reflective(self, mock_settings, mock_opik_sdk):
        """Test creating HierarchicalReflectiveOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].HierarchicalReflectiveOptimizer.assert_called_once()

    def test_get_optimizer_few_shot_bayesian(self, mock_settings, mock_opik_sdk):
        """Test creating FewShotBayesianOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.FEW_SHOT_BAYESIAN)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].FewShotBayesianOptimizer.assert_called_once()

    def test_get_optimizer_evolutionary(self, mock_settings, mock_opik_sdk):
        """Test creating EvolutionaryOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.EVOLUTIONARY)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].EvolutionaryOptimizer.assert_called_once()

    def test_get_optimizer_meta_prompt(self, mock_settings, mock_opik_sdk):
        """Test creating MetaPromptOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.META_PROMPT)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].MetaPromptOptimizer.assert_called_once()

    def test_get_optimizer_gepa(self, mock_settings, mock_opik_sdk):
        """Test creating GepaOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.GEPA)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].GepaOptimizer.assert_called_once()

    def test_get_optimizer_gepa_not_installed(self, mock_settings, mock_opik_sdk):
        """Test error when GEPA package not installed."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        mock_opik_sdk["optimizer"].GepaOptimizer.side_effect = ImportError(
            "No module named 'gepa'"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="GEPA optimizer requires"):
            client.get_optimizer(OptimizerAlgorithm.GEPA)

    def test_get_optimizer_parameter(self, mock_settings, mock_opik_sdk):
        """Test creating ParameterOptimizer."""
        # Arrange
        client = OpikClient(settings=mock_settings)

        # Act
        optimizer = client.get_optimizer(OptimizerAlgorithm.PARAMETER)

        # Assert
        assert optimizer is not None
        mock_opik_sdk["optimizer"].ParameterOptimizer.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
class TestOpikClientOptimization:
    """Test suite for OpikClient optimization operations."""

    async def test_optimize_prompt_async_success(self, mock_settings, mock_opik_sdk):
        """Test successful async prompt optimization."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        prompt = "You are a helpful assistant."
        dataset = MagicMock()
        metric = MagicMock()

        # Mock optimization result
        mock_result = MagicMock()
        mock_result.prompt = "You are an expert AI assistant."
        mock_result.score = 0.9
        mock_result.improvement = 0.25

        mock_optimizer = MagicMock()
        mock_optimizer.optimize_prompt.return_value = mock_result
        mock_opik_sdk["optimizer"].HierarchicalReflectiveOptimizer.return_value = (
            mock_optimizer
        )

        # Act
        result = await client.optimize_prompt_async(
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            algorithm=OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE,
            max_trials=5,
        )

        # Assert
        assert result["optimized_prompt"] == "You are an expert AI assistant."
        assert result["original_prompt"] == prompt
        assert result["score"] == 0.9
        assert result["improvement"] == 0.25
        assert result["algorithm"] == "hierarchical_reflective"
        assert result["trials"] == 5

    async def test_optimize_prompt_async_with_tools(self, mock_settings, mock_opik_sdk):
        """Test optimization with MCP tools (MetaPrompt algorithm)."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        prompt = "You are a helpful assistant."
        dataset = MagicMock()
        metric = MagicMock()
        tools = [{"name": "web_search", "description": "Search the web"}]
        function_map = {"web_search": lambda x: x}

        mock_result = MagicMock()
        mock_result.prompt = "Optimized with tools"
        mock_result.score = 0.95
        mock_result.improvement = 0.3

        mock_optimizer = MagicMock()
        mock_optimizer.optimize_prompt.return_value = mock_result
        mock_opik_sdk["optimizer"].MetaPromptOptimizer.return_value = mock_optimizer

        # Act
        result = await client.optimize_prompt_async(
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            algorithm=OptimizerAlgorithm.META_PROMPT,
            max_trials=10,
            tools=tools,
            function_map=function_map,
        )

        # Assert
        assert result["optimized_prompt"] == "Optimized with tools"
        assert result["algorithm"] == "meta_prompt"
        # Verify ChatPrompt was created with tools
        mock_opik_sdk["optimizer"].ChatPrompt.assert_called_once()
        call_kwargs = mock_opik_sdk["optimizer"].ChatPrompt.call_args.kwargs
        assert call_kwargs["tools"] == tools
        assert call_kwargs["function_map"] == function_map

    def test_optimize_prompt_sync(self, mock_settings, mock_opik_sdk):
        """Test synchronous wrapper for optimize_prompt."""
        # Arrange
        client = OpikClient(settings=mock_settings)
        prompt = "test"
        dataset = MagicMock()
        metric = MagicMock()

        mock_result = MagicMock()
        mock_result.prompt = "optimized"
        mock_result.score = 0.8
        mock_result.improvement = 0.1

        mock_optimizer = MagicMock()
        mock_optimizer.optimize_prompt.return_value = mock_result
        mock_opik_sdk["optimizer"].HierarchicalReflectiveOptimizer.return_value = (
            mock_optimizer
        )

        # Act
        result = client.optimize_prompt(
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            algorithm=OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE,
            max_trials=3,
        )

        # Assert
        assert result["optimized_prompt"] == "optimized"
        assert result["score"] == 0.8


@pytest.mark.integration
class TestOpikClientSingleton:
    """Test suite for OpikClient singleton pattern."""

    def test_get_opik_client_singleton(self, mock_settings, mock_opik_sdk):
        """Test that get_opik_client returns singleton instance."""
        # Arrange & Act
        with patch("deep_agent.integrations.opik_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            client1 = get_opik_client()
            client2 = get_opik_client()

            # Assert
            assert client1 is client2  # Same instance
            # Should only create once
            assert mock_opik_sdk["opik"].Opik.call_count == 1


@pytest.mark.integration
class TestAlgorithmSelectionGuide:
    """Test suite for ALGORITHM_SELECTION_GUIDE constant."""

    def test_algorithm_guide_exists(self):
        """Test that algorithm selection guide is defined."""
        # Assert
        assert ALGORITHM_SELECTION_GUIDE is not None
        assert isinstance(ALGORITHM_SELECTION_GUIDE, str)
        assert len(ALGORITHM_SELECTION_GUIDE) > 100

    def test_algorithm_guide_includes_all_algorithms(self):
        """Test that guide mentions all 6 algorithms."""
        # Assert
        guide_lower = ALGORITHM_SELECTION_GUIDE.lower()
        assert "hierarchicalreflective" in guide_lower or "hierarchical" in guide_lower
        assert "fewshot" in guide_lower or "few shot" in guide_lower or "bayesian" in guide_lower
        assert "evolutionary" in guide_lower
        assert "metaprompt" in guide_lower or "meta prompt" in guide_lower
        assert "gepa" in guide_lower
        assert "parameter" in guide_lower

    def test_algorithm_guide_includes_benchmarks(self):
        """Test that guide includes benchmark percentages."""
        # Assert
        # Should mention performance percentages
        assert "67.83" in ALGORITHM_SELECTION_GUIDE  # HierarchicalReflective
        assert "59.17" in ALGORITHM_SELECTION_GUIDE  # FewShotBayesian
        assert "52.51" in ALGORITHM_SELECTION_GUIDE  # Evolutionary

    def test_algorithm_guide_mentions_mcp_tools(self):
        """Test that guide mentions MCP tool support."""
        # Assert
        guide_upper = ALGORITHM_SELECTION_GUIDE.upper()
        assert "MCP" in guide_upper
