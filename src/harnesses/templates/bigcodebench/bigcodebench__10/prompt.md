# BigCodeBench v0.1.2 Task: `BigCodeBench/10`

- Target implementation file: `src/solution.py`
- Target unit test file: `tests/test_solution.py`

## Specification
```python
import numpy as np
import itertools
import random
import statistics

def task_func(T1, RANGE=100):
    """
    Convert elements in 'T1' to integers and create a list of random integers.
    The size of the list is the sum of the integers in `T1`. Calculate and 
    return the mean, median, and mode of the list.
    
    Parameters:
    T1 (tuple of tuples): Each tuple contains string representations of integers which are converted to integers.
    RANGE (int, optional): The upper limit for generating random integers. Default is 100.
    
    Returns:
    tuple: A tuple containing the mean, median, and mode of the generated list of random integers.
           The mean and median are floats, and the mode is an integer. The calculations use the generated
           list whose size is determined by the sum of converted integers from `T1`.
    
    Requirements:
    - numpy
    - itertools
    - random
    - statistics

    Raises:
    statistics.StatisticsError if T1 is empty
    
    Example:
    >>> import random
    >>> random.seed(42)
    >>> T1 = (('13', '17', '18', '21', '32'), ('07', '11', '13', '14', '28'), ('01', '05', '06', '08', '15', '16'))
    >>> stats = task_func(T1)
    >>> print(stats)
    (49.88, 48.0, 20)
    >>> stats = task_func(T1, RANGE=50)
    >>> print(stats)
    (23.773333333333333, 25.0, 15)
    """

```
