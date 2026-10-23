import asyncio
import subprocess
import threading
import os
import psutil

from .logger import PostLogger as Post
from ..models.shell_result_model import ShellResult

SYSTEM_PATH = (
    r"%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0"
)
_env_default = {}
for k, v in os.environ.items():
    _env_default[k] = v
_env_default["PATH"] = os.path.expandvars(SYSTEM_PATH)
if "CUDA_PATH" in _env_default:
    _env_default.pop("CUDA_PATH")


class _command_runner:
    def __init__(self, command, env):
        self.command = command
        self.env = env
        self.proc = None

    async def start(self):
        self.proc = await asyncio.create_subprocess_shell(
            cmd=self.command,
            env=self.env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

    async def stream(self):
        while True:
            if self.proc.stdout.at_eof():  # type: ignore
                break
            stdout = await self.proc.stdout.readline()  # type: ignore
            yield stdout.decode(encoding="utf-8")

    async def wait(self):
        if self.proc is None:
            return None
        await self.proc.communicate()
        return self.proc.returncode

    async def kill(self):
        if self.proc:
            self.proc.terminate()


class AsyncShell:
    def __init__(self):
        self.task_lock = asyncio.Lock()
        self.runner = None
        self.cmd = ""
        self.env = None
        self.with_content = False
        self.killed = False

    async def _run_cmd(self) -> ShellResult:
        self.killed = False
        async with self.task_lock:
            self.runner = _command_runner(self.cmd, env=self.env)
        retult_stdout = ""
        result_stderr = ""
        await self.runner.start()
        async for stdout in self.runner.stream():
            if stdout and len(stdout):
                stdout = stdout.replace("\r", "")
                if self.with_content:
                    retult_stdout += stdout
                else:
                    Post.info(stdout)
        exitcode = await self.runner.wait()
        async with self.task_lock:
            self.runner = None
        return ShellResult(exitcode=exitcode, stdout=retult_stdout, stderr=result_stderr, killed=self.killed)

    def exec(self, command: str, env: None | dict = None, with_content: bool = False, shell: bool = False):
        self.cmd = command
        nenv = _env_default.copy()
        if env:
            for k, v in env.items():
                nenv[k] = v
        self.env = nenv
        self.with_content = with_content
        return asyncio.run(self._run_cmd())

    async def kill(self):
        async with self.task_lock:
            self.killed = True
            if self.runner:
                await self.runner.kill()
            if self.runner:
                await self.runner.kill()


def split_cmd_line(cmd_line: str):
    args = []
    current = []
    in_quotes = False
    quote_char = None  # " または '

    i = 0
    while i < len(cmd_line):
        c = cmd_line[i]

        # クォート開始/終了処理
        if c in ('"', "'"):
            if not in_quotes:
                # クォート開始
                # ただし直前が = の場合は内部クォートとして残す
                if current and current[-1] == "=":
                    current.append(c)
                else:
                    in_quotes = True
                    quote_char = c
            else:
                # クォート終了
                if c == quote_char:
                    in_quotes = False
                    quote_char = None
                else:
                    # 異なる種類のクォートはそのまま
                    current.append(c)

        # クォート外のスペース → 引数区切り
        elif c.isspace() and not in_quotes:
            if current:
                args.append("".join(current))
                current = []

        else:
            current.append(c)

        i += 1

    if current:
        args.append("".join(current))

    return args


class Shell:
    def __init__(self):
        pass

    def exec(
        self,
        cmd_line: str,
        cwd: str | None = None,
        env: dict | None = None,
        with_content: bool = False,
        shell: bool = False,
    ):
        if not env:
            env = os.environ.copy()

        result = None
        if shell:
            try:
                result = subprocess.run(
                    cmd_line, capture_output=True, text=True, cwd=cwd, env=env, encoding="cp65001", shell=True
                )
                return ShellResult(exitcode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            except Exception as e:
                return ShellResult(exitcode=255, stderr=str(e))
        else:
            cmd_args = split_cmd_line(cmd_line)
            try:
                result = subprocess.run(cmd_args, capture_output=True, text=True, cwd=cwd, env=env, encoding="cp65001")
                return ShellResult(exitcode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            except Exception as e:
                return ShellResult(exitcode=255, stderr=str(e))


class PipedShell:
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self._killed = False

    def exec(
        self,
        cmd_line: str,
        cwd: str | None = None,
        env: dict | None = None,
        with_content: bool = False,
        shell: bool = False,
    ) -> ShellResult:
        self._killed = False
        if not env:
            env = os.environ.copy()

        stdout_chunks = []
        stderr_chunks = []

        def stream_reader(stream, out_type: str, chunks_list: list | None):
            try:
                while True:
                    if self._killed:
                        break

                    line = stream.readline()

                    if line == "":
                        break
                    if chunks_list is not None:
                        chunks_list.append(line)

                    mesg = line.rstrip("\r\n")
                    if mesg:
                        Post.info(mesg)

            except Exception as e:
                Post.error(f"Stream reader error ({out_type}): {e}")

            finally:
                try:
                    stream.close()
                    pass
                except Exception:
                    pass

        def run_command(args, cwd: str | None, env: dict, shell: bool = True, with_content: bool = False):
            self._killed = False
            self.process = subprocess.Popen(
                args=args,
                env=env,
                shell=shell,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            thr_out = threading.Thread(
                target=stream_reader,
                args=(
                    self.process.stdout,
                    "stdout",
                    stdout_chunks if with_content else None,
                ),
                daemon=True,
            )
            thr_err = threading.Thread(
                target=stream_reader,
                args=(
                    self.process.stderr,
                    "stderr",
                    stderr_chunks if with_content else None,
                ),
                daemon=True,
            )

            thr_out.start()
            thr_err.start()

            # 1. まず親プロセス（cmd.exeなど）の終了を待つ
            exit_code = self.process.wait()

            # スレッドがEOFに達するのを安全に待つ
            thr_out.join()
            thr_err.join()
            stdout = "".join(stdout_chunks) if with_content else ""
            stderr = "".join(stderr_chunks) if with_content else ""

            # killフラグが立っていた場合のWindows強制終了コード補正
            if self._killed and (exit_code == 0 or exit_code is None):
                exit_code = 1

            return ShellResult(
                exitcode=exit_code,
                stdout=stdout,
                stderr=stderr,
                killed=self._killed,
            )

        try:
            if shell:
                return run_command(args=cmd_line, cwd=cwd, env=env, shell=True, with_content=with_content)
            else:
                cmd_args = split_cmd_line(cmd_line)
                return run_command(args=cmd_args, cwd=cwd, env=env, shell=False, with_content=with_content)
        except Exception as e:
            return ShellResult(exitcode=255, stderr=str(e))

    def kill(self):
        if self.process and self.process.poll() is None:
            self._killed = True
            self.process.kill()
