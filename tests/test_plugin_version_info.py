# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from types import SimpleNamespace
from unittest.mock import Mock

from pkg_resources import packaging

from ..plugin import PluginTemplate
from ..submodules.base.constants import VersionInfo, VersionError


def _fake_plugin(repo_xml_path: str, lookup) -> SimpleNamespace:
    return SimpleNamespace(repo_xml_path=repo_xml_path, zip_file_name="plugin.zip", repo_auth_cfg="auth-id",
                           get_repository_version_zipname=Mock(side_effect=lookup),
                           versionRead=SimpleNamespace(emit=Mock()))


def test_load_version_info_without_url():
    """Without repository url the version stays '-1' (no plugin management)."""
    fake = _fake_plugin("", lambda *args, **kwargs: None)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version == "-1"
    fake.get_repository_version_zipname.assert_not_called()
    fake.versionRead.emit.assert_called_once_with(fake)


def test_load_version_info_success():
    """A found version is stored and the authcfg is passed to the lookup."""
    info = VersionInfo(packaging.version.parse("1.0.0"), "1.0.0", "abc", None, None)
    fake = _fake_plugin("https://x", lambda *args, **kwargs: info)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version == info.version
    assert fake.repo_commit == "abc"
    fake.get_repository_version_zipname.assert_called_once_with("https://x", "plugin.zip", auth_cfg="auth-id")


def test_load_version_info_returned_error():
    """Returned VersionError (e.g. HTTP 401) leads to 'Updateserver nicht erreichbar' state."""
    fake = _fake_plugin("https://x", lambda *args, **kwargs: VersionError("HTTP-Status: 401"))

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version is None
    assert fake.repo_version_error == "HTTP-Status: 401"


def test_load_version_info_raised_error():
    """Raised VersionError (unknown authcfg) leads to 'Updateserver nicht erreichbar' state."""
    def lookup(*args, **kwargs):
        raise VersionError("unknown authcfg")

    fake = _fake_plugin("https://x", lookup)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version is None
    assert fake.repo_version_error == "unknown authcfg"
