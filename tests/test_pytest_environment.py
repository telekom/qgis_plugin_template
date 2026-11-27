# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Deutsche Telekom Technik GmbH
# SPDX-License-Identifier: GPL-3.0-only
""" Test temporary pytest environment variables. """

import os

from pathlib import Path

import pytest

from ..test import (apply_pytest_environment_variables,
                    load_pytest_environment_variables,
                    restore_pytest_environment_variables)


def test_pytest_environment_variables_restore(tmp_path: Path):
    """ Restore existing and previously missing environment variables. """
    existing_name = "PYTEST_ENV_RESTORE_EXISTING"
    missing_name = "PYTEST_ENV_RESTORE_MISSING"

    env_file = tmp_path / "pytest.env"
    env_file.write_text(
        "[pytest-environment-variables]\n"
        f"{existing_name}=new-value\n"
        f"{missing_name}=100%\n",
        encoding="utf-8")

    variables = load_pytest_environment_variables(env_file)

    os.environ[existing_name] = "old-value"
    os.environ.pop(missing_name, None)
    previous_state = apply_pytest_environment_variables(variables)

    try:
        assert os.environ[existing_name] == "new-value"
        assert os.environ[missing_name] == "100%"
    finally:
        restore_pytest_environment_variables(previous_state)

    assert os.environ[existing_name] == "old-value"
    assert missing_name not in os.environ
    os.environ.pop(existing_name, None)


def test_pytest_environment_variables_require_section(tmp_path: Path):
    """ Reject env files without the pytest environment section. """
    env_file = tmp_path / "invalid.env"
    env_file.write_text("[other]\nKEY=value\n", encoding="utf-8")

    with pytest.raises(ValueError, match="pytest-environment-variables"):
        load_pytest_environment_variables(env_file)
