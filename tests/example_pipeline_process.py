from pipen import Proc
from pipen_cli_run import Pipeline, process

some_other_value = 123


class P1(Proc):
    input = "a"
    output = "outfile:file:out.txt"
    script = "echo {{in.a}} > {{out.outfile}}"


class P2(Proc):
    input = "infile:file"
    output = "outfile:file:out.txt"
    script = "cat {{in.infile}} > {{out.outfile}}; echo 123 >> {{out.outfile}}"


class example_pipeline(Pipeline):
    """This is a pipeline"""

    @process(start=True)
    def build_p1(self):
        return P1

    @process(end=True)
    def build_p2(self, p1):
        P2.requires = p1
        return P2

    def build(self) -> None:
        p1 = self.build_p1()
        self.build_p2(p1)


if __name__ == "__main__":
    example_pipeline().run(["1"])
