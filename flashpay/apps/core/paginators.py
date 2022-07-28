from rest_framework.pagination import CursorPagination


class CustomCursorPagination(CursorPagination):

    ordering = "-created_at"


class TimeStampOrderedCustomCursorPagination(CursorPagination):

    ordering = "-timestamp"
