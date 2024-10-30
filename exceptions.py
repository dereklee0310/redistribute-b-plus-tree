"""
Custom Exceptions.
"""


class LeftRedistributeError(Exception):
    """Raise when left distribution fail."""

    pass


class RotateError(Exception):
    """Raise when right rotation fail."""

    pass


class RemoveError(Exception):
    """Raise when key is not found in B+ tree."""

    pass
