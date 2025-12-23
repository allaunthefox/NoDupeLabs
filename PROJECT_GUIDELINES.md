# NoDupeLabs Project Rules & Standards

## 1. Documentation Standard (Mandatory)
- **Always** generate comprehensive docstrings for all new code and modifications.
- **Style:** Follow the **Google Python Style Guide** for docstrings.
- **Scope:** Every module, class, and function (public or private) must have a docstring.
- **Content:** Include a concise summary, `Args`, `Returns`, and `Raises` (if applicable).

### Docstring Format Examples

All functions, classes, methods, and modules should include comprehensive docstrings following the Google style format:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of what the function does.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter
        
    Returns:
        Description of the return value
        
    Raises:
        Description of any exceptions that might be raised
    """
    # function implementation
```

Classes should have docstrings that describe their purpose, attributes, and usage:

```python
class ExampleClass:
    """Brief description of what the class represents.
    
    Attributes:
        attr1: Description of the first attribute
        attr2: Description of the second attribute
    """
    # class implementation
```

All Python files should start with a module docstring:

```python
"""Module description explaining the purpose of the file.

This module contains...
"""
```

## 2. Testing Standard
- **Always** create or update unit tests for any logic changes.
- **Framework:** Use `pytest`.
- **Location:** Place tests in the `tests/` directory, mirroring the source structure.
- **Convention:** Test files must start with `test_` and test functions must start with `test_`.

### Test Format Examples

Unit tests should follow the pytest framework conventions:

```python
def test_function_name():
    """Test description explaining what is being tested."""
    # Arrange - set up test data
    # Act - execute the function being tested
    # Assert - verify the expected results
    assert result == expected_value
```

## 3. ContextStream Integration
- When a significant architectural decision is made, use `session_capture` to record it.
- If a specific error or "gotcha" is resolved, use `session_capture_lesson` to prevent recurrence.
- If the ContextStream MCP server is unavailable, fall back to updating `PROJECT_GUIDELINES.md`.

### ContextStream Configuration

For accessing ContextStream MCP server tools, proper configuration is required:

1. Obtain a ContextStream API key from https://contextstream.io
2. Set the following environment variables:
   - `CONTEXTSTREAM_API_URL`: "https://api.contextstream.io" 
   - `CONTEXTSTREAM_API_KEY`: Your personal API key

3. Install the MCP server:
   ```bash
   npm install -g @contextstream/mcp-server
   ```

4. Run the setup wizard:
   ```bash
   npx -y @contextstream/mcp-server setup
   ```

## 4. General Coding Behavior
- Prioritize readability and maintainability over "clever" one-liners.
- Keep functions small and focused on a single responsibility.
- Before starting a major refactor, propose the plan to the user for approval.

## 5. High-Speed Debugging & Verification
- **Diagnostic First:** Before suggesting a fix for an error, you MUST run a diagnostic command (e.g., `grep`, `ls -R`, or a specific `pytest` line) to verify the current state.
- **Atomic Edits:** Never fix more than one bug in a single file-write. Each fix must be isolated.
- **The "No-Guess" Rule:** If you are unsure why a variable is a certain value, you must insert temporary `print()` or `logging` statements and run the code before proposing a final fix.
- **Fix Verification:** A task is not complete until you have executed the relevant test or script and confirmed the output is correct. Do not "assume" a fix works because the code looks right.
- **Regression Prevention:** Every bug fix must include a new test case in `tests/` that specifically targets the discovered failure to prevent it from returning.
