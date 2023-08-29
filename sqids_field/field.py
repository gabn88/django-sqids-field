from django import forms
from django.core import exceptions, checks
from django.core import validators as django_validators
from django.db import models
from django.db.models import Field
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import widgets as admin_widgets
from sqids import Sqids

from .lookups import SqidExactLookup, SqidIterableLookup
from .lookups import SqidGreaterThan, SqidGreaterThanOrEqual, SqidLessThan, SqidLessThanOrEqual
from .descriptor import SqidDescriptor
from .sqid import Sqid
from .conf import settings
from .validators import SqidMaxValueValidator, SqidMinValueValidator


def _alphabet_unique_len(alphabet):
    return len([x for i, x in enumerate(alphabet) if alphabet.index(x) == i])


class SqidFieldMixin(object):
    default_error_messages = {
        'invalid': _("'%(value)s' value must be a positive integer or a valid Sqids string."),
        'invalid_sqid': _("'%(value)s' value must be a valid Sqids string."),
    }
    exact_lookups = ('exact', 'iexact', 'contains', 'icontains')
    iterable_lookups = ('in',)
    passthrough_lookups = ('isnull',)
    comparison_lookups = {
        'gt': SqidGreaterThan,
        'gte': SqidGreaterThanOrEqual,
        'lt': SqidLessThan,
        'lte': SqidLessThanOrEqual,
    }

    def __init__(self, salt=settings.SQID_FIELD_SALT,
                 min_length=settings.SQID_FIELD_MIN_LENGTH,
                 alphabet=settings.SQID_FIELD_ALPHABET,
                 allow_int_lookup=settings.SQID_FIELD_ALLOW_INT_LOOKUP,
                 enable_sqid_object=settings.SQID_FIELD_ENABLE_SQID_OBJECT,
                 enable_descriptor=settings.SQID_FIELD_ENABLE_DESCRIPTOR,
                 prefix="", *args, **kwargs):
        self.salt = salt
        self.min_length = min_length
        self.alphabet = alphabet
        if _alphabet_unique_len(self.alphabet) < 16:
            raise exceptions.ImproperlyConfigured("'alphabet' must contain a minimum of 16 unique characters")
        self._sqids = Sqids(salt=self.salt, min_length=self.min_length, alphabet=self.alphabet)
        self.allow_int_lookup = allow_int_lookup
        self.enable_sqid_object = enable_sqid_object
        self.enable_descriptor = enable_descriptor
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['min_length'] = self.min_length
        kwargs['alphabet'] = self.alphabet
        kwargs['prefix'] = self.prefix
        return name, path, args, kwargs

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_alphabet_min_length())
        errors.extend(self._check_salt_is_set())
        return errors

    def _check_alphabet_min_length(self):
        if _alphabet_unique_len(self.alphabet) < 16:
            return [
                checks.Error(
                    "'alphabet' must contain a minimum of 16 unique characters",
                    hint="Add more unique characters to custom 'alphabet'",
                    obj=self,
                    id='SqidField.E001',
                )
            ]
        return []

    def _check_salt_is_set(self):
        if self.salt is None or self.salt == "":
            return [
                checks.Warning(
                    "'salt' is not set",
                    hint="Pass a salt value in your field or set settings.SQID_FIELD_SALT",
                    obj=self,
                    id="SqidField.W001",
                )
            ]
        return []

    @cached_property
    def validators(self):
        if self.enable_sqid_object:
            return super().validators
        else:
            # IntegerField will add min and max validators depending on the database we're connecting to, so we need
            # to override them with our own validator that knows how to `clean` the value before doing the check.
            validators_ = super().validators
            validators = []
            for validator_ in validators_:
                if isinstance(validator_, django_validators.MaxValueValidator):
                    validators.append(SqidMaxValueValidator(self, validator_.limit_value, validator_.message))
                elif isinstance(validator_, django_validators.MinValueValidator):
                    validators.append(SqidMinValueValidator(self, validator_.limit_value, validator_.message))
                else:
                    validators.append(validator_)
            return validators

    def encode_id(self, id):
        sqid = self.get_sqid(id)
        if self.enable_sqid_object:
            return sqid
        else:
            return str(sqid)

    def get_sqid(self, id):
        return Sqid(id, salt=self.salt, min_length=self.min_length, alphabet=self.alphabet,
                      prefix=self.prefix, sqids=self._sqids)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.encode_id(value)

    def get_lookup(self, lookup_name):
        if lookup_name in self.exact_lookups:
            return SqidExactLookup
        if lookup_name in self.iterable_lookups:
            return SqidIterableLookup
        if lookup_name in self.comparison_lookups:
            return self.comparison_lookups[lookup_name]
        if lookup_name in self.passthrough_lookups:
            return super().get_lookup(lookup_name)
        return None  # Otherwise, we don't allow lookups of this type

    def to_python(self, value):
        if isinstance(value, Sqid):
            return value
        if value is None:
            return value
        try:
            sqid = self.encode_id(value)
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )
        return sqid

    def get_prep_value(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, Sqid):
            return value.id
        try:
            sqid = self.get_sqid(value)
        except ValueError:
            raise ValueError(self.error_messages['invalid'] % {'value': value})
        return sqid.id

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # if callable(self.prefix):
        #     self.prefix = self.prefix(field_instance=self, model_class=cls, field_name=name, **kwargs)
        if self.enable_descriptor:
            descriptor = SqidDescriptor(field_name=self.attname, salt=self.salt, min_length=self.min_length,
                                          alphabet=self.alphabet, prefix=self.prefix, sqids=self._sqids,
                                          enable_sqid_object=self.enable_sqid_object)
            setattr(cls, self.attname, descriptor)


