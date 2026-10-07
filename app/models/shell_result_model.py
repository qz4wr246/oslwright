from dataclasses import dataclass


@dataclass
class ShellResult:
    exitcode: int = 255
    stdout: str = ""
    stderr: str = ""
    killed: bool = False
