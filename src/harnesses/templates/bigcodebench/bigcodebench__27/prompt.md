# BigCodeBench v0.1.2 Task: `BigCodeBench/27`

- Target implementation file: `src/solution.py`
- Target unit test file: `tests/test_solution.py`

## Specification
```python
import json
import base64
from datetime import datetime

def task_func(data: dict, DATE_FORMAT = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Takes a Python dictionary, adds a current timestamp to it, serializes the modified dictionary
    to a JSON-formatted string, and then encodes this string using base64 encoding with ASCII character encoding.
    
    Parameters:
    data (dict): The Python dictionary to encode. The dictionary should not contain a key named 'timestamp',
                 as this key is used to insert the current timestamp by the function. The input dictionary
                 is modified in-place by adding the 'timestamp' key.
    
    Returns:
    str: A base64 encoded string that represents the input dictionary with an added timestamp,
         encoded in ASCII. The timestamp is added with the key 'timestamp'.
    DATE_FORMAT: The timestamp format. Default to 'YYYY-MM-DD HH:MM:SS'.
         
    Requirements:
    - json
    - base64
    - datetime.datetime
    
    Example:
    >>> data = {'name': 'John', 'age': 30, 'city': 'New York'}
    >>> encoded_data = task_func(data)
    >>> isinstance(encoded_data, str)
    True
    """

```
