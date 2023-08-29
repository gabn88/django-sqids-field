import warnings

from django.conf import settings

setattr(settings, 'SQID_FIELD_SALT', getattr(settings, 'SQID_FIELD_SALT', ""))
setattr(settings, 'SQID_FIELD_MIN_LENGTH', getattr(settings, 'SQID_FIELD_MIN_LENGTH', 7))
setattr(settings, 'SQID_FIELD_BIG_MIN_LENGTH', getattr(settings, 'SQID_FIELD_BIG_MIN_LENGTH', 13))
setattr(settings, 'SQID_FIELD_ALPHABET',
        getattr(settings, 'SQID_FIELD_ALPHABET', "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"))
setattr(settings, 'SQID_FIELD_ALLOW_INT_LOOKUP', getattr(settings, 'SQID_FIELD_ALLOW_INT_LOOKUP', False))
setattr(settings, 'SQID_FIELD_LOOKUP_EXCEPTION', getattr(settings, 'SQID_FIELD_LOOKUP_EXCEPTION', False))
setattr(settings, 'SQID_FIELD_ENABLE_SQID_OBJECT', getattr(settings, 'SQID_FIELD_ENABLE_SQID_OBJECT', True))
setattr(settings, 'SQID_FIELD_ENABLE_DESCRIPTOR', getattr(settings, 'SQID_FIELD_ENABLE_DESCRIPTOR', True))

