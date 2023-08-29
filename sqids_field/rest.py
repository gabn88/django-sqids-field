from django.apps import apps
from django.core import exceptions
from django.utils.translation import gettext_lazy as _

from sqids import Sqids
from rest_framework import fields

from sqids_field.conf import settings
from sqids_field.sqid import Sqid
from sqids_field.lookups import _is_int_representation


class UnconfiguredSqidSerialField(fields.Field):
    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        raise exceptions.ImproperlyConfigured(
            "The field '{field_name}' on {parent} must be explicitly declared when used with a ModelSerializer".format(
                field_name=field_name, parent=parent.__class__.__name__))


class SqidSerializerMixin(object):
    usage_text = "Must pass a SqidField, SqidAutoField or 'app_label.model.field'"
    default_error_messages = {
        'invalid': _("value must be a positive integer or a valid Sqids string."),
        'invalid_sqid': _("'{value}' value must be a valid Sqids string."),
    }

    def __init__(self, **kwargs):
        self.sqid_salt = kwargs.pop('salt', settings.SQID_FIELD_SALT)
        self.sqid_min_length = kwargs.pop('min_length', settings.SQID_FIELD_MIN_LENGTH)
        self.sqid_alphabet = kwargs.pop('alphabet', settings.SQID_FIELD_ALPHABET)
        self.allow_int_lookup = kwargs.pop('allow_int_lookup', settings.SQID_FIELD_ALLOW_INT_LOOKUP)
        self.prefix = kwargs.pop('prefix', "")
        self._sqids = kwargs.pop('sqids', None)

        source_field = kwargs.pop('source_field', None)
        if source_field:
            from sqid_field import SqidField, BigSqidField, SqidAutoField, BigSqidAutoField
            if isinstance(source_field, str):
                try:
                    app_label, model_name, field_name = source_field.split(".")
                except ValueError:
                    raise ValueError(self.usage_text)
                model = apps.get_model(app_label, model_name)
                source_field = model._meta.get_field(field_name)
            elif not isinstance(source_field, (SqidField, BigSqidField, SqidAutoField, BigSqidAutoField)):
                raise TypeError(self.usage_text)
            self.sqid_salt = source_field.salt
            self.sqid_min_length = source_field.min_length
            self.sqid_alphabet = source_field.alphabet
            self.allow_int_lookup = source_field.allow_int_lookup
            self.prefix = source_field.prefix
            self._sqids =source_field._sqids
        if not self._sqids:
            self._sqids = Sqids(salt=self.sqid_salt, min_length=self.sqid_min_length,
                                    alphabet=self.sqid_alphabet)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return Sqid(value, salt=self.sqid_salt, min_length=self.sqid_min_length,
                          alphabet=self.sqid_alphabet, prefix=self.prefix, sqids=self._sqids)
        except ValueError:
            self.fail('invalid_sqid', value=data)


class SqidSerializerCharField(SqidSerializerMixin, fields.CharField):
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        sqid = super().to_internal_value(data)
        if isinstance(data, int) and not self.allow_int_lookup:
            self.fail('invalid_sqid', value=data)
        if isinstance(data, str) and not self.allow_int_lookup:
            # Make sure int lookups are not allowed, even if prefixed, unless the
            # given value is actually a sqid made up entirely of numbers.
            without_prefix = data[len(self.prefix):]
            if _is_int_representation(without_prefix) and without_prefix != sqid.sqid:
                self.fail('invalid_sqid', value=data)
        return sqid


class SqidSerializerIntegerField(SqidSerializerMixin, fields.IntegerField):
    def to_representation(self, value):
        return int(value)

