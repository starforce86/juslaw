from rest_framework import permissions


class IsNotSharedFolder(permissions.BasePermission):
    """Check if folder is shared or not."""

    def has_object_permission(self, request, view, obj):
        """Forbid operation if it is shared folder."""
        return not (not obj.is_template and obj.is_shared)


class IsNotAdminTemplate(permissions.BasePermission):
    """Check if folder is not admin template."""

    def has_object_permission(self, request, view, obj):
        """Forbid operation if it is admin template resource."""
        return not obj.is_global_template


class IsNotPersonalRootTemplateFolder(permissions.BasePermission):
    """Check if folder is not root attorney template folder."""

    def has_object_permission(self, request, view, obj):
        """Forbid operation if it is root attorney template folder."""
        return not obj.is_root_personal_template
