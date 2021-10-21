"""Provides PipenCliRun"""
from types import ModuleType
from typing import Any, Mapping, List

from diot import Diot
from pipen import Proc, Pipen
from pipen.cli import CLIPlugin
from pipen.utils import importlib_metadata
from pyparam import Params
from rich import print

from .utils import (
    ENTRY_POINT_GROUP,
    doc_to_summary,
    params_from_pipeline,
    set_proc_data,
    skip_hooked_args,
)

try:
    from functools import cached_property
except ImportError:  # pragma: no cover
    from cached_property import cached_property


class PipenCliRunPlugin(CLIPlugin):
    """Run a process or a pipeline"""

    from .version import __version__

    name = "run"

    def __init__(self) -> None:
        """Read entry points"""
        self.entry_points = {}
        for dist in importlib_metadata.distributions():
            for epoint in dist.entry_points:
                if epoint.group != ENTRY_POINT_GROUP:
                    continue
                # don't load them
                self.entry_points[epoint.name] = epoint

    def _print_help(self) -> None:
        """Print the root help page"""
        for key in sorted(self.entry_points):
            desc = self.entry_points[key].load().__doc__
            self.params.add_command(
                key,
                desc.strip() if desc else "Undescribed.",
                group="NAMESPACES",
            )
        self.params.print_help()

    def _print_ns_help(self, namespace: str, ns_mod: ModuleType) -> None:
        """Print help for the namespace"""
        command = self.params.add_command(
            namespace,
            ns_mod.__doc__.strip() if ns_mod.__doc__ else "Undescribed.",
            force=True,
        )
        command.add_param(
            command.help_keys,
            desc="Print help for this namespace.",
        )
        for attrname in dir(ns_mod):
            attrval = getattr(ns_mod, attrname)
            if isinstance(attrval, Pipen):
                command.add_command(
                    attrname,
                    desc=attrval.desc,
                    group="PIPELINES",
                )
            elif not isinstance(attrval, type):
                continue
            elif issubclass(attrval, Proc) and attrval.input:
                command.add_command(
                    attrval.name,
                    desc=doc_to_summary(attrval.__doc__ or "Undescribed."),
                    group="PROCESSES",
                )
        command.print_help()

    @cached_property
    def params(self) -> Params:
        """Add run command"""
        pms = Params(
            desc=self.__class__.__doc__,
        )
        pms.add_param(
            pms.help_keys,
            desc="Print help for this command.",
        )
        return pms

    def parse_args(self, args: List[str]) -> Mapping[str, Any]:
        """Parse the arguments"""
        args = skip_hooked_args(args)
        if len(args) == 0:
            self._print_help()

        namespace = args[0]
        help_keys = [
            f"-{key}" if len(key) == 1 else f"--{key}"
            for key in self.params.help_keys
        ]
        if namespace in help_keys:
            self._print_help()

        # add commands and parse
        if namespace not in self.entry_points:
            print(
                "[red][b]ERROR: [/b][/red]No such namespace: "
                f"[green]{namespace}[/green]"
            )
            self._print_help()

        module = self.entry_points[namespace].load()
        if len(args) == 1:
            self._print_ns_help(namespace, module)

        pname = args[1]
        # Strictly, help_keys should be from command.help_keys
        if pname in help_keys:
            self._print_ns_help(namespace, module)

        pipeline = getattr(module, pname)
        full_opts = "--full-opts" in args[2:]
        if full_opts:
            args = args + help_keys[:1]

        single = False
        if not isinstance(pipeline, Pipen):
            pipeline = Pipen(
                name=f"{pipeline.name}-pipeline",
                desc="A pipeline wrapper to run a single process",
            ).set_starts(pipeline)
            single = True

        pms = params_from_pipeline(
            namespace,
            pname,
            pipeline,
            full_opts=full_opts,
            single=single,
        )
        parsed = Diot.from_namespace(pms.parse(args[2:]))
        parsed["__single__"] = single
        parsed["__pipeline__"] = pipeline

        return parsed

    def exec_command(self, args: Mapping[str, Any]) -> None:
        """Execute the command"""
        pipeline = args["__pipeline__"]
        single = args["__single__"]
        if single:
            set_proc_data(pipeline.procs[0], args)
        else:
            for proc in pipeline.procs:
                if proc.name in args:
                    set_proc_data(proc, args[proc.name])

        pipeline.run()
