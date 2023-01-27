from collections import namedtuple
from typing import Dict, Iterable, Union

import pytest

from apps.business.models import Matter

from ...users import models as user_models
from .. import models


@pytest.fixture
def resource_list_in(
    request,
    resource_mapping: Dict[str, Union[models.Folder, models.Document]]
) -> Iterable[Union[models.Folder, models.Document]]:
    """Get list of resource that should be in queryset."""
    return (resource_mapping[key] for key in request.param)


@pytest.fixture
def resource_list_not_in(
    request,
    resource_mapping: Dict[str, models.Folder]
) -> Iterable[Union[models.Folder, models.Document]]:
    """Get list of resource that shouldn't be in queryset."""
    return (resource_mapping[key] for key in request.param)


class TestResourceQuerySet:
    """Test common ResourceQuerySet methods."""
    queryset_test_arg_names = (
        'user',
        'model',
        'attr_to_check',
        'resource_list_in',
        'resource_list_not_in'
    )
    QuerySetTestArgs = namedtuple('QuerySetTestArgs', queryset_test_arg_names)
    queryset_test_arg_values = (
        QuerySetTestArgs(
            user='client',
            model=models.Folder,
            attr_to_check='available_for_user',
            resource_list_in=('shared_folder',),
            resource_list_not_in=(
                'private_attorney_folder',
                'matter_folder',
                'shared_matter_folder',
                'attorney_template_folder',
                'root_attorney_template_folder',
                'root_admin_template_folder',
                'admin_template_folder'
            ),
        ),
        QuerySetTestArgs(
            user='attorney',
            model=models.Folder,
            attr_to_check='available_for_user',
            resource_list_in=(
                'shared_folder',
                'private_attorney_folder',
                'matter_folder',
                'shared_matter_folder',
                'attorney_template_folder',
                'root_attorney_template_folder',
                'root_admin_template_folder',
                'admin_template_folder'
            ),
            resource_list_not_in=tuple(),
        ),
        QuerySetTestArgs(
            user='client',
            model=models.Folder,
            attr_to_check='private_resources',
            resource_list_in=tuple(),
            resource_list_not_in=(
                'shared_folder',
                'private_attorney_folder',
                'matter_folder',
                'shared_matter_folder',
                'attorney_template_folder',
                'root_attorney_template_folder',
                'root_admin_template_folder',
                'admin_template_folder'
            ),
        ),
        QuerySetTestArgs(
            user='attorney',
            model=models.Folder,
            attr_to_check='private_resources',
            resource_list_in=(
                'private_attorney_folder',
                'attorney_template_folder',
                'root_attorney_template_folder',
            ),
            resource_list_not_in=(
                'shared_folder',
                'matter_folder',
                'shared_matter_folder',
                'root_admin_template_folder',
                'admin_template_folder'
            ),
        ),
        QuerySetTestArgs(
            user='client',
            model=models.Document,
            attr_to_check='available_for_user',
            resource_list_in=('shared_document',),
            resource_list_not_in=(
                'private_attorney_document',
                'matter_document',
                'shared_matter_document',
                'attorney_template_document',
                'admin_template_document'
            ),
        ),
        QuerySetTestArgs(
            user='attorney',
            model=models.Document,
            attr_to_check='available_for_user',
            resource_list_in=(
                'shared_document',
                'private_attorney_document',
                'matter_document',
                'shared_matter_document',
                'attorney_template_document',
                'admin_template_document'
            ),
            resource_list_not_in=tuple(),
        ),
        QuerySetTestArgs(
            user='client',
            model=models.Document,
            attr_to_check='private_resources',
            resource_list_in=tuple(),
            resource_list_not_in=(
                'shared_document',
                'private_attorney_document',
                'matter_document',
                'shared_matter_document',
                'attorney_template_document',
                'admin_template_document'
            ),
        ),
        QuerySetTestArgs(
            user='attorney',
            model=models.Document,
            attr_to_check='private_resources',
            resource_list_in=(
                'private_attorney_document',
                'attorney_template_document',
            ),
            resource_list_not_in=(
                'shared_document',
                'matter_document',
                'shared_matter_document',
                'admin_template_document'
            ),
        ),
    )
    global_queryset_test_arg_names = (
        'model',
        'resource_list_in',
        'resource_list_not_in'
    )
    GlobalQuerySetTestArgs = namedtuple(
        'GlobalQuerySetTestArgs', global_queryset_test_arg_names
    )
    global_queryset_test_arg_values = (
        GlobalQuerySetTestArgs(
            model=models.Folder,
            resource_list_in=(
                'root_admin_template_folder',
                'admin_template_folder',
            ),
            resource_list_not_in=(
                'shared_folder',
                'private_attorney_document',
                'matter_folder',
                'shared_matter_folder',
                'attorney_template_folder',
                'root_attorney_template_folder',
            ),
        ),
        GlobalQuerySetTestArgs(
            model=models.Document,
            resource_list_in=(
                'admin_template_document',
            ),
            resource_list_not_in=(
                'shared_document',
                'private_attorney_document',
                'matter_document',
                'shared_matter_document',
                'attorney_template_document',
            ),
        ),
    )

    @pytest.mark.parametrize(
        argnames=queryset_test_arg_names,
        argvalues=queryset_test_arg_values,
        indirect=True
    )
    def test_queryset_method(
        self,
        user: user_models.AppUser,
        model,
        attr_to_check: str,
        resource_list_in: Iterable[Union[models.Folder, models.Document]],
        resource_list_not_in: Iterable[Union[models.Folder, models.Document]],
        matter

    ):
        """Check common resource queryset methods for both users.

        Attributes:
            attr_to_check: queryset method to check
            resource_list_in: what should return
            resource_list_not_in: what shouldn't return

        """
        for resource in resource_list_in:
            if resource.matter:
                resource.matter.status = Matter.STATUS_OPEN
                resource.matter.save()

        qs = getattr(model.objects, attr_to_check)(user=user)
        for resource in resource_list_in:
            assert resource in qs
        for resource in resource_list_not_in:
            assert resource not in qs

    @pytest.mark.parametrize(
        argnames=global_queryset_test_arg_names,
        argvalues=global_queryset_test_arg_values,
        indirect=True
    )
    def test_global_templates_method(
        self,
        model,
        resource_list_in: Iterable[Union[models.Folder, models.Document]],
        resource_list_not_in: Iterable[Union[models.Folder, models.Document]],
    ):
        """Check `global_templates` method."""
        qs = model.objects.global_templates()
        for resource in resource_list_in:
            assert resource in qs
        for resource in resource_list_not_in:
            assert resource not in qs
