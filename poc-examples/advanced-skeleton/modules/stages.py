#!/usr/bin/env python3
"""
Stage Management Module for OSWE PoC Development

Provides structured stage execution with:
- Automatic stage numbering
- Success/failure tracking
- Dependency management
- Rollback capability
- Stage skipping/retrying

Usage:
    from modules.stages import StageManager, Stage

    manager = StageManager()

    @manager.stage("Reconnaissance")
    def recon(ctx):
        # ... recon code ...
        return True

    @manager.stage("Exploitation", depends_on=["Reconnaissance"])
    def exploit(ctx):
        # ... exploit code ...
        return True

    manager.execute(ctx)
"""

from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of stage execution."""
    name: str
    status: StageStatus
    duration: float = 0.0
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage:
    """
    Represents a single exploit stage.
    """
    name: str
    function: Callable
    number: int
    depends_on: List[str] = field(default_factory=list)
    optional: bool = False
    retry_count: int = 0
    retry_delay: int = 0

    def __call__(self, *args, **kwargs):
        """Execute the stage function."""
        return self.function(*args, **kwargs)


class StageManager:
    """
    Manages exploit stage execution with dependencies and error handling.

    Features:
    - Automatic stage numbering
    - Dependency resolution
    - Optional vs required stages
    - Retry logic
    - Stage skipping
    - Result tracking
    """

    def __init__(self, logger=None, fail_fast: bool = False):
        """
        Initialize stage manager.

        Args:
            logger: Optional logger instance
            fail_fast: If True, stop on first failure. If False, continue with optional stages.
        """
        self.stages: List[Stage] = []
        self.results: List[StageResult] = []
        self.logger = logger
        self.fail_fast = fail_fast
        self.stage_number = 0

    def stage(self,
              name: str,
              depends_on: Optional[List[str]] = None,
              optional: bool = False,
              retry: int = 0,
              retry_delay: int = 0):
        """
        Decorator to register a stage.

        Args:
            name: Stage name
            depends_on: List of stage names this depends on
            optional: If True, failure won't stop execution
            retry: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds

        Example:
            @manager.stage("Authentication", depends_on=["Reconnaissance"])
            def auth_stage(ctx):
                return ctx.login()
        """
        def decorator(func: Callable) -> Callable:
            self.stage_number += 1

            stage = Stage(
                name=name,
                function=func,
                number=self.stage_number,
                depends_on=depends_on or [],
                optional=optional,
                retry_count=retry,
                retry_delay=retry_delay
            )

            self.stages.append(stage)
            return func

        return decorator

    def add_stage(self,
                  name: str,
                  function: Callable,
                  depends_on: Optional[List[str]] = None,
                  optional: bool = False) -> Stage:
        """
        Programmatically add a stage (alternative to decorator).

        Args:
            name: Stage name
            function: Stage function
            depends_on: Dependencies
            optional: Optional flag

        Returns:
            Created Stage object
        """
        self.stage_number += 1

        stage = Stage(
            name=name,
            function=function,
            number=self.stage_number,
            depends_on=depends_on or [],
            optional=optional
        )

        self.stages.append(stage)
        return stage

    def _check_dependencies(self, stage: Stage) -> bool:
        """
        Check if stage dependencies have been satisfied.

        Args:
            stage: Stage to check

        Returns:
            True if all dependencies succeeded
        """
        if not stage.depends_on:
            return True

        for dep_name in stage.depends_on:
            # Find dependency result
            dep_result = next((r for r in self.results if r.name == dep_name), None)

            if not dep_result:
                return False

            if dep_result.status != StageStatus.SUCCESS:
                return False

        return True

    def _execute_stage(self, stage: Stage, *args, **kwargs) -> StageResult:
        """
        Execute a single stage with retry logic.

        Args:
            stage: Stage to execute
            *args: Arguments to pass to stage function
            **kwargs: Keyword arguments to pass to stage function

        Returns:
            StageResult
        """
        attempts = stage.retry_count + 1

        for attempt in range(attempts):
            if self.logger:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{stage.retry_count}")
                self.logger.stage(stage.name)

            # Execute stage
            start_time = time.time()

            try:
                result = stage.function(*args, **kwargs)
                duration = time.time() - start_time

                # Interpret result
                if isinstance(result, bool):
                    success = result
                    data = {}
                elif isinstance(result, dict):
                    success = result.get('success', True)
                    data = result
                elif isinstance(result, tuple):
                    success, data = result
                else:
                    success = bool(result)
                    data = {'result': result}

                if success:
                    status = StageStatus.SUCCESS

                    if self.logger:
                        self.logger.stage_complete(success=True)
                        self.logger.timing(stage.name, duration)

                    return StageResult(
                        name=stage.name,
                        status=status,
                        duration=duration,
                        data=data
                    )
                else:
                    # Failed but might retry
                    if attempt < attempts - 1:
                        if self.logger:
                            self.logger.warning(f"Stage failed, retrying in {stage.retry_delay}s...")
                        time.sleep(stage.retry_delay)
                        continue
                    else:
                        # Final failure
                        status = StageStatus.FAILED
                        if self.logger:
                            self.logger.stage_complete(success=False)

                        return StageResult(
                            name=stage.name,
                            status=status,
                            duration=duration,
                            error="Stage returned False"
                        )

            except Exception as e:
                duration = time.time() - start_time

                if attempt < attempts - 1:
                    if self.logger:
                        self.logger.warning(f"Stage error: {e}, retrying in {stage.retry_delay}s...")
                    time.sleep(stage.retry_delay)
                    continue
                else:
                    # Final failure
                    if self.logger:
                        self.logger.error(f"Stage failed: {e}")
                        self.logger.stage_complete(success=False)

                    return StageResult(
                        name=stage.name,
                        status=StageStatus.FAILED,
                        duration=duration,
                        error=str(e)
                    )

        # Should never reach here
        return StageResult(
            name=stage.name,
            status=StageStatus.FAILED,
            error="Unknown error"
        )

    def execute(self, *args, **kwargs) -> bool:
        """
        Execute all registered stages in order.

        Args:
            *args: Arguments to pass to stage functions
            **kwargs: Keyword arguments to pass to stage functions

        Returns:
            True if all required stages succeeded
        """
        if self.logger:
            self.logger.info(f"Executing {len(self.stages)} stage(s)")

        overall_success = True

        for stage in self.stages:
            # Check dependencies
            if not self._check_dependencies(stage):
                if self.logger:
                    self.logger.warning(f"Skipping stage '{stage.name}' - dependencies not met")

                self.results.append(StageResult(
                    name=stage.name,
                    status=StageStatus.SKIPPED,
                    error="Dependencies not met"
                ))
                continue

            # Execute stage
            result = self._execute_stage(stage, *args, **kwargs)
            self.results.append(result)

            # Handle failure
            if result.status == StageStatus.FAILED:
                if not stage.optional:
                    overall_success = False

                    if self.fail_fast:
                        if self.logger:
                            self.logger.error(f"Required stage '{stage.name}' failed. Aborting.")
                        break
                    else:
                        if self.logger:
                            self.logger.warning(f"Required stage '{stage.name}' failed, continuing...")
                else:
                    if self.logger:
                        self.logger.warning(f"Optional stage '{stage.name}' failed, continuing...")

        return overall_success

    def get_results(self) -> List[StageResult]:
        """Get all stage results."""
        return self.results.copy()

    def get_result(self, stage_name: str) -> Optional[StageResult]:
        """
        Get result for a specific stage.

        Args:
            stage_name: Name of the stage

        Returns:
            StageResult if found, None otherwise
        """
        return next((r for r in self.results if r.name == stage_name), None)

    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 60)
        print("STAGE EXECUTION SUMMARY")
        print("=" * 60)

        total_time = sum(r.duration for r in self.results)

        for result in self.results:
            status_symbol = {
                StageStatus.SUCCESS: "[+]",
                StageStatus.FAILED: "[-]",
                StageStatus.SKIPPED: "[!]",
            }.get(result.status, "[?]")

            print(f"{status_symbol} {result.name}: {result.status.value} ({result.duration:.2f}s)")

            if result.error:
                print(f"    Error: {result.error}")

        print("=" * 60)
        print(f"Total Time: {total_time:.2f}s")
        print(f"Success: {sum(1 for r in self.results if r.status == StageStatus.SUCCESS)}/{len(self.results)}")
        print("=" * 60)


# Example usage
if __name__ == "__main__":
    from modules.logger import create_logger

    log = create_logger("stage_demo")
    manager = StageManager(logger=log, fail_fast=False)

    # Define stages using decorator
    @manager.stage("Reconnaissance")
    def recon(target):
        log.info(f"Scanning {target}")
        time.sleep(0.5)
        return True

    @manager.stage("Authentication", depends_on=["Reconnaissance"])
    def auth(target):
        log.info("Attempting login")
        time.sleep(0.3)
        return {"success": True, "username": "admin"}

    @manager.stage("Exploitation", depends_on=["Authentication"], retry=2, retry_delay=1)
    def exploit(target):
        log.info("Exploiting vulnerability")
        time.sleep(0.4)
        # Simulate occasional failure
        import random
        return random.choice([True, True, False])

    @manager.stage("Post-Exploitation", depends_on=["Exploitation"], optional=True)
    def post_exploit(target):
        log.info("Extracting data")
        time.sleep(0.2)
        return True

    # Execute all stages
    success = manager.execute("192.168.1.100")

    # Print summary
    manager.print_summary()

    log.close()