class SqidCharFieldMixin:
    def formfield(self, **kwargs):
        defaults = {'form_class': forms.CharField}
        defaults.update(kwargs)
        if defaults.get('widget') == admin_widgets.AdminIntegerFieldWidget:
            defaults['widget'] = admin_widgets.AdminTextInputWidget
        if defaults.get('widget') == admin_widgets.AdminBigIntegerFieldWidget:
            defaults['widget'] = admin_widgets.AdminTextInputWidget
        # noinspection PyCallByClass,PyTypeChecker
        return Field.formfield(self, **defaults)


class SqidField(SqidFieldMixin, SqidCharFieldMixin, models.IntegerField):
    description = "A Sqids obscured IntegerField"


class BigSqidField(SqidFieldMixin, SqidCharFieldMixin, models.BigIntegerField):
    description = "A Sqids obscured BigIntegerField"

    def __init__(self, min_length=settings.SQID_FIELD_BIG_MIN_LENGTH, *args, **kwargs):
        super().__init__(min_length=min_length, *args, **kwargs)


class SqidAutoField(SqidFieldMixin, models.AutoField):
    description = "A Sqids obscured AutoField"


class BigSqidAutoField(SqidFieldMixin, models.AutoField):
    # This inherits from AutoField instead of BigAutoField so that DEFAULT_AUTO_FIELD doesn't throw an error
    description = "A Sqids obscured BigAutoField"

    def get_internal_type(self):
        return 'BigAutoField'

    def rel_db_type(self, connection):
        return models.BigIntegerField().db_type(connection=connection)

    def __init__(self, min_length=settings.SQID_FIELD_BIG_MIN_LENGTH, *args, **kwargs):
        super().__init__(min_length=min_length, *args, **kwargs)


# Monkey patch Django REST Framework, if it's installed, to throw exceptions if fields aren't explicitly defined in
# ModelSerializers. Not doing so can lead to hard-to-debug behavior.
try:
    from rest_framework.serializers import ModelSerializer
    from sqid_field.rest import UnconfiguredSqidSerialField

    ModelSerializer.serializer_field_mapping[SqidField] = UnconfiguredSqidSerialField
    ModelSerializer.serializer_field_mapping[BigSqidField] = UnconfiguredSqidSerialField
    ModelSerializer.serializer_field_mapping[SqidAutoField] = UnconfiguredSqidSerialField
    ModelSerializer.serializer_field_mapping[BigSqidAutoField] = UnconfiguredSqidSerialField
except ImportError:
    pass
