#!/usr/bin/env python
"""Configuration Manager class

Merges configuration settings from the following sources, lowest to highest priority:

    1. Default values provided
    2. Configuration file
    3. Environment variables
    4. CLI arguments

Example usage:

  @dataclass
  class ClassDefaults:
      timeout: int = 400
      flags: bool = False
      hostname: "example.com"

  config = ConfigManager(
    defaults = ClassDefaults,
    config_file = "/home/User/.app.ini",
    env_prefix = "APP_",
    cli_args = parsed_args,
  )
  config.get("timeout")

Copyright (c) 2026 Dan Griffin

Licensed under the GNU General Public License v3.0+
(see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
# PYTHON_ARGCOMPLETE_OK


import argparse
import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigManager:
    """The Configuration Manager to merge settings from multiple sources.

    Which fields and their types are determined by the defaults you pass in.
    This class contains no predefined settings.
    """

    def __init__(
        self,
        defaults: Union[Dict[str, Any], Any],
        config_file: Optional[Union[str, Path]] = None,
        ini_section: Optional[str] = None,
        env_prefix: Optional[str] = None,
        cli_args: Optional[Union[argparse.Namespace, Dict[str, Any]]] = None,
    ):
        """Initialize the configuration manager.

        Args:
            defaults: (dict[str, Any] | Any): Dictionary of default atribute names
                and their values.
            config_file (str | Path | None): Path to (optional) configuration file.
            ini_section (str| None): Optional ini section to read settings from.
                If None, all sections are read and parsed.
            env_prefix (str | None): Optional environment variable prefix string
                e.g. "FOO_" causes the "id" attribute to read from "FOO_ID".
            cli_args: (argparse.Namespace | dict[str, Any] | None): Optional parsed CLI
                args to overwrite other values.
        """
        self.defaults = self._load_defaults(defaults)
        self.config_file = config_file
        self.ini_section = ini_section
        self.env_prefix = env_prefix
        self.cli_args = cli_args

        self._env = self._load_env()
        self._config = self._load_config(self.config_file)
        self._cli = self._load_cli(cli_args)

        self._merged = self._merge()

    def _load_defaults(self, defaults: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """Convert an object with attributes to a dictionary.

        Args:
            defaults(dict[str, Any] | Any): The defaults passed to ConfigManager.
                Either a dict or an object with attributes.

        Returns:
            dict[str, Any]: A normalized dictionary of defaults.

        Raises:
            TypeError: If defaults is not a dict nor has a __dict__.
        """
        if isinstance(defaults, dict):
            return dict(defaults)
        if hasattr(defaults, "__dict__"):
            return dict(vars(defaults))
        raise TypeError(
            "defaults must be a dict or an object with attributes "
            "(dataclass instance, SimpleNamespace, etc.)"
        )

    def _load_config(
        self, path: Optional[Union[str, Path]], section: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read settings from configuration file.

        Args:
            path (str | Path | None): Path to the config file.
            section (str | None): Section to read settings from.  If None, merge
                settings from all sections.

        Returns:
            dict[str, Any]: parsed config values.
        """
        if not path:
            return {}
        config_file = Path(path)
        if not config_file.exists():
            return {}
        parser = configparser.ConfigParser()
        parser.read(path)

        if section is not None:
            read_sections = [section] if parser.has_section(section) else []
        else:
            read_sections = parser.sections()

        result = {}

        if not read_sections and section is None and parser.defaults():
            read_sections = [configparser.DEFAULTSECT]

        for sec in read_sections:
            items = (
                parser.defaults().items()
                if sec == configparser.DEFAULTSECT
                else parser.items(sec)
            )

            for key, value in items:
                default_value = self.defaults.get(key)
                result[key] = (
                    self._type_cast(value, default_value)
                    if key in self.defaults
                    else value
                )
        return result

    def _load_env(self) -> Dict[str, Any]:
        """Read settings from environment variables.

        Returns:
            dict[str, Any]: Dictionary of settings who had an environment variable
                with an optional prefix.
        """
        env_conf = {}
        prefix = self.env_prefix or ""
        for key, default_val in self.defaults.items():
            env_key = f"{prefix}{key.upper()}"
            if env_key in os.environ:
                env_conf[key] = self._type_cast(os.environ[env_key], default_val)
        return env_conf

    def _load_cli(
        self, cli_args: Optional[Union[argparse.Namespace, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Read settings provided from a CLI tool.

        Args:
            cli_args (argparse.Namespace | dict[str, Any] | None): already parsed
                cli args or None.

        Returns:
            dict[str, Any]: Dictionary of settings provided from the command line.
        """
        if cli_args is None:
            return {}
        cli_dict = (
            vars(cli_args)
            if isinstance(cli_args, argparse.Namespace)
            else dict(cli_args)
        )
        return {
            key: val
            for key, val in cli_dict.items()
            if val is not None and key in self.defaults
        }

    def _type_cast(self, value: str, default_value: Any) -> Any:
        """Convert a string to match its default type.

        Args:
            value (str): The raw string value.
            default_value (Any): The default for the key. Its type is used
                to convert the string value.

        Returns:
            Any: The converted value or the original string
        """
        if isinstance(default_value, bool):
            return value.strip().lower() in ("1", "true", "yes", "on")
        if isinstance(default_value, int):
            try:
                return int(value)
            except ValueError:
                return value
        if isinstance(default_value, float):
            try:
                return float(value)
            except ValueError:
                return value
        if isinstance(default_value, (list, tuple)):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    def _merge(self) -> Dict[str, Any]:
        """Merge defaults, config file, env vars, and command line arguments.

        Returns:
            dict[str, Any]: Final merged settings.
        """
        merged = dict(self.defaults)
        merged.update(self._config)
        merged.update(self._env)
        merged.update(self._cli)
        return merged

    def get(self, key: str) -> Any:
        """Get a setting's value

        Args:
            key (str): The setting's name.
        """
        return self._merged.get(key)

    def source(self, key: str) -> str:
        """Return where the setting is being defined from.

        Returns:
            str: Returns either "cli", "env", "config", "default" or "none".
        """
        if key in self._cli:
            return "cli"
        if key in self._env:
            return "env"
        if key in self._config:
            return "config"
        if key in self.defaults:
            return "default"
        return "none"
