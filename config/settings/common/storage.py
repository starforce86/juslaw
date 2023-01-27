# Django Storages
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Make boto3 storage return objects over `http`
# It will allow google to index page
# More: http://www.eliotk.net/05/30/force-http-with-django-storages-and-s3boto/
AWS_S3_SECURE_URLS = True

# Set to False to remove query parameter authentication from generated URLs.
AWS_QUERYSTRING_AUTH = False

# Set Access Control List to public-read
# The AllUsers group gets READ access.
AWS_DEFAULT_ACL = 'public-read'

# Upload parameters for s3 objects
AWS_S3_OBJECT_PARAMETERS = dict(
    # On link objects will be downloaded, not opened(request from front end)
    ContentDisposition='attachment'
)
