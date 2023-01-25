from pipen import Proc
from pipen_cli_run import Pipeline

some_other_value = 123


class example_pipeline(Pipeline):
    """This is a pipeline"""

    def build_p1(self):

        class P1(Proc):
            input = "a"
            output = "outfile:file:out.txt"
            script = "echo {{in.a}} > {{out.outfile}}"

        self.procs.P1 = P1
        self.starts.append(P1)
        return P1

    def build_p2(self, p1):

        class P2(Proc):
            requires = p1
            input = "infile:file"
            output = "outfile:file:out.txt"
            script = (
                "cat {{in.infile}} > {{out.outfile}}; "
                "echo 123 >> {{out.outfile}}"
            )

        self.procs.P2 = P2
        self.ends.append(P2)
        return P2

    def build(self) -> None:
        p1 = self.build_p1()
        self.build_p2(p1)


class example_pipeline2(Pipeline):
    # not implementing build
    ...


class example_pipeline3(example_pipeline):

    def build_p1(self):

        class P1(Proc):
            input = "a"
            output = "outfile:file:out.txt"
            script = "echo {{in.a}} > {{out.outfile}}"

        self.procs.P1 = P1
        return P1


if __name__ == "__main__":
    example_pipeline().run(["1"])
