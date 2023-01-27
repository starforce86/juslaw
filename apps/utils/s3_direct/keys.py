import uuid


class S3KeyWithUUIDFolder(object):
    """Prefixed key generator with UUID folder name."""

    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, filename: str) -> str:
        """Return prefixed S3 key.

        Example:
            prefix/a13d0a2e-8391-4d95-8dae-fe312f2769a1/file.jpg

        """
        return f'{self.prefix}/{uuid.uuid4()}/{filename.split("/")[-1]}'
