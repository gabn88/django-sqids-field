.. image:: https://github.com/nshafer/django-sqids-field/actions/workflows/tests.yml/badge.svg?branch=master
    :target: https://github.com/gabn88/django-sqids-field/actions/workflows/tests.yml?query=branch%3Amaster
.. image:: https://badge.fury.io/py/django-sqids-field.svg
    :target: https://badge.fury.io/py/django-sqids-field

Django Sqid Field
====================

A custom Model Field that uses the `Sqids <http://sqids.org/>`_ `library <https://pypi.python.org/pypi/sqids/>`_
to obfuscate an IntegerField or AutoField. It can be used in new models or dropped in place of an existing IntegerField,
explicit AutoField, or an automatically generated AutoField.

Features
--------

* Stores IDs as integers in the database
* Allows lookups and filtering by sqid string or Sqid object and (optionally) integer.
* Can enable integer lookups globally or per-field
* Can be used as sort key
* Allows specifying a salt, min_length and alphabet globally
* Supports custom *salt*, *min_length*, *alphabet*, *prefix* and *allow_int_lookup* settings per field
* Allows prefixing sqids with custom string, e.g. `prefix="user_"` for sqids like "user_h6ks82g"
* Can drop-in replace an existing IntegerField (SqidField) or AutoField (SqidAutoField)
* Supports "Big" variants for large integers: BigSqidField, BigSqidAutoField
* Supports Django 3.2 setting `DEFAULT_AUTO_FIELD = 'sqids_field.BigSqidAutoField'`
* Supports Django REST Framework Serializers
* Supports exact ID searches in Django Admin when field is specified in search_fields.
* Supports common filtering lookups, such as ``__iexact``, ``__contains``, ``__icontains``, though matching is the same as ``__exact``.
* Supports subquery lookups with ``field__in=queryset``
* Supports other lookups: `isnull`, `gt`, `gte`, `lt` and `lte`.
* Supports hashing operations so the fields can be used in Dictionaries and Sets.

Requirements
------------

This module is tested and known to work with:

* Python 3.7, 3.8, 3.9, 3.10
* Django 3.2, 4.0
* Sqids 1.3
* Django REST Framework 3.13

*Please Note*: Python 2.x is at its end of life and is no longer supported.

Installation
------------

Install the package (preferably in a virtualenv):

.. code-block:: bash

    $ pip install django-sqids-field

Configure a global SALT for all SqidFields to use by default in your settings.py. (*Note*: Using a global salt for all
fields will result in IDs from different fields/models being the same. If you want to have unique sqid strings for the
same id, then also configure per-field salts as described in Field Parameters below.)

.. code-block:: python

    SQID_FIELD_SALT = "a long and secure salt value that is not the same as SECRET_KEY"
    # Note: You can generate a secure key with:
    #     from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())

Add it to your model

.. code-block:: python

    from sqids_field import SqidField

    class Book(models.Model):
        reference_id = SqidField()

Migrate your database

.. code-block:: bash

    $ ./manage.py makemigrations
    $ ./manage.py migrate

Basic Usage
-----------

Use your field like you would any other, for the most part. You can assign integers:

.. code-block:: python

    >>> b = Book()
    >>> b.reference_id = 123
    >>> b.reference_id
    Sqid(123): OwLxW8D

You can assign valid sqids. It's valid only if it can be decoded into an integer based on your settings:

.. code-block:: python

    >>> b.reference_id = 'r8636LO'
    >>> b.reference_id
    Sqid(456): r8636LO

You can access your field with either sqid strings or Sqid objects:

.. code-block:: python

    >>> Book.objects.filter(reference_id='OwLxW8D')
    <QuerySet [<Book:  (OwLxW8D)>]>
    >>> b = Book.objects.get(reference_id='OwLxW8D')
    >>> b
    <Book:  (OwLxW8D)>
    >>> h = b.reference_id
    >>> h
    Sqid(123): OwLxW8D
    >>> Book.objects.filter(reference_id=h)
    <Book:  (OwLxW8D)>

You can lookup objects with integers if you set ``SQID_FIELD_ALLOW_INT_LOOKUP = True`` or ``allow_int_lookup=True``
as a parameter to the field.

.. code-block:: python

    reference_id = SqidField(allow_int_lookup=True)

