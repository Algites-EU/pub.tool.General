from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdValueConstraints:
    """Scalar and array constraints; decimal bounds retain exact precision."""
    data_type: str | None = None
    minimum: str | None = None
    maximum: str | None = None
    exclusive_minimum: bool = False
    exclusive_maximum: bool = False
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: tuple[str, ...] = ()
    min_items: int | None = None
    max_items: int | None = None

    def __post_init__(self):
        """Reject impossible cardinality and length intervals at the canonical boundary."""
        for name in ('min_items', 'max_items', 'min_length', 'max_length'):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise ValueError(f'{name} must be a non-negative integer')
        if self.min_items is not None and self.max_items is not None and self.min_items > self.max_items:
            raise ValueError('min_items exceeds max_items')
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('Inconsistent length restriction: min_length exceeds max_length')
