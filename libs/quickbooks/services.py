"""Different extra methods and shortcuts."""


def create_qb_object(qb_class, **kwargs):
    """Create simple quickbook object."""
    qb_object = qb_class()
    for key, value in kwargs.items():
        setattr(qb_object, key, value)
    return qb_object
