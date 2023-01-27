class ActionPermissionsMixin(object):
    """Mixin which allows to define specific permissions per actions

    It requires filled ``permissions_map`` attribute

    It should be used for ``ModelViewSet``

    Examples:

        class NoteViewSet(ActionPermissionsMixin, viewsets.ModelViewSet):
            queryset = Note.objects.all()
            serializer_class = NoteSerializer
            base_permission_classes = [IsAuthenticated, IsConferenceAttendee]
            permissions_map = {
                'list': base_permission_classes + [IsOwner],
                'update': base_permission_classes + [CanModerate, IsOwner],
                # default permissions for all other actions
                # if 'default' section is not defined
                'default': base_permission_classes + [CanModerate],
            }
    """

    permissions_map = None

    def get_permissions(self):
        """Returns permissions list for current ``.action`` attribute value.

        It returns permissions list from `permissions_map` using view's action
        as key. If view doesn't have permissions_map or permissions_map doesn't
        have `default` key, we use `get_viewset_permissions` if view have this
        attr, or otherwise we use `super().get_permissions()`.

        Returns:
            list: list of permissions for related action
        """
        permissions = super().get_permissions()
        if hasattr(self, 'get_viewset_permissions'):
            permissions = self.get_viewset_permissions()

        # if action is not in permission_map - add view
        # `base_permission_classes` and extra ones from `permission_classes`
        # as default
        is_permissions_map_set = isinstance(self.permissions_map, dict)

        if not is_permissions_map_set:
            return permissions

        if self.action in self.permissions_map:
            return self.get_permissions_from_map(self.action)

        if 'default' in self.permissions_map:
            return self.get_permissions_from_map('default')

        return permissions

    def get_permissions_from_map(self, action):
        """Return permissions list from permission map."""
        return [p() for p in self.permissions_map[action]]


class ActionSerializerMixin(object):
    """Mixin which allows to define specific serializers per action.

    It requires filled ``serializers_map`` attribute

    It should be used for ``ModelViewSet``

    Examples:

        class NoteViewSet(ActionSerializerMixin, viewsets.ModelViewSet):
            queryset = Note.objects.all()
            serializer_class = NoteSerializer
            serializers_map = {
                'update': serializers.UpdateNoteSerializer,
                'partial_update': serializers.UpdateNoteSerializer,
            }
    """
    serializers_map = None

    def get_serializer_class(self):
        """Get serializer for view's action.

        First we try to find corresponding `action` in `serializer_map` and
        in case if current method is absent in `serializer_map` we return
        `default` from `serializer_map`(if default is not set we use
        serializer_class from `super().get_serializer_class()`).

        Example:
            serializer_map = {
                'update': serializers.UpdateLeadSerializer,
                'partial_update': serializers.UpdateLeadSerializer,
            }

        """
        serializer_class = super().get_serializer_class()
        is_serializers_map_set = isinstance(self.serializers_map, dict)

        if not is_serializers_map_set:
            return serializer_class

        if self.action in self.serializers_map:
            return self.serializers_map.get(self.action)

        if 'default' in self.serializers_map:
            return self.serializers_map.get('default')

        return serializer_class
