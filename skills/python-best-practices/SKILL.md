---
name: python-best-practices
description: Use this skill when asked about Python best practices, code quality, or production-ready Python code patterns.
---

# Python Best Practices

## Overview

This skill provides comprehensive Python best practices for writing production-ready code.

## Instructions

When the user asks about Python best practices, apply these guidelines:

### 1. Type Hints (MANDATORY)

Always use type hints for function signatures:

```python
# BAD
def calculate_total(items, tax_rate):
    return sum(items) * (1 + tax_rate)

# GOOD
def calculate_total(items: list[float], tax_rate: float) -> float:
    return sum(items) * (1 + tax_rate)
```

### 2. Docstrings (Google Style)

Use Google-style docstrings for all public functions:

```python
def process_order(order_id: str, items: list[dict]) -> dict:
    """Process an order and return the result.

    Args:
        order_id: Unique identifier for the order.
        items: List of item dictionaries with 'name' and 'price' keys.

    Returns:
        Dictionary containing order status and total.

    Raises:
        ValueError: If order_id is empty or items list is empty.
    """
```

### 3. Error Handling

Use specific exceptions, not bare except:

```python
# BAD
try:
    result = risky_operation()
except:
    pass

# GOOD
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except ConnectionError as e:
    logger.warning(f"Connection failed: {e}")
    return None
```

### 4. Constants and Configuration

Use UPPER_CASE for constants, dataclasses for config:

```python
from dataclasses import dataclass

MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

@dataclass
class AppConfig:
    debug: bool = False
    log_level: str = "INFO"
    max_connections: int = 100
```

### 5. Context Managers

Use context managers for resource management:

```python
# BAD
f = open("file.txt")
data = f.read()
f.close()

# GOOD
with open("file.txt") as f:
    data = f.read()
```

### 6. List Comprehensions (When Readable)

Use list comprehensions for simple transformations:

```python
# GOOD - Simple and readable
squares = [x ** 2 for x in range(10)]

# BAD - Too complex, use regular loop
result = [transform(x) for x in items if validate(x) and check(x) or fallback(x)]
```

### 7. Naming Conventions

- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- "Really private": `__double_leading`

### 8. Function Size

Keep functions under 20 lines. If longer, extract helper functions.

### 9. Imports Order

1. Standard library
2. Third-party packages
3. Local imports

Separate each group with a blank line.

```python
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from myapp.config import settings
from myapp.utils import helpers
```

### 10. Avoid Magic Numbers

```python
# BAD
if user.age >= 18:
    allow_access()

# GOOD
MINIMUM_AGE = 18

if user.age >= MINIMUM_AGE:
    allow_access()
```

## When to Apply

Apply these rules when:
- User asks to review Python code
- User asks about best practices
- User asks for production-ready code
- User asks to improve code quality
