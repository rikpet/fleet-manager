"""Mock response object from requests"""
from http import HTTPStatus

class MockResponse():
    """Mocking Respons object from python standard library requests"""
    def __init__(self, response: dict, status_code: HTTPStatus) -> None:
        self._response = response
        self._status_code = status_code

    @property
    def status_code(self) -> HTTPStatus:
        """Response HTTP code

        Returns:
            HTTPStatus: Response HTTP code
        """
        return self._status_code

    def json(self) -> dict:
        """Mocks response json endpoint

        Returns:
            dict: Mock response
        """
        return self._response
