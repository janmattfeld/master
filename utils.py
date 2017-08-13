def create_uuid(start=None):
    """Create a UUID with optionally specified beginning"""

    import uuid

    if start:
        return "{text}-{uuid}".format(text=start, uuid=uuid.uuid4())
    else:
        return uuid.uuid4()
