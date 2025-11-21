"""
Custom exceptions
"""


class BaseAppException(Exception):
    """Base application exception"""
    pass


class ServiceCallException(BaseAppException):
    """Service call failed exception"""
    pass


class DatabaseException(BaseAppException):
    """Database exception"""
    pass



