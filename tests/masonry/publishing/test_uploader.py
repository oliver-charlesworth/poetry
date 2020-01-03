import pytest

from poetry.io.null_io import NullIO
from poetry.masonry.publishing.uploader import Uploader
from poetry.masonry.publishing.uploader import UploadError


def test_uploader_properly_handles_400_errors(poetry_factory, http):
    http.register_uri(http.POST, "https://foo.com", status=400, body="Bad request")
    uploader = Uploader(poetry_factory("simple_project"), NullIO())

    with pytest.raises(UploadError) as e:
        uploader.upload("https://foo.com")

    assert "HTTP Error 400: Bad Request" == str(e.value)


def test_uploader_properly_handles_403_errors(poetry_factory, http):
    http.register_uri(http.POST, "https://foo.com", status=403, body="Unauthorized")
    uploader = Uploader(poetry_factory("simple_project"), NullIO())

    with pytest.raises(UploadError) as e:
        uploader.upload("https://foo.com")

    assert "HTTP Error 403: Forbidden" == str(e.value)


def test_uploader_registers_for_appropriate_400_errors(poetry_factory, mocker, http):
    register = mocker.patch("poetry.masonry.publishing.uploader.Uploader._register")
    http.register_uri(
        http.POST, "https://foo.com", status=400, body="No package was ever registered"
    )
    uploader = Uploader(poetry_factory("simple_project"), NullIO())

    with pytest.raises(UploadError):
        uploader.upload("https://foo.com")

    assert 1 == register.call_count
