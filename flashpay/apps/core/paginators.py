from typing import List, Tuple, Union

from rest_framework.pagination import CursorPagination


class CustomCursorPagination(CursorPagination):

    ordering: Union[str, List[str], Tuple[str, ...]] = "-created_at"


class TimeStampOrderedCustomCursorPagination(CursorPagination):

    ordering: Union[str, List[str], Tuple[str, ...]] = "-timestamp"
