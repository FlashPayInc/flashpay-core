# from typing import Optional

# from rest_framework.request import Request

# from flashpay.apps.core.models import Network


# class CustomRequest(Request):
#     _network: Optional[Network] = None

#     @property
#     def network(self) -> Optional[Network]:
#         return self._network

#     @network.setter
#     def network(self, value: Network) -> None:
#         self._network = value
