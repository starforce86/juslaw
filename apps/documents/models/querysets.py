from django.db.models import Q, QuerySet

from apps.users.models import AppUser


class ResourceQuerySet(QuerySet):
    """QuerySet for `Resource` model."""

    def root_resources(self):
        """Get root resources."""
        return self.filter(parent=None)

    def available_for_user(self, user: AppUser):
        """Get resources, which user owns."""
        from apps.business.models import Matter

        available_matters = Matter.objects.all().available_for_user(user) \
            .values('id')
        if user.is_attorney:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters) |
                Q(is_template=True, owner=None)
            )
        elif user.is_client:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters)
            )
        else:
            qs = self.filter(
                Q(owner=user) |
                Q(matter_id__in=available_matters) |
                Q(is_template=True, owner=None)
            )
        # matter__shared_links Creates duplicates
        # It generates `right join`
        return qs.distinct()

    def private_resources(self, user: AppUser):
        """Get user's private resources.

        Private resources is resources that belongs to user and not
        related to anything(like matter for example).

        """
        return self.available_for_user(user).filter(matter=None).exclude(
            is_template=True, owner=None
        )

    def global_templates(self):
        """Get resources, which are admin templates"""
        return self.filter(
            is_template=True, owner=None
        )


class FolderQuerySet(ResourceQuerySet):
    """QuerySet for `Folder` model."""

    def available_for_user(self, user: AppUser):
        """Get resources, which user owns."""
        qs = super().available_for_user(user)
        # Show for client only shared folders
        return qs

    def root_admin_template_folder(self):
        """Get root admin template folder."""
        return self.get(
            is_template=True, owner__isnull=True, parent__isnull=True
        )


class DocumentQuerySet(ResourceQuerySet):
    """QuerySet for `Document` model."""

    def available_for_user(self, user: AppUser):
        """Get resources, which user owns."""
        qs = super().available_for_user(user)
        # Show for client only documents in shared folders
        return qs
