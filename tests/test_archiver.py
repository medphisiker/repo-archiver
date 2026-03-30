"""Интеграционные и E2E тесты AES-шифрования для `repo-archiver`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import pyzipper

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from repo_archiver.archiver import EncryptedZipError, _enable_aes_encryption, create_archive


class ArchiveEncryptionTests(unittest.TestCase):
    """L2/L3: проверка metadata и реального чтения зашифрованного архива."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.repo_dir = self.temp_path / "repo"
        self.repo_dir.mkdir()
        (self.repo_dir / "keep.txt").write_text("secret payload", encoding="utf-8")
        (self.repo_dir / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (self.repo_dir / "ignored.txt").write_text("ignored content", encoding="utf-8")
        (self.repo_dir / ".env").write_text("TOKEN=123", encoding="utf-8")
        hidden_dir = self.repo_dir / ".config"
        hidden_dir.mkdir()
        (hidden_dir / "secret.txt").write_text("hidden secret", encoding="utf-8")
        self.output_path = self.temp_path / "encrypted.zip"
        self.config = {
            "compression": {"method": "deflated", "level": 9},
            "gitignore": {"enabled": True, "paths": [".gitignore"]},
            "encryption": {"enabled": True, "password_env": "ARCHIVE_PASSWORD"},
            "force_include": [],
            "force_exclude": [],
            "output": {"filename": "encrypted.zip", "directory": str(self.temp_path)},
        }

    def test_enable_aes_encryption_rejects_empty_password(self) -> None:
        """L2: helper шифрования отклоняет пустой пароль."""
        target = self.temp_path / "empty-password.zip"
        with pyzipper.AESZipFile(target, "w", compression=pyzipper.ZIP_DEFLATED) as archive:
            with self.assertRaisesRegex(EncryptedZipError, "не может быть пустым"):
                _enable_aes_encryption(archive, b"")

    def test_create_archive_marks_entries_as_encrypted(self) -> None:
        """L2: созданный архив содержит encrypted flag и AES extra data."""
        files_added, _ = create_archive(
            self.repo_dir,
            self.output_path,
            self.config,
            verbose=False,
            password=b"super-secret",
        )

        self.assertEqual(files_added, 4)
        with zipfile.ZipFile(self.output_path, "r") as archive:
            info = archive.getinfo("keep.txt")
            self.assertTrue(info.flag_bits & 0x1)
            self.assertIn(b"\x01\x99", info.extra)
            self.assertNotIn("ignored.txt", archive.namelist())

    def test_create_archive_includes_dotfiles_and_hidden_dirs(self) -> None:
        """L3: скрытые файлы и директории попадают в архив при force_include."""
        self.config["force_include"] = [".env", ".config"]
        create_archive(
            self.repo_dir,
            self.output_path,
            self.config,
            verbose=False,
            password=b"super-secret",
        )

        with pyzipper.AESZipFile(self.output_path, "r") as archive:
            archive.setpassword(b"super-secret")
            self.assertEqual(archive.read(".env").decode("utf-8"), "TOKEN=123")
            self.assertEqual(archive.read(".config/secret.txt").decode("utf-8"), "hidden secret")

    def test_create_archive_includes_dotfiles_with_dot_slash_force_include(self) -> None:
        """L3: `force_include` с префиксом `./` сохраняет dotfiles и скрытые каталоги."""
        self.config["force_include"] = ["./.env", "./.config"]
        create_archive(
            self.repo_dir,
            self.output_path,
            self.config,
            verbose=False,
            password=b"super-secret",
        )

        with pyzipper.AESZipFile(self.output_path, "r") as archive:
            archive.setpassword(b"super-secret")
            self.assertEqual(archive.read(".env").decode("utf-8"), "TOKEN=123")
            self.assertEqual(archive.read(".config/secret.txt").decode("utf-8"), "hidden secret")

    def test_create_archive_requires_password_to_read_payload(self) -> None:
        """L3: без пароля чтение невозможно, с паролем — успешно."""
        create_archive(
            self.repo_dir,
            self.output_path,
            self.config,
            verbose=False,
            password=b"super-secret",
        )

        with pyzipper.AESZipFile(self.output_path, "r") as archive:
            with self.assertRaises(RuntimeError):
                archive.read("keep.txt")

        with pyzipper.AESZipFile(self.output_path, "r") as archive:
            archive.setpassword(b"super-secret")
            payload = archive.read("keep.txt").decode("utf-8")
            self.assertEqual(payload, "secret payload")


class CliEndToEndTests(unittest.TestCase):
    """L4: полный CLI сценарий архивации с AES-шифрованием."""

    def test_cli_creates_aes_archive_from_password_env(self) -> None:
        """CLI создает AES-архив, который читается только с правильным паролем."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repo_dir = temp_path / "repo"
            repo_dir.mkdir()
            (repo_dir / "sample.txt").write_text("hello from cli", encoding="utf-8")
            (repo_dir / ".gitignore").write_text("", encoding="utf-8")
            (repo_dir / ".env").write_text("FROM=CLI", encoding="utf-8")

            hidden_dir = repo_dir / ".config"
            hidden_dir.mkdir()
            (hidden_dir / "secret.txt").write_text("cli hidden", encoding="utf-8")

            config_path = repo_dir / "archive_config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "compression": {"method": "deflated", "level": 9},
                        "gitignore": {"enabled": True, "paths": [".gitignore"]},
                        "encryption": {"enabled": True, "password_env": "ARCHIVE_PASSWORD"},
                        "force_include": [".env", ".config"],
                        "force_exclude": [],
                        "output": {"filename": "cli-encrypted.zip", "directory": "."},
                    }
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env.update({
                "PYTHONPATH": str(SRC_ROOT),
                "ARCHIVE_PASSWORD": "cli-secret",
            })

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "repo_archiver",
                    "-r",
                    str(repo_dir),
                    "-c",
                    str(config_path),
                    "--quiet",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            archive_path = repo_dir / "cli-encrypted.zip"
            self.assertTrue(archive_path.exists())

            with pyzipper.AESZipFile(archive_path, "r") as archive:
                with self.assertRaises(RuntimeError):
                    archive.read("sample.txt")

            with pyzipper.AESZipFile(archive_path, "r") as archive:
                archive.setpassword(b"cli-secret")
                self.assertEqual(archive.read("sample.txt").decode("utf-8"), "hello from cli")
                self.assertEqual(archive.read(".env").decode("utf-8"), "FROM=CLI")
                self.assertEqual(archive.read(".config/secret.txt").decode("utf-8"), "cli hidden")


if __name__ == "__main__":
    unittest.main()
