from functools import total_ordering

from sqids import Sqids


def _is_uint(candidate):
    """Returns whether a value is an unsigned integer."""
    return isinstance(candidate, int) and candidate >= 0


def _is_str(candidate):
    """Returns whether a value is a string."""
    return isinstance(candidate, str)


@total_ordering
class Sqid(object):
    def __init__(self, value, salt="", min_length=0, alphabet=Sqids.ALPHABET, prefix="", sqids=None):
        self._salt = salt
        self._min_length = min_length
        self._alphabet = alphabet
        self._prefix = str(prefix)

        # If sqids is provided, it's for optimization only, and should be initialized with the same salt, min_length
        # and alphabet, or else we will run into problems
        self._sqids = sqids or Sqids(salt=self._salt, min_length=self._min_length, alphabet=self._alphabet)
        if not self._valid_sqids_object():
            raise Exception("Invalid sqids.Sqids object")

        if value is None:
            raise ValueError("id must be a positive integer or a valid Sqid string")

        # Check if `value` is an integer and encode it.
        # This presumes sqids will only ever be strings, even if they are made up entirely of numbers
        if _is_uint(value):
            self._id = value
            self._sqid = self.encode(value)
        elif _is_str(value):
            # Verify that it begins with the prefix, which could be the default ""
            if value.startswith(self._prefix):
                value = value[len(self._prefix):]
            else:
                # Check if the given string is all numbers, and encode without requiring the prefix.
                # This is to maintain backwards compatibility, specifically being able to enter numbers in an admin.
                # If a sqid is typed in that happens to be all numbers, without the prefix, then it will be
                # interpreted as an integer and encoded (again).
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise ValueError("value must begin with prefix {}".format(self._prefix))

            # Check if this string is a valid sqid, even if it's made up entirely of numbers
            _id = self.decode(value)
            if _id is None:
                # The given value is not a sqids string, so see if it's a valid string representation of an integer
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise ValueError("value must be a positive integer or a valid Sqid string")

                # Make sure it's positive
                if not _is_uint(value):
                    raise ValueError("value must be a positive integer")

                # We can use it as-is
                self._id = value
                self._sqid = self.encode(value)
            else:
                # This is a valid sqid
                self._id = _id
                self._sqid = value
        elif isinstance(value, int) and value < 0:
            raise ValueError("value must be a positive integer")
        else:
            raise ValueError("value must be a positive integer or a valid Sqid string")

    @property
    def id(self):
        return self._id

    @property
    def sqid(self):
        return self._sqid

    @property
    def prefix(self):
        return self._prefix

    @property
    def sqids(self):
        return self._sqids

    def encode(self, id):
        return self._sqids.encode(id)

    def decode(self, sqid):
        ret = self._sqids.decode(sqid)
        if len(ret) == 1:
            return ret[0]
        else:
            return None

    def _valid_sqids_object(self):
        # The sqids.Sqids class randomizes the alphabet and pulls out separators and guards, thus not being
        # reversible. So all we can test is that the length of the alphabet, separators and guards are equal to the
        # original alphabet we gave it. We could also check that all of the characters we gave it are present, but that
        # seems excessive... this test will catch most errors.
        return self._salt == self._sqids._salt \
            and self._min_length == self._sqids._min_length \
            and len(self._alphabet) == len(self._sqids._alphabet + self._sqids._separators + self._sqids._guards)

    def __repr__(self):
        return "Sqid({}): {}".format(self._id, str(self))

    def __str__(self):
        return self._prefix + self._sqid

    def __int__(self):
        return self._id

    def __long__(self):
        return int(self._id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self._id == other._id and
                self._sqid == other._sqid and
                self._prefix == other._prefix
            )
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, int):
            return int(self) == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self._id < other._id
        if isinstance(other, type(self._id)):
            return self._id < other
        return NotImplemented

    def __len__(self):
        return len(str(self))

    def __sqid__(self):
        return sqid(str(self))

    def __getstate__(self):
        return self._id, self._salt, self._min_length, self._alphabet, self._prefix, self._sqid

    def __setstate__(self, state):
        self._id, self._salt, self._min_length, self._alphabet, self._prefix, self._sqid = state

    def __add__(self, other):
        return self._id + other

    def __sub__(self, other):
        return self._id - other

    def __mul__(self, other):
        return self._id * other

    def __matmul__(self, other):
        raise NotImplementedError("Sqid does not support matrix multiplication")

    def __truediv__(self, other):
        return self._id / other

    def __floordiv__(self, other):
        return self._id // other

    def __mod__(self, other):
        return self._id % other

    def __divmod__(self, other):
        return self.__floordiv__(other), self.__mod__(other)

    def __pow__(self, other, *args):
        return pow(self._id, other, *args)

    def __lshift__(self, other):
        return self._id << other

    def __rshift__(self, other):
        return self._id >> other

    def __and__(self, other):
        return self._id & other

    def __xor__(self, other):
        return self._id ^ other

    def __or__(self, other):
        return self._id | other
