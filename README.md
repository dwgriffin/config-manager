# dwgriffin-config

dwgriffin's config library.

## Installation

`python3 -m pip install dwgriffin-config`

## Classes

### `ConfigManager`

Takes a dictionary of default settings. Merges configuration settings from defaults,
config file, environment variables, and CLI arguments.

#### Usage

```
import argparse
import os
from dwgriffin_config import ConfigManager


parser = argparse.ArgumentParser(description="An example CLI tool")
parser.add_argument("--timeout", type=int, default=None)
parser.add_argument("--flags", type=bool, default=None)
parser.add_argument("--hostname", type=str, default=None)
args = parser.parse_args()

defaults = {
    "timeout": 300,
    "flags": False,
    "hostname": "example.com",
}
os.environ["APP_TIMEOUT"] = "600"

config = ConfigManager(
    defaults = defaults,
    config_file = "./config.ini",  # sets "hostname = example2.com"
    env_prefix = "APP_",
    cli_args = args,
)

print(config.all())
```
produces:
```
{'timeout': 600, 'flags': False, 'hostname': 'example2.com'}
```

## License

GNU General Public License v3.0 or later
