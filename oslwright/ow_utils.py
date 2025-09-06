import asyncio
import locale
import logging
import os
import re
from typing import Any

import pyjson5

SYSTEM_PATH = (
    r"%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0"
)
env_default = {}
for k, v in os.environ.items():
    env_default[k] = v
env_default["PATH"] = os.path.expandvars(SYSTEM_PATH)
if "CUDA_PATH" in env_default:
    env_default.pop("CUDA_PATH")


class DictDotNotation(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    __getattr__ = dict.get


def LoadJson5(filepath: str) -> DictDotNotation:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
        json_obj = pyjson5.loads(text)
        return json_obj


def SaveJson5(filepath: str, data: dict) -> None:
    with open(filepath, "w") as f:
        f.write(pyjson5.dumps(data))


def MergeDict(lft: dict, rgt: dict) -> dict:
    if not lft:
        return rgt
    if not rgt:
        return lft

    dist = lft.copy()
    return _mergeDict(dist, rgt)


def _mergeDict(lft: dict, rgt: dict) -> dict:
    # for key in rgt:
    #     if key in lft:
    #         if isinstance(lft[key], dict) and isinstance(rgt[key], dict):
    #             _mergeDict(lft[key], rgt[key])
    #         else:
    #             lft[key] = rgt[key]
    #     else:
    #         lft[key] = rgt[key]
    # return lft

    rgt_dic = {}
    for key in rgt.keys():
        if "!" in key:
            mkey, cmd = key.split("!", 1)
            rgt_dic[mkey] = (cmd, rgt[key])
        else:
            rgt_dic[key] = ("", rgt[key])

    for key in rgt_dic.keys():
        if key in lft:
            cmd = rgt_dic[key][0]
            val = rgt_dic[key][1]
            if isinstance(lft[key], dict) and isinstance(val, dict):
                if cmd == "a":  # append
                    _mergeDict(lft[key], val)
                elif cmd == "d":  # delete
                    lft.pop(key, None)
                elif cmd == "r":  # replace
                    lft[key] = val
                else:  # append
                    _mergeDict(lft[key], val)
            elif isinstance(lft[key], list) and isinstance(val, list):
                if cmd == "a":  # append
                    lft[key].extend(val)
                elif cmd == "d":  # delete
                    lft.pop(key, None)
                elif cmd == "r":  # replace
                    lft[key] = val
                else:  # replace
                    lft[key] = val
            else:
                lft[key] = val
        else:
            cmd = rgt_dic[key][0]
            val = rgt_dic[key][1]
            if cmd == "d":  # delete
                pass
            else:
                lft[key] = val
    return lft


def CompareDict(lft: dict, rgt: dict) -> bool:
    if lft.keys() != rgt.keys():
        return False
    for key in rgt:
        if key in lft:
            if isinstance(lft[key], dict) and isinstance(rgt[key], dict):
                if not CompareDict(lft[key], rgt[key]):
                    return False
            else:
                if lft[key] != rgt[key]:
                    return False
        else:
            return False
    return True


class _Post:
    def __init__(self):
        self.status_handler = None
        self.info_handler = None
        self.debug_handler = None
        self.error_handler = None

    def Status(self, message: str) -> None:
        if self.status_handler:
            self.status_handler(message)
        else:
            logging.info(message)

    def Info(self, message: str) -> None:
        if self.info_handler:
            self.info_handler(message)
        else:
            logging.info(message)

    def Debug(self, message: str) -> None:
        if self.debug_handler:
            self.debug_handler(message)
        else:
            logging.debug(message)

    def Error(self, message: str) -> None:
        if self.error_handler:
            self.error_handler(message)
        else:
            logging.error(message)

    def SetHandler(
        self,
        info_handler: Any | None = None,
        debug_handler: Any | None = None,
        error_handler: Any | None = None,
        status_handler: Any | None = None,
    ):
        self.info_handler = info_handler
        self.debug_handler = debug_handler
        self.error_handler = error_handler
        self.status_handler = status_handler


Post = _Post()


class _CommandRunner:
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
            if self.proc.stdout.at_eof():
                break
            stdout = await self.proc.stdout.readline()
            yield stdout.decode(encoding="utf-8")

    async def wait(self):
        if self.proc is None:
            return None
        await self.proc.communicate()
        return self.proc.returncode

    async def kill(self):
        if self.proc:
            self.proc.terminate()


class Shell:
    def __init__(self):
        self.task_lock = asyncio.Lock()
        self.runner = None
        self.cmd = ""
        self.env = None
        self.with_content = False
        self.killed = False

    async def _run_cmd(self) -> DictDotNotation:
        self.killed = False
        async with self.task_lock:
            self.runner = _CommandRunner(self.cmd, env=self.env)
        retult_stdout = ""
        result_stderr = ""
        await self.runner.start()
        async for stdout in self.runner.stream():
            if stdout and len(stdout):
                stdout = stdout.replace("\r", "")
                if self.with_content:
                    retult_stdout += stdout
                else:
                    Post.Debug(stdout)
        exitcode = await self.runner.wait()
        async with self.task_lock:
            self.runner = None
        return DictDotNotation(
            {"exitcode": exitcode, "stdout": retult_stdout, "stderr": result_stderr, "killed": self.killed}
        )

    def exec(self, command: str, env: None | dict = None, with_content: bool = False) -> DictDotNotation:
        self.cmd = command
        nenv = env_default.copy()
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
