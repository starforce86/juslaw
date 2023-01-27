class TransitionFailedException(Exception):
    """Exception raised when we got an error on status transition.

    Examples:
        @transition(
            field=status,
            source=STATUS_SENT,
            target=STATUS_PAID,
            on_error_STATUS_PAYMENT_FAILED,
        )
        def pay(self):
            try:
                services.pay(self)
                obj.save()
            except PaymentException as e:
                raise TransitionFailedException

    """
