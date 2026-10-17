---
apply: by file patterns
patterns: tests/**/*.py
---

# Unit test guidelines

## Structure
- Utilize test cases (`unittest.TestCase` or `unittest.IsolatedAsyncioTestCase`) for organizing unit tests
- Write one test case per class or function being tested

## Naming
- Name all test cases using the pascal case name of the class or function being tested, with the suffix `TestCase`
- Test case methods that test class units should reference the method name, followed by two underscores, then any specific behavior. For example: `test_method_name__returns_thing`
- Test case methods for testing functions should describe the functionality. For example: `test_returns_thing`

## Best practices
- Utilize assertion methods on test case classes
- Avoid redundancy by organizing common test setup, that should run for every test, into a test case's `setUp` method
- Avoid redundancy by organizing common test setup, that can be run once for all test case methods, into a test case's `setUpClass` classmethod
- Utilize mocking (`unittest.mock`) to isolate units being tested

## Tools
- Tests are executed using `pytest`
