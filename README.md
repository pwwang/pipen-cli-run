<div align="center">
    <img src="./logo.png" width="220px" alt="pipen-cli-run logo" />
    <p style="font-weight:bold;">A pipen cli plugin to run a process or a pipeline</p>
</div>

## Install

```shell
pip install -U pipen-cli-run
```

## Usage

### Register a namespace

`pyproject.toml`
```toml
[tool.poetry.plugins.pipen_cli_run]
ns = "yourpackage.ns"
```

`ns` should be a module where you define you processes/pipelines

Then run the process or pipeline:

```shell
pipen run ns <process_or_pipeline_name> [args...]
```
