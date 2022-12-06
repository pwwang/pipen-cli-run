from pipen import Proc
from pipen_cli_run import Pipeline

some_other_value = 123


class P1(Proc):
    input = "a"
    output = "outfile:file:out.txt"
    script = "echo {{in.a}} > {{out.outfile}}"


class P2(Proc):
    requires = P1
    input = "infile:file"
    output = "outfile:file:out.txt"
    script = "cat {{in.infile}} > {{out.outfile}}; echo 123 >> {{out.outfile}}"


class example_pipeline(Pipeline):
    """This is a pipeline"""
    def build(self) -> None:
        self.starts = [P1]
        self.ends = [P2]
        self.procs.P1 = P1
        self.procs.P2 = P2


class example_pipeline2(Pipeline):
    # not implementing build
    ...


class example_pipeline3(Pipeline):

    def build(self) -> None:
        # Not having starts
        self.ends = [P2]


if __name__ == "__main__":
    example_pipeline().run(["1"])
