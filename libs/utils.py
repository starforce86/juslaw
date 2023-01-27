import base64
import json
import os
import re
import uuid
from datetime import datetime
from shutil import make_archive
from tempfile import NamedTemporaryFile, TemporaryDirectory
from time import mktime
from typing import Any, Type

from django.utils.safestring import mark_safe

import pytz
from PIL import Image
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer


def get_base_url() -> str:
    """Get frontend current domain."""
    if 'local' in os.environ.get('ENVIRONMENT', ''):
        current_site = 'http://localhost:3000/'
    elif 'development' in os.environ.get('ENVIRONMENT', ''):
        current_site = 'https://app.dev.jus-law.com/'
    elif 'staging' in os.environ.get('ENVIRONMENT', ''):
        current_site = 'https://app.staging.jus-law.com/'
    elif 'prod' in os.environ.get('ENVIRONMENT', ''):
        current_site = 'https://app.juslaw.com/'
    else:
        current_site = ''
    return current_site


def get_random_filename(filename):
    """Get random filename.

    Generation random filename that contains unique identifier and
    filename extension like: ``photo.jpg``.

    If extension is too long (we had issue with that), replace it with
    UUID too

    Args:
        filename (str): Name of file.

    Returns:
        new_filename (str): ``9841422d-c041-45a5-b7b3-467179f4f127.ext``.

    """
    path = str(uuid.uuid4())
    ext = os.path.splitext(filename)[1]
    if len(ext) > 15:
        ext = str(uuid.uuid4())

    return ''.join([path, ext.lower()])


def struct_time_to_timezoned(struct_time):
    """Convert ``struct_time`` object to timezoned ``datetime.datetime`` .

    Result is intended to be passed to django ``DateTimeField`` with timezone

    """
    timestamp = mktime(struct_time)
    utc_date = datetime.utcfromtimestamp(timestamp)
    timezoned = utc_date.replace(tzinfo=pytz.utc)
    return timezoned


def get_file_extension(url):
    """Extract file extension from path/URL.

    Args:
        url (str): Path to the file

    Returns:
        String: extension of the file

    Example:
        'dir/subdir/file.ext' -> 'ext'

    """
    return os.path.splitext(url)[1][1:]


class NewImage(object):
    """Context manager to create temporary image file.

    Example:
        with NewImage() as img:
            self.image = img

    """

    def __init__(self, width=500, height=500, ext='PNG', color='green',
                 prefix=None):
        self.width = width
        self.height = height
        self.color = color
        self.ext = ext
        self.prefix = prefix

    def __enter__(self):
        image = Image.new('RGB', (self.width, self.height), self.color)
        self.tmp_file = NamedTemporaryFile(
            delete=False,
            suffix='.{0}'.format(self.ext.lower()),
            prefix=self.prefix,
        )
        image.save(self.tmp_file.name, self.ext)
        return self.tmp_file

    def __exit__(self, *args):
        os.unlink(self.tmp_file.name)


class ZipArchive(object):
    """Context manager to create temporary zip archive with files.

    Structure of files and directories in archive:
        some_file.doc (if `file_without_folder` is True)
        /some_folder
            some_music_file.mp3
            some_image_file.png

    """

    def __init__(self, file_without_folder=False, file_with_invalid_ext=False):
        self.file_without_folder = file_without_folder
        self.file_with_invalid_ext = file_with_invalid_ext

    def __enter__(self):
        self.tmp_dir = TemporaryDirectory()
        self.tmp_subdir = TemporaryDirectory(dir=self.tmp_dir.name)

        self.tmp_zip = NamedTemporaryFile()
        self.tmp_file = NamedTemporaryFile(
            dir=self.tmp_subdir.name, suffix='.png')
        self.another_tmp_file = NamedTemporaryFile(
            dir=self.tmp_subdir.name, suffix='.mp3')

        # create file without folder
        if self.file_without_folder:
            self.tmp_file_without_parent_dir = NamedTemporaryFile(
                dir=self.tmp_dir.name,
                suffix='.mp3'
            )

        if self.file_with_invalid_ext:
            self.tmp_file_with_invalid_ext = NamedTemporaryFile(
                dir=self.tmp_subdir.name,
                suffix='.undefined'
            )

        self.image = Image.new('RGB', (1280, 720), 'green')
        self.image.save(self.tmp_file.name, 'PNG')

        self.zip_file = make_archive(self.tmp_zip.name, 'zip',
                                     self.tmp_dir.name)

        return {
            'tmp_zip': self.tmp_zip,
            'tmp_dir': self.tmp_dir,
            'tmp_file': self.tmp_file,
            'tmp_subdir': self.tmp_subdir,
            'zip_file': self.zip_file,
        }

    def __exit__(self, *args):
        self.tmp_file.close()
        self.another_tmp_file.close()

        if self.file_without_folder:
            self.tmp_file_without_parent_dir.close()

        if self.file_with_invalid_ext:
            self.tmp_file_with_invalid_ext.close()

        self.tmp_subdir.cleanup()
        self.tmp_dir.cleanup()
        return True


def get_object_fullname(obj):
    """Get fully qualified class name of an object in Python.

    May be used to dump object's class to string and later use to restore it
    using `import_string`.

    WARNING: simplest implementation used, may not work in some cases
    """
    return '.'.join([obj.__module__ + "." + obj.__class__.__name__])


def bytes_to_base_64(data: bytes) -> str:
    """Shortcut to convert simple `bytes` data to base64."""
    return base64.b64encode(data).decode('ascii')


def get_filename_from_path(path: str) -> str:
    """Shortcut to extract filename from `path`."""
    full_filename = os.path.basename(path)
    return full_filename


def json_prettified(json_instance: dict) -> str:
    """Function to display pretty version of json in html.

    Shamelessly copied from:
    https://www.pydanny.com/pretty-formatting-json-django-admin.html

    """

    # Convert the data to sorted, indented JSON
    response = json.dumps(json_instance, sort_keys=True, indent=2)

    # Truncate the data. Alter as needed
    response = response[:5000]

    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')

    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)


def get_lookup_value(instance: Any, lookup: str) -> Type:
    """Get instance related to `lookup` value.

    Usage:
        > get_lookup_value(<Invoice instance>, 'matter.attorney')
        > <Attorney instance>

    """
    attrs = lookup.split('.')
    value = instance
    for attr in attrs:
        value = getattr(value, attr)
    return value


def get_datetime_from_str(date: str, format: str = '%Y-%m-%d') -> datetime:
    """Prepare datetime object from str with a desired format."""
    return datetime.strptime(date, format)


def invalidate_cached_property(instance: Any, property_name: str):
    """Invalidate cached property value."""
    try:
        del instance.__dict__[property_name]
    except KeyError:
        pass


def get_latest_version(changelog_filepath: str) -> str:
    """Get latest version from changelog file.

    Args:
        changelog_filepath (str):Path to changelog file

    Raises:
        ValueError: if we couldn't find any versions in changelog file

    """
    version_regex = r'(?!### )\d{1,2}\.\d{1,2}\.\d{1,3}'
    re_rule = re.compile(version_regex)

    try:
        open_file = open(f'docs/{changelog_filepath}')
    except FileNotFoundError:
        open_file = open(changelog_filepath)

    with open_file as file:
        for line in file:
            search = re_rule.search(line)
            if search:
                return search.group()

    raise ValueError(
        "Incorrect changelog file, couldn't find version number for "
        f"{changelog_filepath}"
    )
