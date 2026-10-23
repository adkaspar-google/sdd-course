"""
A collection of update operations for TinyDB.

They are used for updates like this:

>>> db.update(delete('foo'), where('foo') == 2)

This would delete the ``foo`` field from all documents where ``foo`` equals 2.
"""

def delete(field):
    """
    Delete a given field from the document.
    """
    pass

def add(field, n):
    """
    Add ``n`` to a given field in the document.
    """
    pass

def subtract(field, n):
    """
    Subtract ``n`` to a given field in the document.
    """
    pass

def set(field, val):
    """
    Set a given field to ``val``.
    """
    pass

def increment(field):
    """
    Increment a given field in the document by 1.
    """
    pass

def decrement(field):
    """
    Decrement a given field in the document by 1.
    """
    pass