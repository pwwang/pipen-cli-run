"""Default settings and utilities"""

import re
from typing import TYPE_CHECKING, Any, List, Mapping, Type
from pandas import DataFrame

from pardoc import google_parser
from pardoc.parsed import ParsedItem

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Pipen, Proc
    from pyparam import Params

ENTRY_POINT_GROUP = "pipen_cli_run"


def doc_to_summary(docstr: str) -> str:
    """Get the first line of docstring as summary"""
    out = []
    for i, line in enumerate(docstr.splitlines()):
        line = line.strip()
        if not line and i > 0:
            break
        out.append(line)
    return " ".join(out)


def annotate_process(proc: Type["Proc"]) -> Mapping[str, Any]:
    """Annotate the process with docstrings"""
    parsed = google_parser.parse(proc.__doc__ or "")
    keys = ("Input", "Envs")

    out = {}
    for key in keys:
        out[key] = {}
        if key not in parsed:
            continue
        for item in parsed[key].section:
            if not isinstance(item, ParsedItem):  # pragma: no cover
                continue
            out[key][item.name] = item.desc

    return out


def skip_hooked_args(args: List[str]) -> List[str]:
    """This allows the modules to have some extra arguments starting with `+`
    """
    out = []
    skipping = False
    for arg in args:
        if skipping:
            skipping = False
            continue
        if re.match(r"^\+[-\w\.]+$", arg):
            skipping = True
            continue
        if re.match(r"^\+[-\w\.]+=.+$", arg):
            skipping = False
            continue
        out.append(arg)

    return out


def params_from_pipeline(
    namespace: str,
    pname: str,
    pipeline: "Pipen",
    full_opts: bool,
    single: bool,
) -> "Params":
    """Get params from the pipeline"""
    from pipen_args import Args

    out = Args(
        prog=f"pipen run {namespace} {pname}",
        pipen_opt_group="PIPELINE OPTIONS",
        hide_args=None if full_opts else [
            "scheduler-opts",
            "plugin-opts",
            "template-opts",
            "dirsig",
            "cache",
            "forks",
            "error-strategy",
            "num-retries",
            "loglevel",
            "plugins",
            "submission-batch",
        ],
    )

    out.add_param(
        "full-opts",
        desc="Show full options.",
        default=False,
    )

    pipeline._build_proc_relationships()
    if single:
        out.desc = [doc_to_summary(pipeline.procs[0].__doc__ or "")]
    for proc in pipeline.procs:
        anno = annotate_process(proc)
        if not single:
            out.add_param(
                proc.name,
                desc=f"Options for process: {proc.name}",
                argname_shorten=False,
                show=False,
                type="ns",
            )

        if proc in pipeline.starts:
            out.add_param(
                "in" if single else f"{proc.name}.in",
                desc="Input data for the process.",
                argname_shorten=False,
                show=False,
                type="ns",
            )

            input_keys = proc.input or []
            if isinstance(input_keys, str):
                input_keys = [
                    ikey.strip()
                    for ikey in input_keys.split(",")
                ]

            for input_key_type in input_keys:
                if ":" not in input_key_type:
                    input_key = input_key_type.strip()
                    # out.type[input_key_type] = ProcInputType.VAR
                else:
                    # input_key, input_type = input_key_type.split(":", 1)
                    input_key, _ = input_key_type.split(":", 1)
                    input_key = input_key.strip()
                    # input_type = input_type.strip()

                out.add_param(
                    f"in.{input_key}"
                    if single
                    else f"{proc.name}.in.{input_key}",
                    desc=anno["Input"].get(input_key, "Undescribed."),
                    argname_shorten=False,
                    required=True,
                    type="list",
                )

        out.add_param(
            "envs" if single else f"{proc.name}.envs",
            desc="Envs for the process.",
            argname_shorten=False,
            show=False,
            type="ns",
        )
        for key, val in (proc.envs or {}).items():
            out.add_param(
                f"envs.{key}" if single else f"{proc.name}.envs.{key}",
                default=val,
                desc=anno["Envs"].get(key, "Undescribed."),
                argname_shorten=False,
            )

        if not single:
            out.add_param(
                f"{proc.name}.cache",
                desc=(
                    "Whether use cache. Default: <from config>"
                ),
                show=full_opts,
                type="bool",
            )
            out.add_param(
                f"{proc.name}.dirsig",
                desc=(
                    "Whether calcuate signature for directories. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="bool",
            )
            out.add_param(
                f"{proc.name}.export",
                desc=(
                    "Whether export output. Default: <from config>"
                ),
                show=full_opts,
                type="bool",
            )
            out.add_param(
                f"{proc.name}.error-strategy",
                desc=(
                    "How to deal with the errors. One of {choices}. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="choice",
                choices=["retry", "halt", "ignore"]
            )
            out.add_param(
                f"{proc.name}.num-retries",
                desc=(
                    "How many times to retry to jobs once error occurs. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="int",
            )
            out.add_param(
                f"{proc.name}.forks",
                desc=(
                    "How many jobs to run simultaneously? "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="int",
            )
            out.add_param(
                f"{proc.name}.submission-batch",
                desc=(
                    "How many jobs to be submitted simultaneously. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="int",
            )
            out.add_param(
                f"{proc.name}.plugin-opts",
                desc=(
                    "Options for process-level plugins. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="json",
            )
            out.add_param(
                f"{proc.name}.scheduler-opts",
                desc=(
                    "The options for the scheduler. "
                    "Default: <from config>"
                ),
                show=full_opts,
                type="json",
            )

    return out


def set_proc_data(proc: Type["Proc"], args: Mapping[str, Any]) -> None:
    """Set the data for the proc"""
    # input data
    if "in" in args:
        proc.input_data = DataFrame(args["in"])

    if "envs" in args and proc.envs is not None and args.envs is not None:
        proc.envs.update(args.envs)

    proc.cache = args["cache"]
    proc.dirsig = args["dirsig"]
    proc.error_strategy = args["error_strategy"]
    proc.num_retries = args["num_retries"]
    proc.forks = args["forks"]
    proc.submission_batch = args["submission_batch"]

    if proc.plugin_opts is not None and args["plugin_opts"] is not None:
        proc.plugin_opts.update(args["plugin_opts"])

    if proc.scheduler_opts is not None and args["scheduler_opts"] is not None:
        proc.scheduler_opts.update(args["scheduler_opts"])

    if "export" in args:
        proc.export = args["export"]
