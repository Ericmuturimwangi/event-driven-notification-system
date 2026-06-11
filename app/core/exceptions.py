class NotificationError(Exception):
    """Base class for notification failures. """

class RetryableNotificationError(NotificationError):
    """Transient Failure """

class PermanentNotificationError(NotificationError):

    """ Permanent Failure """

class CircuitOpenError(NotificationError):
    """
    The circuit breaker for this channel is OPEN 
    """