"""Cascade Stage Protocol.

Abstract base class and protocol definitions for all Cascade stages.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class QualityTier(Enum):
    """Quality tiers for cascade stages.
    
    Defines the quality levels that cascade stages can operate at,
    allowing the system to select appropriate stages based on
    performance and quality requirements.
    """
    BEST = "best"           # Highest quality, best performance when available
    GOOD = "good"           # Good quality, reliable performance
    ACCEPTABLE = "acceptable"  # Acceptable quality, fallback option
    MINIMAL = "minimal"     # Minimal quality, basic functionality


class StageExecutionError(Exception):
    """Exception raised when a cascade stage fails to execute.
    
    This exception is raised when a cascade stage encounters
    an error during execution that prevents it from completing
    its task successfully.
    """
    
    def __init__(self, message: str, stage: str, execution_time: Optional[float] = None):
        """Initialize StageExecutionError.
        
        Args:
            message: Error message describing the failure
            stage: Name of the stage that failed
            execution_time: Optional execution time when error occurred
        """
        self.message = message
        self.stage = stage
        self.execution_time = execution_time
        super().__init__(self.message)


class CascadeStage(ABC):
    """Abstract base class for all Cascade stages.
    
    Defines the common interface and behavior for all cascade stages.
    Cascade stages implement specific functionality with quality tiers
    and availability checking for optimal performance selection.
    
    Key Features:
        - Quality tier-based operation
        - Availability checking
        - Error handling and recovery
        - Performance measurement
        - Security policy integration
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name.
        
        Returns:
            Human-readable name of the stage
        """

    @property
    @abstractmethod
    def quality_tier(self) -> QualityTier:
        """Quality tier for this stage.
        
        Returns:
            QualityTier enum value indicating stage quality level
        """

    @property
    @abstractmethod
    def requires_internet(self) -> bool:
        """Whether this stage requires internet access.
        
        Returns:
            True if internet access is required, False otherwise
        """

    @property
    @abstractmethod
    def requires_plugins(self) -> List[str]:
        """List of required plugins for this stage.
        
        Returns:
            List of plugin names that must be available
        """

    @abstractmethod
    def can_operate(self) -> bool:
        """Check if the stage can operate in current environment.
        
        This method should check:
        - Plugin availability
        - Security policy constraints
        - System requirements
        - Any other prerequisites
        
        Returns:
            True if stage can operate, False otherwise
        """

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the stage with given parameters.
        
        Args:
            *args: Positional arguments specific to the stage
            **kwargs: Keyword arguments specific to the stage
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            StageExecutionError: If execution fails
        """

    def get_stage_info(self) -> Dict[str, Any]:
        """Get comprehensive stage information.
        
        Returns:
            Dictionary containing stage metadata
        """
        return {
            "name": self.name,
            "quality_tier": self.quality_tier.value,
            "requires_internet": self.requires_internet,
            "requires_plugins": self.requires_plugins,
            "can_operate": self.can_operate()
        }

    def validate_input(self, *args, **kwargs) -> bool:
        """Validate input parameters before execution.
        
        Args:
            *args: Positional arguments to validate
            **kwargs: Keyword arguments to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        # Default implementation - can be overridden by subclasses
        return True

    def measure_performance(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Execute function with performance measurement.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Dictionary with results and performance metrics
        """
        import time
        
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            if isinstance(result, dict):
                result["execution_time"] = execution_time
            else:
                result = {
                    "result": result,
                    "execution_time": execution_time
                }
            
            return result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            raise StageExecutionError(
                f"Performance measurement failed: {str(e)}",
                stage=self.name,
                execution_time=execution_time
            )


