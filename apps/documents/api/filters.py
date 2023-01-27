from django_filters import rest_framework as filters

from apps.business.models import Matter
from apps.users.models import AppUser, Attorney

from ...documents import models


class ResourceFilter(filters.FilterSet):
    """Filter fields for `Resource` model."""

    owner = filters.ModelMultipleChoiceFilter(
        field_name='owner', queryset=AppUser.objects.all()
    )
    matter = filters.ModelMultipleChoiceFilter(
        field_name='matter', queryset=Matter.objects.all()
    )
    matter__attorney = filters.ModelMultipleChoiceFilter(
        field_name='matter__attorney', queryset=Attorney.objects.all()
    )
    matter__client = filters.ModelMultipleChoiceFilter(
        field_name='matter__client', queryset=AppUser.objects.all()
    )
    parent = filters.ModelMultipleChoiceFilter(
        field_name='parent', queryset=models.Folder.objects.all()
    )
    shared_with = filters.ModelMultipleChoiceFilter(
        field_name='shared_with', queryset=AppUser.objects.all()
    )
    title__icontains = filters.CharFilter(
        field_name='title', lookup_expr='icontains'
    )
    title__istartswith = filters.CharFilter(
        field_name='title', lookup_expr='istartswith'
    )
    private = filters.BooleanFilter(
        method='filter_private',
    )
    is_template = filters.BooleanFilter(
        field_name='is_template',
    )
    is_vault = filters.BooleanFilter(
        field_name='is_vault',
    )
    is_global_template = filters.BooleanFilter(
        method='filter_is_global_template',
    )

    def filter_private(self, queryset, name, value):
        """Filter private user's resources.

        If value `true` was passed to filter, we filter queryset to return
        private user's resources.

        """
        if value:
            return queryset.private_resources(user=self.request.user)
        return queryset

    def filter_is_global_template(self, queryset, name, value):
        """Filter global templates resources.

        If value `true` was passed to filter and user is attorney,
        we filter queryset to return global templates resources.

        """
        if value and self.request.user.is_attorney:
            return queryset.global_templates()
        return queryset
