# Tests

This directory contains comprehensive end-to-end (E2E) tests for the LeRobot Dataset Editor.

## Test Philosophy

These tests focus on **command-based E2E testing** rather than individual unit tests. They test the system from the user's perspective, ensuring that:

1. **CLI commands work correctly** with real datasets
2. **Dataset operations** (delete, copy) work end-to-end
3. **Error handling** provides meaningful feedback to users
4. **GUI components** can be initialized and integrate properly
5. **Example scripts** work as documented

## Test Structure

### Test Files

- `test_cli_e2e.py` - CLI command testing (help, summary, list, episode display)
- `test_dataset_operations_e2e.py` - Dataset modification operations (delete, copy)
- `test_gui_e2e.py` - GUI startup and integration testing (with mocking)
- `test_error_handling_e2e.py` - Error scenarios and edge cases
- `test_examples_e2e.py` - Example scripts functionality
- `conftest.py` - Test configuration and fixtures

### Fixtures

The tests use several key fixtures:

- `sample_dataset` - Creates a realistic test dataset with 3 episodes
- `cli_runner` - Runs CLI commands and captures output
- `dataset_validator` - Validates dataset structure integrity
- `episode_counter` - Counts episodes in a dataset
- `episode_data_reader` - Reads episode data for verification

## Running Tests

### Install Test Dependencies

```bash
# Install test dependencies
uv sync --group dev

# Or with pip
pip install pytest pandas pyarrow
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cli_e2e.py

# Run specific test class
pytest tests/test_cli_e2e.py::TestCLIBasicCommands

# Run specific test
pytest tests/test_cli_e2e.py::TestCLIBasicCommands::test_help_command
```

### Test Categories

```bash
# Run only CLI tests
pytest -m cli

# Run only dataset operation tests  
pytest -m dataset

# Run only GUI tests
pytest -m gui

# Skip slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration
```

### Test with Coverage

```bash
# Run with coverage
pytest --cov=lerobot_dataset_editor --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Data

Tests create temporary datasets with realistic structure:

- **3 sample episodes** with proper parquet data
- **2 tasks** with different instructions
- **Multiple camera views** (left, wrist.right)
- **Complete metadata** (info.json, episodes.jsonl, tasks.jsonl)
- **SO-100 robot data** with 6-DOF joint states

## Test Categories

### 1. CLI Tests (`test_cli_e2e.py`)

Tests core CLI functionality:
- Help commands and argument parsing
- Dataset summary and statistics
- Episode listing and display
- Command validation and error handling
- Output formatting and content verification

### 2. Dataset Operations (`test_dataset_operations_e2e.py`)

Tests dataset modification operations:
- Episode deletion with automatic renumbering
- Episode copying with new instructions
- Metadata consistency after operations
- Dry-run mode functionality
- Multi-operation sequences

### 3. GUI Tests (`test_gui_e2e.py`)

Tests GUI components and integration:
- Module imports and availability
- GUI startup and initialization (mocked)
- CLI-GUI integration
- Error handling for missing dependencies
- Component structure validation

### 4. Error Handling (`test_error_handling_e2e.py`)

Tests comprehensive error scenarios:
- Invalid dataset structures
- Missing files and directories
- Corrupted data files
- Permission issues
- Resource limitations
- User-friendly error messages

### 5. Example Scripts (`test_examples_e2e.py`)

Tests example scripts functionality:
- Script help and documentation
- Argument parsing and validation
- Error handling and messages
- Performance characteristics
- Integration with main tool

## Test Design Principles

### 1. E2E Focus
Tests focus on complete user workflows rather than internal implementation details.

### 2. Real Data
Tests use realistic datasets with proper structure and content.

### 3. Command-Based
Tests primarily use CLI commands as users would, ensuring the command interface works correctly.

### 4. Error Scenarios
Comprehensive testing of error conditions ensures robust user experience.

### 5. Performance Awareness
Tests include basic performance checks to catch obvious regressions.

### 6. Environment Independence
Tests work in various environments (CI, headless, different platforms).

## Mocking Strategy

The tests use minimal mocking, primarily for:

- **GUI components** - To test without requiring display
- **File system errors** - To simulate permission/disk issues
- **Network conditions** - To test error handling

Most functionality is tested with real implementations.

## Continuous Integration

Tests are designed to run reliably in CI environments:

- **Headless GUI testing** using mocks
- **Temporary datasets** that don't require external data
- **Platform independence** (Linux, macOS, Windows)
- **Dependency isolation** with optional imports

## Adding New Tests

When adding new functionality:

1. **Add E2E tests** that test the complete user workflow
2. **Test error cases** for new functionality
3. **Update fixtures** if new test data patterns are needed
4. **Add performance tests** for operations that process large data
5. **Test CLI integration** for new command-line features

### Example Test Pattern

```python
def test_new_feature_e2e(self, cli_runner, sample_dataset):
    """Test new feature end-to-end."""
    # Test the happy path
    result = cli_runner(["--new-feature", "arg", str(sample_dataset)])
    assert result.returncode == 0
    assert "expected output" in result.stdout
    
    # Test error cases
    result = cli_runner(["--new-feature", "invalid", str(sample_dataset)])
    assert result.returncode == 1
    assert "error message" in result.stderr
```

## Test Maintenance

- **Keep tests simple** and focused on user scenarios
- **Update tests** when CLI interface changes
- **Add new error scenarios** as they're discovered
- **Maintain test data** to reflect realistic use cases
- **Review test performance** to keep test runs fast