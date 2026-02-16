# gh-worktree project style guide

# Introduction
This style guide outlines the coding conventions for the project `gh-worktree`. The project is a CLI utility that assists software developers in their use of git worktrees. The project uses `python-fire` to provide the CLI and is structured into classes which represent the commands that can be invoked.

# Key Principles
* **Readability:** Code should be broken into understandable units and align with the Single Responsibility Principle (SRP).
* **Maintainability:** Code should uphold the "Don't Repeat Yourself" (DRY) principle.
* **Consistency:** Adhering to a consistent style across all projects improves collaboration and reduces errors.
* **Performance:** While readability is paramount, code should be efficient.

# Deviations from PEP 8

## Line Length
* **Maximum line length:** 100 characters.

## Indentation
* **Use 4 spaces per indentation level.** (PEP 8 recommendation)

## Imports
* **Group imports:** Do not use group imports.
* **Absolute imports:** Always use absolute imports for clarity.

## Naming Conventions

* **Variables:** Use lowercase with underscores (snake_case): `user_name`, `total_count`
* **Constants:**  Use uppercase with underscores: `MAX_VALUE`, `DATABASE_NAME`
* **Functions:** Use lowercase with underscores (snake_case): `calculate_total()`, `process_data()`
* **Classes:** Use CapWords (CamelCase): `UserManager`, `PaymentProcessor`
* **Modules:** Use lowercase with underscores (snake_case): `user_utils`, `payment_gateway`

## Docstrings
* **Use triple double quotes (`"""Docstring goes here."""`) for all docstrings.**
* **For complex functions/classes:** Include detailed descriptions of parameters, return values,
  attributes, and exceptions.
* **Use Sphinx style docstrings:** This helps with automated documentation generation.
    ```python
    def my_function(param1, param2):
        """Single-line summary.

        More detailed description, if necessary.

        :param param1: The first parameter.
        :type param1: int
        :param param2: The second parameter.
        :type param2: str
        :return: The return value.  True for success, False otherwise.
        :rtype: bool
        :raises ValueError: If `param2` is invalid.
        """
        # function body here
        pass
    ```

## Type Hints
* **Use type hints:** Type hints improve code readability and help catch errors early.
* **Follow PEP 484:** Use the standard type hinting syntax.

## Comments
* **Write clear and concise comments:** Explain the "why" behind the code, not just the "what".
* **Comment sparingly:** Well-written code should be self-documenting where possible.
* **Use complete sentences:** Start comments with a capital letter and use proper punctuation.
