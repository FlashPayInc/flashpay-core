from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response


class PingView(GenericAPIView):
    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_200_OK)
