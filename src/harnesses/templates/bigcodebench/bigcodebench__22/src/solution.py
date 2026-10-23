import collections
from itertools import zip_longest
from random import choices

def task_func(l1, l2, K=10):
    """
    Combine two lists by alternating their elements, even if they are of different lengths. 
    Elements from the longer list without a counterpart in the shorter one will be included on their own.
    Then, create a random sample of size K from the combined list, and calculate the frequency of 
    each element in the sample.

    Parameters:
    l1 (list): The first list containing any hashable types.
    l2 (list): The second list containing any hashable types.
    K (int): the size of the random sample from the combined list. Default to 10.

    Returns:
    collections.Counter: An object that counts the frequency of each element in the sample.

    Requirements:
    - collections
    - itertools.zip_longest
    - random.choices

    Example:
    >>> import random
    >>> random.seed(32)
    >>> l1 = list(range(10))
    >>> l2 = list(range(10, 20))
    >>> freq = task_func(l1, l2)
    >>> print(freq)
    Counter({5: 2, 10: 1, 2: 1, 3: 1, 9: 1, 14: 1, 7: 1, 1: 1, 8: 1})
    """
    pass
