from datetime import timedelta

from django.db import models
from django.http.response import HttpResponse
from django.template.loader import get_template
from django.utils import timezone

import pdfkit
import tablib


class BaseResource:
    """Used to define common export logic for data export to file."""
    extension = None
    mimetype = None

    def __init__(self, instance: models.Model, ) -> None:
        """Init resource."""
        self.instance = instance

    @property
    def options(self) -> dict:
        """Get different options for file."""
        return {}

    @property
    def filename(self) -> str:
        """Get export filename."""
        now = timezone.now().strftime('%Y-%m-%d')
        model = self.instance._meta.model_name.capitalize()
        return f'{model}_{now}.{self.extension}'

    @property
    def content_disposition(self):
        return f'attachment;filename="{self.filename}"'

    @property
    def content_type(self):
        return f'{self.mimetype}; charset=utf-8'

    def get_export_file_response(self, data: bytes) -> HttpResponse:
        """Shortcut to get HTTP response with exported file

        Method prepares HttpResponse with exported file. This response
        triggers file upload in browser.

        """
        response = HttpResponse(data, content_type=self.mimetype)
        response['Content-Disposition'] = self.content_disposition
        response['Content-Type'] = self.content_type
        return response


class PDFResource(BaseResource):
    """Base class for all PDF related resources which defines export workflow.

    This class handles export to PDF itself and represents common interface for
    it.

    """

    template = None
    mimetype = 'application/pdf'
    extension = 'pdf'

    def __init__(
        self, instance: models.Model, template: str = None, *args, **kwargs
    ) -> None:
        """Force user to set `template` property."""
        super().__init__(instance=instance)
        assert self.template, '`template` should be defined for PDF resource'
        self.instance = instance
        self.template = template or self.template

    def get_template_context(self) -> dict:
        """Get all required for a template data context."""
        return {'object': self.instance}

    @property
    def options(self) -> dict:
        """Method to get different PDF options."""
        return {
            'page-size': 'Letter',
            'encoding': 'UTF-8',
        }

    def export(self) -> bytes:
        """Make resource export in PDF.

        This method simply makes corresponding instance export in a format
        defined by `template`.

        Returns:
            (bytes) PDF as a bytes string

        """
        template = get_template(template_name=self.template)
        context = self.get_template_context()
        html = template.render(context)
        pdf = pdfkit.from_string(html, output_path=False, options=self.options)
        return pdf


class ExcelResource(BaseResource):
    """Base class for excel related resources which defines export workflow.

    This class handles export to all supported by excel formats and represents
    common interface for it.

    """
    extension = None
    mimetype = None
    mimetype_map = {
        'xls': 'application/vnd.ms-excel',
        'xlsx': (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        'csv': 'text/csv'
    }

    def __init__(
        self, instance: models.Model, extension: str
    ) -> None:
        """Force user to set `template` property."""
        super().__init__(instance)
        self.instance = instance
        self.extension = extension
        self.mimetype = self.mimetype_map[extension]

    def convert_to_bytes(self, data: tablib.Dataset) -> bytes:
        """Convert tablib data to bytes with chosen format(extension)"""
        return data.export(self.extension)

    def format_timedelta(self, time: timedelta):
        """Format timedelta for tablib export."""
        if not time:
            return '00:00:00'
        hours, remaining = divmod(time.seconds, 3600)
        hours += 24 * time.days
        minutes, seconds = divmod(remaining, 60)
        return '{hours}:{minutes:02d}:{seconds:02d}'.format(
            hours=hours, minutes=minutes, seconds=seconds
        )
