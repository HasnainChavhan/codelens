"""
CodeLens — LLM Prompts for Documentation Generation
Fine-tuned few-shot prompts for consistent, high-quality documentation.
"""

SYSTEM_PROMPT = """You are a senior software engineer specialising in writing clean, professional Python documentation.
Your documentation is:
- Concise but complete
- Written in Google docstring style
- Free of redundant verbosity (no "This function..."-style openings)
- Specific about edge cases, performance characteristics, and return types
- Always in plain English — no emojis, no markdown inside docstrings

Output ONLY the docstring content (triple-quoted), nothing else."""

FUNCTION_DOC_PROMPT = """Generate a Google-style docstring for this Python function.

Function: {function_name}
Signature: {signature}
Is async: {is_async}
Decorators: {decorators}

Parameters (from AST):
{parameters}

Return type: {return_type}

Call relationships (what this function calls):
{calls}

Existing docstring (if any, use as context):
{existing_docstring}

Source code:
```python
{source_code}
```

Generate the docstring now:"""

CLASS_DOC_PROMPT = """Generate a Google-style class docstring.

Class: {class_name}
Inherits from: {bases}
Decorators: {decorators}
Number of methods: {method_count}

Method signatures:
{method_signatures}

Existing docstring (if any):
{existing_docstring}

Generate the class docstring (describe purpose, key attributes, usage):"""

MODULE_DOC_PROMPT = """Generate a module-level docstring for this Python module.

Module: {module_name}
Total lines: {total_lines}
Functions: {function_count} ({function_names})
Classes: {class_count} ({class_names})

Key imports:
{imports}

Existing docstring:
{existing_docstring}

Generate a concise module docstring (1-3 sentences describing purpose and main exports):"""

# Few-shot examples for consistent style
FEW_SHOT_EXAMPLES = [
    {
        "input": """Function: calculate_discount
Signature: def calculate_discount(price: float, discount_pct: float, min_price: float = 0.0) -> float:
Source: if discount_pct < 0 or discount_pct > 100: raise ValueError...""",
        "output": '''"""Apply a percentage discount to a price with a floor constraint.

Args:
    price: Original price in the base currency unit.
    discount_pct: Discount percentage, must be in range [0, 100].
    min_price: Minimum allowable price after discount. Defaults to 0.0.

Returns:
    Discounted price, floored at min_price.

Raises:
    ValueError: If discount_pct is outside [0, 100].
    ValueError: If price is negative.
"""''',
    },
    {
        "input": """Class: ConnectionPool
Bases: object
Methods: connect, disconnect, acquire, release, health_check""",
        "output": '''"""Thread-safe connection pool for managing reusable database connections.

Maintains a fixed-size pool of pre-established connections, dispensing them
on demand and returning them after use. Prevents connection exhaustion under
high concurrency by blocking callers when the pool is fully allocated.

Usage:
    pool = ConnectionPool(size=10, dsn="postgresql://...")
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")
"""''',
    },
]
