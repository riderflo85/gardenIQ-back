class ProtectedException(Exception):
    # TODO: update when translation is done !
    default_message = "This object is used by other objects."

    def __init__(self, *args) -> None:
        if not args:
            args = (self.default_message,)

        super().__init__(*args)


class DisabledProtectedException(ProtectedException):
    # TODO: update when translation is done !
    default_message = "This object is used by other objects and cannot be disabled."


class DeleteProtectedException(ProtectedException):
    # TODO: update when translation is done !
    default_message = "This object is used by other objects and cannot be deleted."