class StageManager:
    """Manager for cascade stages.
    
    Provides functionality to:
    - Register and discover cascade stages
    - Select optimal stages based on quality tiers
    - Handle stage execution and error recovery
    - Manage stage dependencies and availability
    """
    
    def __init__(self):
        """Initialize stage manager."""
        self.stages: Dict[str, CascadeStage] = {}
        self.availability_cache: Dict[str, bool] = {}
    
    def register_stage(self, stage: CascadeStage) -> None:
        """Register a cascade stage.
        
        Args:
            stage: CascadeStage instance to register
        """
        self.stages[stage.name] = stage
        # Clear availability cache when registering new stages
        self.availability_cache.clear()
    
    def get_stage(self, stage_name: str) -> Optional[CascadeStage]:
        """Get a registered stage by name.
        
        Args:
            stage_name: Name of the stage to retrieve
            
        Returns:
            CascadeStage instance or None if not found
        """
        return self.stages.get(stage_name)
    
    def get_available_stages(self) -> List[CascadeStage]:
        """Get all available stages.
        
        Returns:
            List of stages that can operate in current environment
        """
        available_stages = []
        for stage in self.stages.values():
            if self.is_stage_available(stage.name):
                available_stages.append(stage)
        return available_stages
    
    def is_stage_available(self, stage_name: str) -> bool:
        """Check if a stage is available.
        
        Args:
            stage_name: Name of the stage to check
            
        Returns:
            True if stage is available, False otherwise
        """
        if stage_name in self.availability_cache:
            return self.availability_cache[stage_name]
        
        stage = self.stages.get(stage_name)
        if not stage:
            self.availability_cache[stage_name] = False
            return False
        
        try:
            is_available = stage.can_operate()
            self.availability_cache[stage_name] = is_available
            return is_available
        except Exception:
            self.availability_cache[stage_name] = False
            return False
    
    def select_optimal_stage(self, stage_type: str, quality_preference: QualityTier = QualityTier.BEST) -> Optional[CascadeStage]:
        """Select optimal stage based on quality preference.
        
        Args:
            stage_type: Type of stage to select
            quality_preference: Preferred quality tier
            
        Returns:
            Optimal stage instance or None if no suitable stage found
        """
        # Get all stages of the requested type (this would need to be implemented
        # based on how stages are categorized in your system)
        available_stages = self.get_available_stages()
        
        # Filter by quality tier preference
        suitable_stages = []
        for stage in available_stages:
            if stage.quality_tier.value == quality_preference.value:
                suitable_stages.append(stage)
        
        # If no stages match preferred quality, try lower quality tiers
        if not suitable_stages:
            for tier in [QualityTier.GOOD, QualityTier.ACCEPTABLE, QualityTier.MINIMAL]:
                if tier == quality_preference:
                    continue
                for stage in available_stages:
                    if stage.quality_tier.value == tier.value:
                        suitable_stages.append(stage)
                if suitable_stages:
                    break
        
        # Return the first suitable stage (could be enhanced with more sophisticated selection)
        return suitable_stages[0] if suitable_stages else None
    
    def execute_stage(self, stage_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a stage with error handling.
        
        Args:
            stage_name: Name of the stage to execute
            *args: Arguments for the stage
            **kwargs: Keyword arguments for the stage
            
        Returns:
            Stage execution results
            
        Raises:
            StageExecutionError: If stage execution fails
        """
        stage = self.get_stage(stage_name)
        if not stage:
            raise StageExecutionError(
                f"Stage '{stage_name}' not found",
                stage=stage_name
            )
        
        if not self.is_stage_available(stage_name):
            raise StageExecutionError(
                f"Stage '{stage_name}' is not available in current environment",
                stage=stage_name
            )
        
        try:
            return stage.execute(*args, **kwargs)
        except StageExecutionError:
            raise
        except Exception as e:
            raise StageExecutionError(
                f"Stage '{stage_name}' execution failed: {str(e)}",
                stage=stage_name
            )


# Global stage manager instance
_stage_manager: Optional[StageManager] = None


def get_stage_manager() -> StageManager:
    """Get the global stage manager instance."""
    global _stage_manager
    if _stage_manager is None:
        _stage_manager = StageManager()
    return _stage_manager


def register_stage(stage: CascadeStage) -> None:
    """Register a cascade stage globally.
    
    Args:
        stage: CascadeStage instance to register
    """
    manager = get_stage_manager()
    manager.register_stage(stage)


def execute_stage(stage_name: str, *args, **kwargs) -> Dict[str, Any]:
    """Execute a stage globally.
    
    Args:
        stage_name: Name of the stage to execute
        *args: Arguments for the stage
        **kwargs: Keyword arguments for the stage
        
    Returns:
        Stage execution results
    """
    manager = get_stage_manager()
    return manager.execute_stage(stage_name, *args, **kwargs)


__all__ = [
    'QualityTier',
    'StageExecutionError',
    'CascadeStage',
    'StageManager',
    'get_stage_manager',
    'register_stage',
    'execute_stage'
]
