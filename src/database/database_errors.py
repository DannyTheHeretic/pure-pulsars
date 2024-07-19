class NullUserError(TypeError):
    """User Doesn't exist in firebase database."""

    def __init__(self) -> None:
        super().__init__("User doesn't exist")
