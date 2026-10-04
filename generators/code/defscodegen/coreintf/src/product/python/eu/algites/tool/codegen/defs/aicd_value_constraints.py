from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdValueConstraints:
    """Scalar family and portable basic constraints; decimal bounds retain exact precision."""
    data_type: str | None = None
    minimum: str | None = None
    maximum: str | None = None
    exclusive_minimum: bool = False
    exclusive_maximum: bool = False
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: tuple[str, ...] = ()
