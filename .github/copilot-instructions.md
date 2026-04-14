# pipen-cli-run Project Guidelines

## Overview

A CLI plugin for the [pipen](https://github.com/pwwang/pipen) pipeline framework. Adds a `run` subcommand that discovers and executes `Proc` and `ProcGroup` subclasses registered by third-party packages via Python entry points (`pipen_cli_run` group).

CLI flow: `pipen run <namespace> <ProcOrProcGroup> [+arg=val ...]`

## Architecture

All logic lives in `pipen_cli_run/entry.py` — a single `PipenCliRunPlugin(AsyncCLIPlugin)` class:

- **`__init__`**: scans installed distributions for `pipen_cli_run` entry points; stores raw `EntryPoint` objects (lazy, not yet loaded)
- **`_subparser_pre_parse`**: adds one sub-parser per registered namespace
- **`_subsubparser_pre_parse`**: loads the namespace module on demand, introspects attributes, registers eligible `Proc`/`ProcGroup` subclasses
- **`exec_command`**: instantiates the selected class and calls `pipeline.async_run()`

Entry point group constant: `ENTRY_POINT_GROUP = "pipen_cli_run"` in `entry.py`.

## Key Conventions

- **`Proc` eligibility**: only listed/runnable if `attrval.input` is truthy (inputs must be defined)
- **`ProcGroup` eligibility**: must be a subclass of `ProcGroup` or `ArgsProcGroup` but not those base classes themselves
- **Lazy loading check**: use `type(x).__name__ == "EntryPoint"` — deliberately not `isinstance` to avoid import cycles. Do not refactor this.
- **Argument prefix**: process/pipeline args use `prefix_chars="+"` (e.g., `+extra=2`) to avoid collision with pipen-level `--` args
- **Pipeline args**: collected as raw list (`pipeline_args`) and passed to `pipen_args.parser.set_cli_args(...)`, not parsed by top-level argparser
- **Code style**: Black, line length 88, Python 3.9–3.12

## Build and Test

```sh
# Install
poetry install

# Run tests (parallel, each in a forked subprocess)
pytest

# Lint
flake8
```

Tests require `@pytest.mark.forked` on every test — pipen/pipen-args use global state that would contaminate between tests without forking.

## Testing Conventions

- **`patch_init` fixture** (`tests/utils.py`): monkey-patches `PipenCliRunPlugin.__init__` to inject test namespaces without real installed entry points
- **`plugin_to_entrypoint(module)`**: creates a fake `EntryPoint`-like wrapper around a module
- **`with_argv(argv)`**: context manager that temporarily replaces `sys.argv`
- Test namespace modules: `example_procs.py`, `example_pipeline.py`, `example_pipeline_process.py`, `example_extra_args.py`
- Non-class attributes in namespace modules are silently skipped — test modules include `some_other_value = 123` to verify this behavior
