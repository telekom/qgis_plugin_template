# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only
""" Tests for loading the repository version info in the plugin template. """

import pytest

from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import Mock

from ..plugin import TEMPLATE_VERSION, PluginTemplate
from ..submodules.base.constants import VersionError, VersionInfo
from ..submodules.base.version import Version
from ..utilities import plugin_migration


def _fake_plugin(repo_xml_path: str, lookup: Callable[..., object]) -> SimpleNamespace:
    """ Return a fake plugin with the attributes used by `load_version_info`.

        :param repo_xml_path: repository url of plugins.xml
        :param lookup: side effect of the mocked version lookup
    """
    return SimpleNamespace(repo_xml_path=repo_xml_path, zip_file_name="plugin.zip", repo_auth_cfg="auth-id",
                           get_repository_version_zipname=Mock(side_effect=lookup),
                           versionRead=SimpleNamespace(emit=Mock()))


def test_load_version_info_without_url() -> None:
    """ Keep the version '-1' (no plugin management) without repository url. """
    fake = _fake_plugin("", lambda *args, **kwargs: None)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version == "-1"
    fake.get_repository_version_zipname.assert_not_called()
    fake.versionRead.emit.assert_called_once_with(fake)


def test_load_version_info_success() -> None:
    """ Store a found version and pass the authcfg to the lookup. """
    info = VersionInfo(Version("1.0.0"), "1.0.0", "abc", None, None)
    fake = _fake_plugin("https://x", lambda *args, **kwargs: info)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version == info.version
    assert fake.repo_commit == "abc"
    fake.get_repository_version_zipname.assert_called_once_with("https://x", "plugin.zip", auth_cfg="auth-id")


def test_load_version_info_returned_error() -> None:
    """ Set the 'Updateserver nicht erreichbar' state for a returned VersionError (e.g. HTTP 401). """
    fake = _fake_plugin("https://x", lambda *args, **kwargs: VersionError("HTTP-Status: 401"))

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version is None
    assert fake.repo_version_error == "HTTP-Status: 401"


def test_load_version_info_raised_error() -> None:
    """ Set the 'Updateserver nicht erreichbar' state for a raised VersionError (unknown authcfg). """
    def lookup(*args: object, **kwargs: object) -> None:
        """ Raise the error of an unknown authcfg.

            :param args: lookup arguments
            :param kwargs: lookup keyword arguments
        """
        raise VersionError("unknown authcfg")

    fake = _fake_plugin("https://x", lookup)

    PluginTemplate.load_version_info(fake)

    assert fake.repo_version is None
    assert fake.repo_version_error == "unknown authcfg"


@pytest.mark.parametrize("saved_version", [None, "no version", 123])
def test_load_template_version_migrates_without_valid_saved_version(monkeypatch: pytest.MonkeyPatch,
                                                                     saved_version: str | int | None) -> None:
    """ Run the migration without a previous version, if no valid template version is saved.

        :param monkeypatch: pytest monkeypatch fixture
        :param saved_version: template version saved in the user profile
    """
    migrate = Mock()
    monkeypatch.setattr(plugin_migration, "migrate", migrate)
    fake = SimpleNamespace(get_option=Mock(return_value=saved_version), set_option=Mock())

    PluginTemplate._PluginTemplate__load_plugin_template_version(fake)

    migrate.assert_called_once_with(fake, Version(TEMPLATE_VERSION), None)
    fake.set_option.assert_called_once_with("PluginTemplateVersion", TEMPLATE_VERSION)


@pytest.mark.parametrize(("saved_version", "should_migrate"), [
    ("1", True), ("1.1", True), ("1.2", False), ("v1.2.0", False), ("1.3", False),
])
def test_load_template_version_compares_saved_version(monkeypatch: pytest.MonkeyPatch, saved_version: str,
                                                      should_migrate: bool) -> None:
    """ Migrate only when the saved template version is older.

        :param monkeypatch: pytest monkeypatch fixture
        :param saved_version: template version saved in the user profile
        :param should_migrate: whether migration is expected
    """
    migrate = Mock()
    monkeypatch.setattr(plugin_migration, "migrate", migrate)
    fake = SimpleNamespace(get_option=Mock(return_value=saved_version), set_option=Mock())

    PluginTemplate._PluginTemplate__load_plugin_template_version(fake)

    if should_migrate:
        migrate.assert_called_once_with(fake, Version(TEMPLATE_VERSION), Version(saved_version))
    else:
        migrate.assert_not_called()
    fake.set_option.assert_called_once_with("PluginTemplateVersion", TEMPLATE_VERSION)
