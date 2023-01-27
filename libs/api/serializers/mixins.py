from rest_framework import serializers


class UnknownFieldsValidationMixin(object):
    """Mixin for unknown fields validation."""

    def validate(self, attrs):
        """Validate unknown fields.

        Raise an exception in the case submitted 'unknown'
        fields in json request body.

        :param attrs:
            valid fields
        :return:
            attrs or raises Validation exception
        """
        has_unknown_fields = set(self.initial_data.keys()) - set(attrs.keys())

        if has_unknown_fields:
            raise serializers.ValidationError(
                "Unknown fields submitted: " + str(has_unknown_fields))

        return super().validate(attrs)