Now integer lookups are allowed. Useful if migrating an existing AutoField to a SqidAutoField, but you need to allow
lookups with older integers.

.. code-block:: python

    >>> Book.objects.filter(reference_id=123)
    <QuerySet [<Book:  (OwLxW8D)>]>

By default, the objects returned from a SqidField are an instance of the class Sqid (this can be disabled globally
or per-field), and allow basic access to the original integer or the sqid:

.. code-block:: python

    >>> from sqids_field import Sqid
    >>> h = Sqid(123)
    >>> h.id
    123
    >>> h.sqid
    'Mj3'
    >>> print(h)
    Mj3
    >>> repr(h)
    'Sqid(123): Mj3'

Sqid Auto Field
-----------------

Along with ``SqidField`` there is also a ``SqidAutoField`` that works in the same way, but that auto-increments just
like an ``AutoField``.

.. code-block:: python

    from sqids_field import SqidAutoField

    class Book(models.Model):
        serial_id = SqidAutoField(primary_key=True)

The only difference is that if you don't assign a value to it when you save, it will auto-generate a value from your
database, just as an AutoField would do. Please note that ``SqidAutoField`` inherits from ``AutoField`` and there can
only be one ``AutoField`` on a model at a time.

.. code-block:: python

    >>> b = Book()
    >>> b.save()
    >>> b.serial_id
    Sqid(1): AJEM7LK

It can be dropped into an existing model that has an auto-created AutoField (all models do by default) as long as you
give it the same name and set ``primary_key=True``. So if you have this model:

.. code-block:: python

    class Author(models.Model):
        name = models.CharField(max_length=40)

Then Django has created a field for you called 'id' automatically. We just need to override that by specifying our own
field with *primary_key* set to True.

.. code-block:: python

    class Author(models.Model):
        id = SqidAutoField(primary_key=True)
        name = models.CharField(max_length=40)

And now you can use the 'id' or 'pk' attributes on your model instances:

.. code-block:: python

    >>> a = Author.objects.create(name="John Doe")
    >>> a.id
    Sqid(60): N8VNa8z
    >>> Author.objects.get(pk='N8VNa8z')
    <Author: Author object>

In Django 3.2 a new setting, "DEFAULT_AUTO_FIELD" was added to change all auto-generated AutoFields to a specific class.
This is fully supported with django-sqids-field, and can be enabled with:

.. code-block:: python

    DEFAULT_AUTO_FIELD = 'sqids_field.SqidAutoField'
    DEFAULT_AUTO_FIELD = 'sqids_field.BigSqidAutoField'

Care must be given, as this will alter ALL models in your project. Usually you would only set this in a new project.
Also, since this changes the auto-generated field, only global settings will be used for that field. If you desire
specific settings for different models, then using this setting is not advised.

Global Settings
---------------

SQID_FIELD_SALT
~~~~~~~~~~~~~~~~~

You can optionally set a global Salt to be used by all SqidFields and SqidAutoFields in your project. Do not use the
same string as your SECRET_KEY, as this could lead to your SECRET_KEY being exposed to an attacker.
Please note that changing this value will cause all SqidFields to change their values, and any previously published
IDs will become invalid.
Can be overridden by the field definition if you desire unique sqid strings for a given field, as described in
Field Parameters below.

