class DisableAPIViewMixin:
    attribute_error_msg = "The model {model_name} has no attribute 'is_enable'."

    def enable(self, request, *args, **kwargs) -> None:
        """
        Enables the specified object by calling its `enable` method if it has an `is_enable` attribute.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            AttributeError: If the object does not have an `is_enable` attribute.

        Returns:
            None
        """
        obj = self.get_object()  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(obj, "is_enable"):
            obj.enable()
        else:
            raise AttributeError(self.attribute_error_msg.format(model_name=obj.__class__.__name__))

    def disable(self, request, *args, **kwargs):
        """
        Disable the specified object by calling its `disable` method if it has an `is_enable` attribute.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            AttributeError: If the object does not have an `is_enable` attribute.

        Returns:
            None
        """
        obj = self.get_object()  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(obj, "is_enable"):
            obj.disable()
        else:
            raise AttributeError(self.attribute_error_msg.format(model_name=obj.__class__.__name__))
