# dwgriffin-config

Lightweight Python library for merging configuration settings from
multiple sources into a single settings object.

ConfigManager merges settings from the following, lowest to highest priority.

  1. Defaults.  A provided dict or object with attributes
  2. Configuration file using INI format
  3. Environment variables
  4. CLI arguments

Settings defined in "defaults" determine which settings are recognized and merged.
ConfigManager has no settings of its own.  Settings read from other sources will
also be type cast to match the default source for bool, int, float, list, and tuple.

## Installation

`python3 -m pip install dwgriffin-config`

## Use

```
import os
from argparse import Namespace
from pathlib import Path
from tempfile import NamedTemporaryFile

from dwgriffin_config import ConfigManager

# Default config settings and values.
defaults = {
    "timeout": 300,
    "flags": False,
    "host": "example.com",
    "retries": 4,
}

# Config file
with NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as file:
    file.write(
        "[DEFAULT]\n"
        "timeout = 500\n"
        "host = config-example.com\n"
        "retries = 2\n"
    )
config_path = Path(file.name)

# Environment modules
os.environ["APP_TIMEOUT"] = "700"

# ClI args
args = Namespace(host="cli-example.com", timeout=None, flags=None)

config = ConfigManager(
    defaults=defaults,
    config_file = config_path,
    env_prefix = "APP_",
    cli_args = args,
)
for key in ("timeout", "flags", "hostname", "retries"):
    print(f"{key:10} = {config.get(key)!r:30} (from {config.source(key)})")

```

Produces:
```
timeout    = 700                            (from env)
flags      = False                          (from default)
host       = 'cli-example.com'              (from cli)
retries    = 2                              (from config)
```

## API

````
ConfigManager(
    defaults,
    config_file=None,
    ini_section=None,
    env_prefix=None,
    cli_args=None,
    required=None,
)
```

| Argument | Type | Description |
| ---------|------|-------------|
| `defaults` | `dict[str, Any]` | Defines known settings and their default values and types.
| `config_file` | `str | Path | None` | Path to optional INI configuration file.
| `ini_section` | `str | None` | Optional INI section to read from. If `None`, include all sections
| `env_prefix` | `str | None` | Prefix for Environment variables. e.g. `APP_` maps `timeout` to `APP_TIMEOUT`.
| `cli_args` | `argparse.Namespace | dict[str, Any] | None` | Parsed CLI arguments. 
| `required` | `list[str] | None` | Optional list of required keys. 

### Methods and access patterns
- Dot access — `config.key` returns the resolved value, or raises `AttributeError` if the key isn't known.
- `config.get(key)` — returns the resolved value, or `None` if unknown.
- `config.all()` — returns a dict copy of every resolved setting.
- `config.source(key)` — returns where a setting's value came from: `cli`, `env`, `config`, `default`, or `none`.

## License

GNU General Public License v3.0 or later