:Type:    string
:Default: ""
:Note:    The upstream sqids-python library [only considers the first 43 characters of the salt](https://github.com/davidaurelio/sqids-python/issues/43).
:Example:
    .. code-block:: python

        SQID_FIELD_SALT = "a long and secure salt value that is not the same as SECRET_KEY"

SQID_FIELD_MIN_LENGTH
~~~~~~~~~~~~~~~~~~~~~~~

Default minimum length for (non-Big) SqidField and AutoSqidField.
It is suggested to use 7 for SqidField and SqidAutoField, so that all possible values
(up to 2147483647) are the same length.

:Type:    integer
:Default: 7
:Example:
    .. code-block:: python

        SQID_FIELD_MIN_LENGTH = 20

SQID_FIELD_BIG_MIN_LENGTH
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default minimum length for BigSqidField and BigSqidAutoField.
It is suggested to use 13 for BigSqidField and BigSqidAutoField, so that all possible values
(up to 9223372036854775807) are the same length.

:Type:    integer
:Default: 13
:Example:
    .. code-block:: python

        SQID_FIELD_BIG_MIN_LENGTH = 30

SQID_FIELD_ALPHABET
~~~~~~~~~~~~~~~~~~~~~~~

The default alphabet to use for characters in generated Sqids strings. Must be at least 16 unique characters.

:Type:    string
:Default: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
:Example:
    .. code-block:: python

        SQID_FIELD_ALPHABET = "0123456789abcdef"

SQID_FIELD_ALLOW_INT_LOOKUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allow lookups or fetches of fields using the underlying integer that's stored in the database.
Disabled by default to prevent users from being to do a sequential scan of objects by pulling objects by
integers (1, 2, 3) instead of Sqid strings ("Ba9p1AG", "7V9gk9Z", "wro12zm").
Can be overridden by the field definition.

:Type:    boolean
:Default: False
:Example:
    .. code-block:: python

        SQID_FIELD_ALLOW_INT_LOOKUP = True

SQID_FIELD_LOOKUP_EXCEPTION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default any invalid sqid strings or integer lookups when integer lookups are turned off will result in an
EmptyResultSet being returned. Enable this to instead throw a ValueError exception (similar to the behavior prior to 2.0).

:Type:    boolean
:Default: False
:Example:
    .. code-block:: python

        SQID_FIELD_LOOKUP_EXCEPTION = True

SQID_FIELD_ENABLE_SQID_OBJECT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default behavior is to return an instance of the Sqid object (described below) in each instance of your Model.
This makes it possible to get both the integer and sqid version of the field. However, other django modules, serializers,
etc may be confused and not know how to handle a Sqid object, so you can turn them off here. Instead, a string
of the sqid will be returned, and a new attribute with the suffix `_sqid` will be created on each instance with the
Sqid object. So if you have `key = SqidField(...)` then `key_sqid` will be created on each instance.
Can be overriden by the field definition.

:Type:    boolean
:Default: True
:Example:
    .. code-block:: python

        SQID_FIELD_ENABLE_SQID_OBJECT = False

SQID_FIELD_ENABLE_DESCRIPTOR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default a Sqid*Field on a model will replace the original value returned from the database with a Descriptor
that attempts to convert values that are set on that field of an instance with a new Sqid object (or string if
ENABLE_SQID_OBJECT is False), regardless if you set an integer or a valid sqid. For the most part this is
completely invisible and benign, however if you have issues due to this descriptor, you can disable it here, or
on the field, and the raw value will not be replaced with the Descriptor.
Can be overriden by the field definition.


:Type:    boolean
:Default: True
:Example:
    .. code-block:: python

        SQID_FIELD_ENABLE_DESCRIPTOR = False



Field Parameters
----------------

Besides the standard field options, there are settings you can tweak that are specific to SqidField and
AutoSqidField.

**Please note** that changing any of the values for ``salt``, ``min_length``, ``alphabet`` or ``prefix`` *will* affect
the obfuscation of the integers that are stored in the database, and will change what are considered "valid" sqids.
If you have links or URLs that include your SqidField values, then they will stop working after changing any of these
values. It's highly advised that you don't change any of these settings once you publish any references to your field.

salt
~~~~

Local overridable salt for sqids generated specifically for this field.
Set this to a unique value for each field if you want the IDs for that field to be different to the same IDs
on another field. e.g. so that `book.id = Sqid(5): 0Q8Kg9r` and `author.id = Sqid(5): kp0eq0V`.
Suggestion: `fieldname = SqidField(salt="modelname_fieldname_" + settings.SQID_FIELD_SALT)`
See SQID_FIELD_SALT above.

:Type:    string
:Default: settings.SQID_FIELD_SALT, ""
:Note:    The upstream sqids-python library [only considers the first 43 characters of the salt](https://github.com/davidaurelio/sqids-python/issues/43).
:Example:
    .. code-block:: python

        reference_id = SqidField(salt="Some salt value")

min_length
~~~~~~~~~~

Generate sqid strings of this minimum length, regardless of the value of the integer that is being encoded.
This defaults to 7 for the field since the maximum IntegerField value can be encoded in 7 characters with
the default *alphabet* setting of 62 characters.

:Type:     int
:Default:  7
:Example:
    .. code-block:: python

        reference_id = SqidField(min_length=15)

alphabet
~~~~~~~~

The set of characters to generate sqids from. Must be at least 16 characters.

:Type:    string of characters
:Default: Sqids.ALPHABET, which is "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
:Example:
    .. code-block:: python

        # Only use numbers and lower-case letters
        reference_id = SqidField(alphabet="0123456789abcdefghijklmnopqrstuvwxyz")

prefix
~~~~~~

An optional string prefix that will be prepended to all generated sqids. Also affects validation, so only sqids
that have this prefix will be considered correct.

:Type:    String
:Default: ""
:Example:
    .. code-block:: python

        # Including the type of id in the id itself:
        reference_id = SqidField(prefix="order_")

allow_int_lookup
~~~~~~~~~~~~~~~~

Local field override for default global on whether or not integer lookups for this field should be allowed.
See SQID_FIELD_ALLOW_INT_LOOKUP above.

:Type:    boolean
:Default: settings.SQID_FIELD_ALLOW_INT_LOOKUP, False
:Example:
    .. code-block:: python

        reference_id = SqidField(allow_int_lookup=True)


enable_sqid_object
~~~~~~~~~~~~~~~~~~~~

Local field override for whether or not to return Sqid objects or plain strings.
Can be safely changed without affecting any existing sqids.
See SQID_FIELD_ENABLE_SQID_OBJECT above.

:Type:    boolean
:Default: settings.SQID_FIELD_ENABLE_SQID_OBJECT, True
:Example:
    .. code-block:: python

        reference_id = SqidField(enable_sqid_object=False)

enable_descriptor
~~~~~~~~~~~~~~~~~

Local field override for whether or not to use the Descriptor on instances of the field.
Can be safely changed without affecting any existing sqids.
See SQID_FIELD_ENABLE_DESCRIPTOR above.

:Type:    boolean
:Default: settings.SQID_FIELD_ENABLE_DESCRIPTOR, True
:Example:
    .. code-block:: python

        reference_id = SqidField(enable_descriptor=False)


Sqid Class
------------

Operations with a SqidField or SqidAutoField return a ``Sqid`` object (unless disabled).
This simple class does the heavy lifting of converting integers and sqid strings back and forth.
There shouldn't be any need to instantiate these manually.

Methods
~~~~~~~

\__init__(value, salt="", min_length=0, alphabet=Sqids.ALPHABET, prefix="", sqids=None):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:value: **REQUIRED** Integer you wish to *encode* or sqid you wish to *decode*
:salt: Salt to use. **Default**: "" (empty string)
:min_length: Minimum length of encoded sqid string. **Default**: 0
:alphabet: The characters to use in the encoded sqid string. **Default**: Sqids.ALPHABET
:prefix: String prefix prepended to sqid strings. **Default**: "" (empty string)
:sqids: Instance of sqids.Sqids to use for encoding/decoding instead of instantiating another.

Read-Only Properties
~~~~~~~~~~~~~~~~~~~~

id
^^

:type: Int
:value: The *decoded* integer

sqid
^^^^^^

:type: String
:value: The *encoded* sqid string

sqids
^^^^^^^

:type: Sqids()
:value: The instance of the Sqids class that is used to *encode* and *decode*

prefix
^^^^^^

:type: String
:value: The prefix prepended to sqid strings


Django REST Framework Integration
=================================

If you wish to use a SqidField or SqidAutoField with a DRF ModelSerializer, there is one extra step that you must
take. Automatic declaration of any Sqid*Fields will result in an ImproperlyConfigured exception being thrown. You
must explicitly declare them in your Serializer, as there is no way for the generated field to know how to work with
a Sqid*Field, specifically what 'salt', 'min_length' and 'alphabet' to use, and can lead to very difficult errors or
behavior to debug, or in the worst case, corruption of your data. Here is an example:

.. code-block:: python

    from rest_framework import serializers
    from sqids_field.rest import SqidSerializerCharField


    class BookSerializer(serializers.ModelSerializer):
        reference_id = SqidSerializerCharField(source_field='library.Book.reference_id')

        class Meta:
            model = Book
            fields = ('id', 'reference_id')


    class AuthorSerializer(serializers.ModelSerializer):
        id = SqidSerializerCharField(source_field='library.Author.id', read_only=True)

        class Meta:
            model = Author
            fields = ('id', 'name')

The ``source_field`` allows the SqidSerializerCharField to copy the 'salt', 'min_length' and 'alphabet' settings from
the given field at ``app_name.model_name.field_name`` so that it can be defined in just one place. Explicit settings are
also possible:

.. code-block:: python

    reference_id = SqidSerializerCharField(salt="a different salt", min_length=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

If nothing is given, then the field will use the same global settings as a Sqid*Field. It is very important that the
options for the serializer field matches the model field, or else strange errors or data corruption can occur.

SqidSerializerCharField will serialize the value into a Sqids string, but will deserialize either a Sqids string or
integer and save it into the underlying Sqid*Field properly. There is also a SqidSerializerIntegerField that will
serialize the Sqids into an un-encoded integer as well.

Primary Key Related Fields
--------------------------

Any models that have a ForeignKey to another model that uses a Sqid*Field as its Primary Key will need to explicitly
define how the
`PrimaryKeyRelatedField <http://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield>`_
should serialize and deserialize the resulting value using the ``pk_field`` argument. If you don't you will get an error
such as "Sqid(60): N8VNa8z is not JSON serializable". We have to tell DRF how to serialize/deserialize Sqid*Fields.

For the given ``Author`` model defined
above that has an ``id = SqidAutoField(primary_key=True)`` set, your BookSerializer should look like the following.

.. code-block:: python

    from rest_framework import serializers
    from sqids_field.rest import SqidSerializerCharField


    class BookSerializer(serializers.ModelSerializer):
        author = serializers.PrimaryKeyRelatedField(
            pk_field=SqidSerializerCharField(source_field='library.Author.id'),
            read_only=True)

        class Meta:
            model = Book
            fields = ('id', 'author')

Make sure you pass the source field to the SqidSerializer*Field so that it can copy the 'salt', 'min_length' and 'alphabet'
as described above.

This example sets ``read_only=True`` but you can explicitly define a ``queryset`` or override ``get_queryset(self)`` to allow
read-write behavior.

.. code-block:: python

    author = serializers.PrimaryKeyRelatedField(
        pk_field=SqidSerializerCharField(source_field='library.Author.id'),
        queryset=Author.objects.all())

For a ManyToManyField, you must also remember to pass ``many=True`` to the ``PrimaryKeyRelatedField``.


SqidSerializerCharField
-------------------------

Serialize a Sqid\*Field to a Sqids string, de-serialize either a valid Sqids string or integer into a
Sqid\*Field (if allow_int_lookup is enabled.)

Parameters
~~~~~~~~~~

source_field
^^^^^^^^^^^^

A 3-field dotted notation of the source field to load matching 'salt', 'min_length' and 'alphabet' settings from. Must
be in the format of "app_name.model_name.field_name". Example: "library.Book.reference_id".

salt, min_length, alphabet, prefix, allow_int_lookup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See `Field Parameters`_


SqidSerializerIntegerField
----------------------------

Serialize a Sqid\*Field to an integer, de-serialize either a valid Sqids string or integer into a
Sqid\*Field. See `SqidSerializerCharField`_ for parameters.

*Please Note*: This field will always serialize to an integer and thus will also de-serialize integers into valid
objects, regardless of the `allow_int_lookup` setting.

Development
===========

Here are some rough instructions on how to set up a dev environment to develop this module. Modify as needed. The
sandbox is a django project that uses django-sqid-id, and is useful for developing features with.

- ``git clone https://github.com/nshafer/django-sqids-field.git && cd django-sqids-field``
- ``mkvirtualenv -a . -p /usr/bin/python3 -r sandbox/requirements.txt django-sqids-field``
- ``python setup.py develop``
- ``sandbox/manage.py migrate``
- ``sandbox/manage.py createsuperuser``
- ``sandbox/manage.py loaddata authors books editors``
- ``sandbox/manage.py runserver``
- ``python runtests.py``

For any pull requests, clone the repo and push to it, then create the PR.

To install the latest development version, use:

```
pip install git+https://github.com/nshafer/django-sqids-field.git
```

LICENSE
=======

MIT License. You may use this in commercial and non-commercial projects with proper attribution.
Please see the `LICENSE <https://github.com/nshafer/django-sqids-field/blob/master/LICENSE>`_
