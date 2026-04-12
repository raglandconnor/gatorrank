class CommentServiceError(Exception):
    """Base class for comment-domain service failures."""


class CommentNotFoundError(CommentServiceError):
    """Raised when the requested comment does not exist."""


class CommentProjectNotFoundError(CommentServiceError):
    """Raised when the requested project cannot accept or expose comments."""


class CommentForbiddenError(CommentServiceError):
    """Raised when the actor cannot perform the requested comment action."""
