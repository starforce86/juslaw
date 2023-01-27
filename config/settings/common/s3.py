from s3direct.api.keys import S3KeyWithUUID

from apps.utils.s3_direct.keys import S3KeyWithUUIDFolder

from .docusign import DOCUSIGN_AVAILABLE_MIME_TYPES

IMAGE_MIME_TYPES = ('image/jpeg', 'image/png')
AUDIO_MIME_TYPES = (
    'audio/wav',
    'audio/x-wav',
    'audio/mpeg',
    'audio/mp4',
    'audio/aac',
    'audio/aacp',
    'audio/ogg',
    'audio/webm',
    'audio/flac',
)

# S3 direct upload destinations
S3DIRECT_DESTINATIONS = {
    'user_avatars': {
        'key': S3KeyWithUUID('users/avatars/'),
        'allowed': IMAGE_MIME_TYPES,
        'acl': 'public-read',
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
    'attorney_registration_attachments': {
        'key': S3KeyWithUUIDFolder(
            'public/attorney_registration_attachments'
        ),
        'acl': 'public-read',
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
    'attorney_posts': {
        'key': S3KeyWithUUIDFolder(
            'public/attorney_posts'
        ),
        'acl': 'public-read',
        'allowed': IMAGE_MIME_TYPES,
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
    'forum_icons': {
        'key': S3KeyWithUUID('forums/icons/'),
        'auth': lambda user: user.is_authenticated,
        'allowed': ['image/jpeg', 'image/png'],
        'acl': 'public-read',
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
    'documents': {
        'key': S3KeyWithUUIDFolder('documents'),
        'auth': lambda user: user.is_authenticated,
        'acl': 'public-read',
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
    'esign': {
        'key': S3KeyWithUUIDFolder('esign'),
        'auth': lambda user: user.is_authenticated,
        'allowed': DOCUSIGN_AVAILABLE_MIME_TYPES,
        'acl': 'public-read',
        'content_length_range': (0, 25000000),  # 25 MB
        'content_disposition': 'attachment',
    },
    'voice_consents': {
        'key': S3KeyWithUUIDFolder('public/voice_consents'),
        'auth': lambda user: user.is_authenticated,
        'allowed': AUDIO_MIME_TYPES,
        'acl': 'public-read',
        'content_length_range': (0, 25000000),  # 25 MB
        'content_disposition': 'attachment',
    },
    # folder to store Firebase chats images
    'chats_images': {
        'key': S3KeyWithUUIDFolder('chats_images'),
        'auth': lambda user: user.is_authenticated,
        'acl': 'public-read',
        'content_length_range': (0, 20000000),  # 20 MB
        'content_disposition': 'attachment',
    },
}

DEFAULT_DESTINATION = 'user_avatars'
AWS_IS_MINIO = False
