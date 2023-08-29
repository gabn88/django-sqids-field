from django.core.validators import MaxValueValidator, MinValueValidator


class SqidMaxValueValidator(MaxValueValidator):
    def __init__(self, sqid_field, limit_value, message=None):
        self.sqid_field = sqid_field
        super().__init__(limit_value, message)

    def clean(self, x):
        return self.sqid_field.get_prep_value(x)


class SqidMinValueValidator(MinValueValidator):
    def __init__(self, sqid_field, limit_value, message=None):
        self.sqid_field = sqid_field
        super().__init__(limit_value, message)

    def clean(self, x):
        return self.sqid_field.get_prep_value(x)
