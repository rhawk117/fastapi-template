



from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Select


@dataclass(slots=True)
class PageParams:
    page_number: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page_number - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


ColDirection = Literal['asc', 'desc']

@dataclass(slots=True)
class SortOrder:
    direction: ColDirection = 'asc'

    def apply(self, query: Select, col: Any):
        if self.direction == 'asc':
            return query.order_by(query.order_by(col.asc())) # type: ignore
        elif self.direction == 'desc':
            return query.order_by(query.order_by(col.desc())) # type: ignore
        else:
            raise ValueError(f"Invalid sort direction: {self.direction}")


