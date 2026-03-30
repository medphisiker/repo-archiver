"""Тесты CLI и получения пароля для `repo-archiver`."""

from __future__ import annotations

import argparse
import os
import unittest
from unittest.mock import patch

from repo_archiver.cli import PasswordError, prompt_for_password, resolve_password, validate_password


class PromptForPasswordTests(unittest.TestCase):
    """L1: тесты интерактивного ввода и валидации пароля."""

    def test_prompt_for_password_returns_utf8_bytes_on_confirm_match(self) -> None:
        """Возвращает пароль в байтах, когда подтверждение совпадает."""
        with patch("repo_archiver.cli.getpass.getpass", side_effect=["секрет", "секрет"]):
            self.assertEqual(prompt_for_password(), "секрет".encode("utf-8"))

    def test_prompt_for_password_rejects_empty_password(self) -> None:
        """Отклоняет пустой пароль."""
        with patch("repo_archiver.cli.getpass.getpass", side_effect=["", ""]):
            with self.assertRaisesRegex(PasswordError, "не может быть пустым"):
                prompt_for_password()

    def test_prompt_for_password_rejects_mismatched_confirmation(self) -> None:
        """Отклоняет несовпадающее подтверждение."""
        with patch("repo_archiver.cli.getpass.getpass", side_effect=["one", "two"]):
            with self.assertRaisesRegex(PasswordError, "не совпадают"):
                prompt_for_password()

    def test_validate_password_rejects_empty_bytes(self) -> None:
        """Отклоняет пустой пароль из неинтерактивных источников."""
        with self.assertRaisesRegex(PasswordError, "--password"):
            validate_password(b"", "--password")


class ResolvePasswordTests(unittest.TestCase):
    """L1: тесты разрешения источника пароля."""

    def setUp(self) -> None:
        self.config = {
            "encryption": {
                "enabled": True,
                "password_env": "ARCHIVE_PASSWORD",
            }
        }

    def test_resolve_password_prefers_prompt_over_all_other_sources(self) -> None:
        """`--password-prompt` имеет максимальный приоритет."""
        args = argparse.Namespace(
            password_prompt=True,
            password="cli-secret",
            password_env="OTHER_ENV",
        )
        with patch("repo_archiver.cli.prompt_for_password", return_value=b"prompt-secret"):
            self.assertEqual(resolve_password(args, self.config), b"prompt-secret")

    def test_resolve_password_uses_cli_password(self) -> None:
        """Использует пароль из `--password`."""
        args = argparse.Namespace(
            password_prompt=False,
            password="cli-secret",
            password_env=None,
        )
        self.assertEqual(resolve_password(args, self.config), b"cli-secret")

    def test_resolve_password_uses_explicit_password_env(self) -> None:
        """Использует пароль из `--password-env`."""
        args = argparse.Namespace(
            password_prompt=False,
            password=None,
            password_env="TEST_ARCHIVE_PASSWORD",
        )
        with patch.dict(os.environ, {"TEST_ARCHIVE_PASSWORD": "env-secret"}, clear=False):
            self.assertEqual(resolve_password(args, self.config), b"env-secret")

    def test_resolve_password_falls_back_to_config_password_env(self) -> None:
        """Использует переменную окружения из конфигурации при отсутствии CLI overrides."""
        args = argparse.Namespace(
            password_prompt=False,
            password=None,
            password_env=None,
        )
        with patch.dict(os.environ, {"ARCHIVE_PASSWORD": "config-secret"}, clear=False):
            self.assertEqual(resolve_password(args, self.config), b"config-secret")

    def test_resolve_password_returns_none_when_config_encryption_disabled(self) -> None:
        """Возвращает `None`, когда шифрование в конфиге выключено."""
        args = argparse.Namespace(
            password_prompt=False,
            password=None,
            password_env=None,
        )
        self.assertIsNone(resolve_password(args, {"encryption": {"enabled": False}}))


if __name__ == "__main__":
    unittest.main()
