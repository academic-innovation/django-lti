from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

import pytest

from lti_tool.decorators import lti_launch_required


class TestLtiLaunchRequired:
    """Tests for the lti_launch_required decorator."""

    @staticmethod
    def make_request(*, is_absent):
        request = RequestFactory().get("/")
        request.lti_launch = SimpleNamespace(is_absent=is_absent)  # type: ignore[attr-defined]
        return request

    def test_sync_launch_present(self):
        calls = []

        @lti_launch_required
        def view(request):
            calls.append(request)
            return "response"

        request = self.make_request(is_absent=False)
        assert view(request) == "response"
        assert calls == [request]

    def test_sync_launch_absent(self):
        calls = []

        @lti_launch_required
        def view(request):
            calls.append(request)
            return "response"

        with pytest.raises(PermissionDenied):
            view(self.make_request(is_absent=True))
        assert calls == []

    @pytest.mark.asyncio
    async def test_async_launch_present(self):
        calls = []

        @lti_launch_required
        async def view(request):
            calls.append(request)
            return "response"

        request = self.make_request(is_absent=False)
        assert await view(request) == "response"
        assert calls == [request]

    @pytest.mark.asyncio
    async def test_async_launch_absent(self):
        calls = []

        @lti_launch_required
        async def view(request):
            calls.append(request)
            return "response"

        with pytest.raises(PermissionDenied):
            await view(self.make_request(is_absent=True))
        assert calls == []
