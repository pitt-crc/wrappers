# CRC Wrapper Applications

Command-line applications for wrapping common HPC tasks on Slurm-based clusters.

The wrapper applications provide a simplified interface to routine Slurm
operations, lowering the barrier to entry for users who are new to HPC systems
and not yet familiar with Slurm's native tooling.

## Installation

The wrapper applications can be installed with any standard Python package manager.
Using the [pipx](https://pypa.github.io/pipx/) manager is recomended on production systems:

```bash
git clone https://github.com/pitt-crc/wrappers
pipx install ./wrappers
```

## Developer Notes

### Configuring a Poetry Environment

This project is developed and packaged using [Poetry](https://python-poetry.org/).
To clone the repository and install the project into a managed virtual environment:

```bash
git clone https://github.com/pitt-crc/wrappers
cd wrappers
poetry install
```

Optional development dependencies are organized into named groups, and can be
installed using the `--with` flag:

```bash
poetry install --with docs,tests
```

Available groups are listed in the table below.

| Dependency Group | Description                                            |
|------------------|--------------------------------------------------------|
| `docs`           | Dependencies for building the documentation.           |
| `tests`          | Dependencies for running the test suite with coverage. |

### Adding a New Application

Applications are built on the standard library `argparse` package. The
`BaseParser` class extends `argparse` to ensure a consistent interface across
all applications.

To add an application, subclass `BaseParser` and define:

1. The application description, as the class docstring
2. The command-line arguments and help text, in the `__init__` method
3. The application logic, in the `app_logic` method

For example:

```python
from argparse import Namespace

from apps._base_parser import BaseParser


class ExampleApplication(BaseParser):
    """This docstring becomes the application description in the CLI help text."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super().__init__()
        self.add_argument('-f', '--foo', help="This is help text for foo")

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        print(args.foo)
`````

To ensure the new application is included during installation,
register the application as a console script in the `[tool.poetry.scripts]`
section of the `pyproject.toml` file. The following example exposes the 
class in `apps/crc_example_module.py` as an executable named `executable-name`:

```toml
[tool.poetry.scripts]
executable-name = "apps.crc_example_module:ExampleApplication.execute"
```
