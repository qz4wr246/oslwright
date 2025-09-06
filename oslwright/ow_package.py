import asyncio
import datetime
import glob
import os
import re
import sys
import traceback
from enum import Enum, auto
from typing import Any

import regex
from natsort import natsorted

from oslwright.ow_utils import SYSTEM_PATH, LoadJson5, MergeDict, Post, SaveJson5, Shell


def Version(text):
    version_split = re.findall(r"\d+|[a-zA-Z]+", text)

    prefix = ["v", "ver", "version", "vol"]
    if version_split[0].lower() in prefix:
        version_split = version_split[1:]

    prerelease_str = ["a", "alpha", "b", "beta", "rc", "pre", "preview", "canary"]

    output = []
    for item in version_split:
        if item.isdecimal():
            output.append((int(item), ""))
        elif item.lower() in prerelease_str:
            output.append((-1, item))
        else:
            output.append((0, item))
    output.append((0, ""))

    return tuple(output)


class Package:
    """ """

    STAGES_ORDER = ["download", "patch", "configure", "build", "test", "install", "post-install"]
    RESERVED_KEYS = [
        "settings",
        "versions",
        "dependencies",
        "environments",
        "stages",
        "scripts",
        "when",
        "script",
        "chdir",
        "ignore_errors",
        "failed",
        "change_stage",
    ]

    CODE_PATTERN = r"(\{\{([^{}]*|\{[^{}]*\}|\{([^{}]*|\{[^{}]*\})+\}|\{([^{}]*(\{([^{}]*|\{[^{}]*\})+\})?)+\})*\}\})"
    VARIAVLE_PATTERN = r"^\$(\w+)|^\$\{\s*(\w+)\s*\}|[^$]\$(\w+)|[^$]\$\{\s*(\w+)\s*\}|\$\$(\w+)|\$\$\{\s*(\w+)\s*\}"

    class Reaseon(Enum):
        COMPLETED = auto()
        USER_INTERRUPTED = auto()
        ERROR = auto()

    def __init__(self, base: str, platform: Any | None = None):
        Post.Info(f"Package: {base}")
        self.package_json = {}
        self.settings = {}
        self.setting_modified = False
        self.stages_finished: list[dict] = []
        self.running = False
        self.process_seconds = 0
        self.platform = platform
        self.shell = Shell()
        self.env = {}
        self.name = ""

        if os.path.isfile(base):
            packge_file = base
        elif os.sep not in base:
            packge_file = os.path.join(platform.package_rootdir, base, "package.jsonc")
        else:
            raise RuntimeError("Bad package path")
        self.packge_file = packge_file
        self._loadPkgFile(packge_file)
        self._initVersions()
        self._setDefaultSettings()
        self._loadSettings()
        self.process_time = 0
        if "process_time" in self.package_json:
            self.process_time = int(self.package_json["process_time"])

    def Reload(self):
        self._loadPkgFile(self.packge_file)
        self._initVersions()
        self._setDefaultSettings()
        self._loadSettings()
        self._saveSetting(force=False)

    def _loadPkgFile(self, fname: str) -> None:
        try:
            self.package_json = LoadJson5(fname)
            self.package_dir = os.path.dirname(fname)
        except Exception as e:
            Post.Error(f"{e}")
            raise e

    def _initVersions(self) -> None:
        vers = [x for x in self.package_json["versions"].keys() if x != "default"]
        if vers:
            self.versions = natsorted(vers)
        else:
            self.versions = ["master"]
        self.latest_version = self.versions[-1]

    def _loadSettings(self) -> None:
        setting_rootdir = self.package_dir
        if self.platform:
            setting_rootdir = self.platform.setting_rootdir
        fname = os.path.join(setting_rootdir, f"{self.name}_settings.jsonc")
        if os.path.isfile(fname):
            data = LoadJson5(fname)
            # update settings
            for k, v in self.settings.items():
                if k in data["settings"]:
                    data[k] = v
            self.settings = data["settings"]
            self.stages_finished = data["stages"]

        self.setting_modified = False
        return

    def _saveSetting(self, settings: dict | None = None, force: bool = False) -> None:
        if not settings:
            settings = self.settings

        if force or self.setting_modified:
            setting_rootdir = self.package_dir
            if self.platform:
                setting_rootdir = self.platform.setting_rootdir
            os.makedirs(setting_rootdir, exist_ok=True)
            fname = os.path.join(setting_rootdir, f"{self.name}_settings.jsonc")
            if settings:
                data = {"settings": settings, "stages": self.stages_finished}
                SaveJson5(fname, data)
                self.settings = settings
        self.setting_modified = False

    def _setDefaultSettings(self) -> None:
        session = self._createSession()
        settings = self._getDefaultSetting(session)
        self.name = session["name"]
        self.display = session["display"]
        self.description = session["description"]
        self.license = session["license"]
        self.site = session["site"]
        self.settings = settings

    def _getDefaultSetting(self, session: dict | None = None) -> dict:
        if not session:
            session = self._createSession()
        params = self.GetSettingParam(session)
        settings = {x["name"]: self._evalValue(session, x["default"]) for x in params}
        settings["name"] = session["name"]
        return settings

    def _differSettings(self, settings: dict) -> str | None:
        if self.settings == settings:
            return None
        if self.settings["version"] != settings["version"]:
            return "download"
        else:
            return "configure"

    def GetSettingParam(self, session: dict | None = None) -> list[dict] | None:
        if "settings" in self.package_json:
            if not session:
                session = self._createSession()
            params: list[dict] = self.package_json["settings"]
            for param in params:
                for k, v in param.items():
                    param[k] = self._evalValue(session, v)
            return params
        return None

    def GetSettings(self) -> dict:
        return self.settings.copy()

    def SetSettings(self, settings: dict):
        ret = self._differSettings(settings)
        if not ret:
            return
        self.settings = settings.copy()
        self.setting_modified = True
        self._changeStage(ret)

    def GetInfoText(self) -> str:
        session = self._createSession()
        if "info" in session:
            fname = session["info"]
            if os.path.isabs(fname):
                with open(fname, encoding="utf-8") as f:
                    md = f.read()
                    return md
            else:
                with open(os.path.join(session["package_dir"], fname), encoding="utf-8") as f:
                    md = f.read()
                    return md
        return ""

    def GetDistinationDirs(self, request: dict | None = None) -> dict:
        settings = self.GetSettingsFromRequest(request)
        stage_root = self._getStageRoot(settings["version"])
        session = self._createSession(root=stage_root, settings=settings)

        result = {}
        if "dist_dir_debug" in session:
            result["debug"] = session["dist_dir_debug"]
        if "dist_dir_release" in session:
            result["release"] = session["dist_dir_release"]

        if "dist_dir_debug" not in session and "dist_dir_release" not in session:
            if "dist_dir" in session:
                result["debug"] = session["dist_dir"]
                result["release"] = session["dist_dir"]
        return result

    def GetSettingsFromRequest(self, request: dict | None = None) -> dict:
        if not request:
            return self.settings.copy()
        req_ver = None
        if request and "version" in request:
            req_ver = request["version"]
        version = self._findRequestVersion(req_ver)
        if not version:
            raise RuntimeError(f"Miss match version. by {request['name']}-{request['version']}")
        params = self.GetSettingParam()
        nsetting = self.settings.copy()
        for itr in params:
            req = next((r for r in request.items() if r[0] == itr["name"]), None)
            if req:
                val = req[1]
                if itr["type"] == "chose":
                    if val in itr["item"]:
                        nsetting[req[0]] = val
                # elif itr["name"] == "enable":
                #     continue
                else:
                    nsetting[req[0]] = val
        nsetting["version"] = version
        return nsetting

    def GetDependencies(self, request: dict | None = None, session: dict | None = None):
        req_ver = None
        if request and "version" in request:
            req_ver = request["version"]
        version = self._findRequestVersion(req_ver)
        stage_root = self._getStageRoot(version)
        if "dependencies" not in stage_root:
            return []
        settings = None
        if not request:
            settings = self.GetSettings()
        else:
            settings = self.GetSettingsFromRequest(request=request)
        settings["version"] = version
        if not session:
            session = self._createSession(root=stage_root, settings=settings)
        dependencies = stage_root["dependencies"]
        depends = []
        for name, dep_request in dependencies.items():
            dep_request = self._evalValue(session, dep_request)
            pkg = self.platform.FindPacakge(name)
            dep_settings = pkg.GetSettingsFromRequest(request=dep_request)
            if dep_request:
                if "enable" not in dep_request or dep_request["enable"]:
                    if "msvc_toolset_version" in dep_settings and "msvc_toolset_version" in settings:
                        dep_settings["msvc_toolset_version"] = settings["msvc_toolset_version"]
                    if "msvc_runtime_library" in dep_settings and "msvc_runtime_library" in settings:
                        dep_settings["msvc_runtime_library"] = settings["msvc_runtime_library"]
                    if "build_arch" in dep_settings and "build_arch" in settings:
                        dep_settings["build_arch"] = settings["build_arch"]
                    if "cuda_enable" in dep_settings and "cuda_enable" in settings:
                        dep_settings["cuda_enable"] = settings["cuda_enable"]
                    if "cuda_versions" in dep_settings and "cuda_versions" in settings:
                        dep_settings["cuda_versions"] = settings["cuda_versions"]

                    depends.append(dep_settings)
            else:
                depends.append(dep_settings)
        return depends

    def _getDepedentPackagePaths(self, settings: dict) -> dict:
        result = {}
        distdir_debug = []
        distdir_release = []
        requests = self.GetDependencies(request=settings)
        for req in requests:
            deppkg = self.platform.FindPacakge(req["name"])
            dirs = deppkg.GetDistinationDirs(req)
            if "debug" in dirs and dirs["debug"]:
                distdir_debug.append(dirs["debug"])
            if "release" in dirs and dirs["release"]:
                distdir_release.append(dirs["release"])
        if distdir_debug:
            result["debug"] = ";".join(distdir_debug)
        if distdir_release:
            result["release"] = ";".join(distdir_release)
        return result

    def _findRequestVersion(self, req_ver: str | None = None) -> str | None:
        reg = r"([><=]=?)?([^\s,;]+)(\s*[,;]+\s*([><]=?)([\w.-]+))?"

        if not len(self.versions):
            return None

        if not req_ver:
            return self.versions[-1]

        m = regex.match(reg, req_ver)
        ope1 = m.group(1)
        ver1 = m.group(2)
        ope2 = m.group(4)
        ver2 = m.group(5)

        if not ver1:
            # "Bad dependenct version in package.jsonc"
            return None

        versions = self.versions
        if not ope1:
            if ver1 in set(versions):
                return ver1
            return None

        if ope1 == "=" or ope1 == "==":
            versions = [v for v in versions if Version(v) == Version(ver1)]
        elif ope1 == "<=":
            versions = [v for v in versions if Version(v) <= Version(ver1)]
        elif ope1 == ">=":
            versions = [v for v in versions if Version(v) >= Version(ver1)]
        elif ope1 == "<":
            versions = [v for v in versions if Version(v) < Version(ver1)]
        elif ope1 == ">":
            versions = [v for v in versions if Version(v) > Version(ver1)]
        elif ope1 == "!=":
            versions = [v for v in versions if Version(v) != Version(ver1)]

        if not ope2 and not ver2:
            return versions[-1] if len(versions) else None

        if not ope2 and ver2:
            if ver2 in set(versions):
                return ver2
            return None

        if ope2 == "=" or ope2 == "==":
            versions = [v for v in versions if Version(v) == Version(ver2)]
        elif ope2 == "<=":
            versions = [v for v in versions if Version(v) <= Version(ver2)]
        elif ope2 == ">=":
            versions = [v for v in versions if Version(v) >= Version(ver2)]
        elif ope2 == "<":
            versions = [v for v in versions if Version(v) < Version(ver2)]
        elif ope2 == ">":
            versions = [v for v in versions if Version(v) > Version(ver2)]
        elif ope2 == "!=":
            versions = [v for v in versions if Version(v) != Version(ver2)]

        return versions[-1] if len(versions) else None

    def _getStageRoot(self, version: str) -> dict:
        root = self.package_json["versions"]["default"].copy()
        for ver in self.versions:
            if ver == version:
                sge = self.package_json["versions"][ver]
                root = MergeDict(root, sge)
                break

        return root

    def _addSessionVariable(self, session: dict, section: dict) -> dict:
        keys = list(filter(lambda x: x not in Package.RESERVED_KEYS, section.keys()))
        for key in keys:
            v = self._evalValue(session, section[key])
            session[key] = v
            section[key] = v
        return session

    def _createSession(
        self, root: dict | None = None, settings: dict | None = None, depdentpath: dict | None = None
    ) -> dict:

        plat_vers = {}
        toolpaths = None
        if self.platform:
            toolpaths = self.platform.GetToolsPaths()
            plat_vers = {
                "rootdir": self.platform.rootdir,
                "package_rootdir": self.platform.package_rootdir,
                "setting_rootdir": self.platform.setting_rootdir,
                "tools_rootdir": self.platform.tools_rootdir,
                "cache_rootdir": self.platform.cache_rootdir,
                "source_rootdir": self.platform.source_rootdir,
                "dist_rootdir": self.platform.dist_rootdir,
                "cuda_root": self.platform.cuda_root,
                "cuda_versions": self.platform.cuda_versions,
                "cuda_enable_default": self.platform.cuda_enable_default,
                "cuda_version_default": self.platform.cuda_version_default,
                "cuda_latest_version": self.platform.cuda_latest_version,
                "visual_studio_infos": self.platform.visual_studio_infos,
                "visual_studio_current": self.platform.visual_studio_current,
                "msvc_toolset_versions": self.platform.msvc_toolset_versions,
                "msvc_toolset_version_default": self.platform.msvc_toolset_version_default,
                "msvc_runtime_library_default": self.platform.msvc_runtime_library_default,
                "build_arch_default": self.platform.build_arch_default,
                "build_library_default": self.platform.build_library_default,
                "msvc_generator": self.platform.msvc_generator,
            }

        session = {
            "package_dir": self.package_dir,
            "versions": self.versions,
            "latest_version": self.latest_version,
        }
        if depdentpath and "release" in depdentpath:
            session["dependent_packages_release"] = depdentpath["release"]
            dlst = []
            for dir in depdentpath["release"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.pc", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["pkg_config_path_release"] = ";".join(set(dlst))
            dlst = []
            for dir in depdentpath["release"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.dll", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["dependent_dlls_release"] = ";".join(set(dlst))
        else:
            session["dependent_packages_release"] = ""
            session["pkg_config_path_release"] = ""
            session["dependent_dlls_release"] = ""

        if depdentpath and "debug" in depdentpath:
            session["dependent_packages_debug"] = depdentpath["debug"]
            dlst = []
            for dir in depdentpath["debug"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.pc", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["pkg_config_path_debug"] = ";".join(set(dlst))
            dlst = []
            for dir in depdentpath["debug"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.dll", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["dependent_dlls_debug"] = ";".join(set(dlst))
        else:
            session["dependent_packages_debug"] = ""
            session["pkg_config_path_debug"] = ""
            session["dependent_dlls_debug"] = ""

        session = MergeDict(plat_vers, session)
        if settings:
            session = self._addSessionVariable(session, settings)
        if self.package_json:
            session = self._addSessionVariable(session, self.package_json)
        if root:
            session = self._addSessionVariable(session, root)

        return session

    def _setupEnvironment(self, session: dict, root: dict, settings: dict | None = None):
        os.environ["CUDA_PATH"] = ""
        os.environ["CUDNN_PATH"] = ""
        self.env["CUDA_PATH"] = ""
        self.env["CUDNN_PATH"] = ""
        self.env["DOTNET_CLI_UI_LANGUAGE"] = "en"
        self.env["VSLANG"] = "1033"
        self.env["PYTHONUNBUFFERED"] = "1"
        self.env["PYTHONUTF8"] = "1"
        self.env["LC_ALL"] = "C"
        self.env["LANG"] = "ja_JP.UTF-8"

        envs = {}
        build_arch = ""
        msvc_toolset_version = ""
        toolpaths = None
        if settings and "build_arch" in settings:
            build_arch = settings["build_arch"]
        if settings and "msvc_toolset_version" in settings:
            msvc_toolset_version = settings["msvc_toolset_version"]
        envs = self.platform.GetMsvcEnvironment(build_arch=build_arch, msvc_toolset_version=msvc_toolset_version)

        for k, v in envs.items():
            self.env[k] = os.path.expandvars(v)

        if root and "environments" in root:
            for k, v in root["environments"].items():
                self.env[k] = self._evalValue(session, v)

        path = os.path.expandvars(SYSTEM_PATH)
        if "PATH" in envs:
            path = ";".join([envs["PATH"], path])
        toolpaths = self.platform.GetToolsPaths()
        if toolpaths:
            path = ";".join([toolpaths, path])
        self.env["PATH"] = path
        os.environ["PATH"] = path

    def _isFinishedStage(self, stage: str) -> None:
        res = next((item for item in self.stages_finished if item["stage"] == stage), None)
        if res:
            return True
        return False

    def StopBuild(self):
        self.running = False
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.shell.kill())

    def _evalValue(self, session: dict, source):
        if not source:
            return source
        elif isinstance(source, list):
            result = []
            for item in source:
                result.append(self._evalValue(session, item))
            return result
        elif isinstance(source, dict):
            result = {}
            for k, v in source.items():
                result[k] = self._evalValue(session, v)
            return result
        elif isinstance(source, str):
            return self._evalValueOne(session, source)
        else:
            return source

    def _expandEnvs(self, src: str, escape: bool = False) -> str:
        dst = ""
        nst = 0
        code = src
        for n in regex.finditer(r"%%(\w+?)%%|%(\w+?)%", src):
            nsp = n.span()
            if n.lastindex == 1:
                vn = str(n.group(n.lastindex))
                es = f"%{vn}%"
            elif n.lastindex:
                vn = str(n.group(n.lastindex))
                if vn in self.env:
                    e = self.env[vn]
                    es = e.replace("\\", "\\\\") if escape else e
                else:
                    e = os.environ.get(vn)
                    if e:
                        es = e.replace("\\", "\\\\") if escape else e
                    else:
                        es = f"%{vn}%"
            else:
                es = src[nsp[0] : nsp[1]]

            dst += src[nst : nsp[0]] + es
            nst = nsp[1]
        dst += src[nst:]
        return dst if dst else src

    def _evalValueOne(self, session: dict, code: str):
        try:
            dst = ""
            st = 0
            ms = None
            for m in regex.finditer(Package.CODE_PATTERN, code):
                sp = m.span()
                pycode = m.group(1)[2:-2].strip()
                if sp[0] == 0 and sp[1] == len(code):  # when value is '{{ expr }}'; return object
                    pydst = ""
                    nst = 0
                    for n in regex.finditer(Package.VARIAVLE_PATTERN, pycode):
                        nsp = n.span()
                        vn = n.group(n.lastindex)
                        vs = ""
                        ic = 0
                        if n.lastindex <= 2:
                            vs = vn
                        elif n.lastindex <= 4:
                            vs = vn
                            ic = 1
                        elif n.lastindex == 5:
                            vs = f"${vn}"
                        else:
                            vs = f"${{{vn}}}"
                        pydst += pycode[nst : nsp[0] + ic] + vs
                        nst = nsp[1]
                    pydst += pycode[nst:]
                    pydst = self._expandEnvs(pydst, True)
                    obj = eval(pydst, None, session)
                    return obj
                ndst = ""
                nsrc = code[st : sp[0]]
                nst = 0
                for n in regex.finditer(Package.VARIAVLE_PATTERN, nsrc):
                    nsp = n.span()
                    vn = n.group(n.lastindex)
                    ic = 0
                    if n.lastindex <= 2:
                        vs = str(session[vn])
                    elif n.lastindex <= 4:
                        vs = str(session[vn])
                        ic = 1
                    elif n.lastindex == 5:
                        vs = f"${vn}"
                    else:
                        vs = f"${{{vn}}}"
                    npre = self._expandEnvs(nsrc[nst : nsp[0] + ic])
                    ndst += npre + vs
                    nst = nsp[1]
                ndst += self._expandEnvs(nsrc[nst:])
                dst += ndst
                pydst = ""
                nst = 0
                for n in regex.finditer(Package.VARIAVLE_PATTERN, pycode):
                    nsp = n.span()
                    vn = n.group(n.lastindex)
                    vs = ""
                    ic = 0
                    if n.lastindex <= 2:
                        vs = vn
                    elif n.lastindex <= 4:
                        vs = vn
                        ic = 1
                    elif n.lastindex == 5:
                        vs = f"${vn}"
                    else:
                        vs = f"${{{vn}}}"
                    npre = self._expandEnvs(pycode[nst : nsp[0] + ic], True)
                    pydst += npre + vs
                    nst = nsp[1]
                pydst += self._expandEnvs(pycode[nst:], True)
                obj = eval(pydst, None, session)
                dst += str(obj)
                st = sp[1]
            nsrc = code[st:]
            ndst = ""
            nst = 0
            for n in regex.finditer(Package.VARIAVLE_PATTERN, nsrc):
                nsp = n.span()
                vn = n.group(n.lastindex)
                vs = ""
                ic = 0
                if n.lastindex <= 2:
                    vs = str(session[vn])
                elif n.lastindex <= 4:
                    vs = str(session[vn])
                    ic = 1
                elif n.lastindex == 5:
                    vs = f"${vn}"
                else:
                    vs = f"${{{vn}}}"
                npre = self._expandEnvs(nsrc[nst : nsp[0] + ic])
                ndst += npre + vs
                nst = nsp[1]
            ndst += self._expandEnvs(nsrc[nst:])
            dst += ndst
            return dst
        except Exception as e:
            Post.Error(f"Syntax error: '{code}'")
            raise e

    def _putFinishedStage(self, stage: str) -> None:
        self.stages_finished.append(
            {
                "stage": stage,
                "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            }
        )
        self.setting_modified = True
        self._saveSetting()

    def _changeStage(self, stage: str) -> None:
        idx = Package.STAGES_ORDER.index(stage)
        stages = Package.STAGES_ORDER[:idx]
        self.stages_finished = [x for x in self.stages_finished if x["stage"] in stages]
        self._saveSetting(force=True)

    def _executeScript(self, session: dict, script: dict) -> Reaseon:
        when = True
        if "when" in script:
            when = self._evalValue(session, script["when"])

        chdir = ""
        if "chdir" in script:
            chdir = self._evalValue(session, script["chdir"])

        code = ""
        if "script" in script:
            code = self._evalValue(session, script["script"])

        failed = ""
        if "failed" in script:
            failed = self._evalValue(session, script["failed"])

        environments = {}
        if "environments" in script:
            environments = script["environments"]

        message = ""
        if "message" in script:
            message = self._evalValue(session, script["message"])

        if when:
            if code:
                if chdir:
                    os.chdir(chdir)
                    Post.Info(f"  cd {chdir}")
                if environments:
                    for k, v in environments.items():
                        self.env[k] = self._evalValue(session, v)
                if message:
                    Post.Info(message)
                Post.Info(f"  {code}")
                result = self.shell.exec(code, env=self.env)
                os.environ["errorlevel"] = str(result.exitcode)
                ignore_errors = False
                if "ignore_errors" in script:
                    ignore_errors = self._evalValue(session, script["ignore_errors"])
                if result.killed:
                    Post.Error(f"User Interrupted.")
                    return Package.Reaseon.USER_INTERRUPTED
                elif result.exitcode and failed:
                    Post.Info(f"ExiteCode={result.exitcode}, is failed so run: {failed}")
                    self.shell.exec(failed, env=self.env)
                    return Package.Reaseon.ERROR
                elif result.exitcode and not ignore_errors:
                    Post.Error(f"ExiteCode={result.exitcode}")
                    return Package.Reaseon.ERROR
        return Package.Reaseon.COMPLETED

    def _executeStage(self, session: dict, stage: dict) -> Reaseon:
        session = self._addSessionVariable(session, stage)
        ret = Package.Reaseon.ERROR
        if "environments" in stage:
            for k, v in stage["environments"].items():
                self.env[k] = self._evalValue(session, v)
        for script in stage["scripts"]:
            ret = self._executeScript(session, script)
            if ret != Package.Reaseon.COMPLETED:
                break
        return ret

    def RunStages(self, request: dict | None = None) -> Reaseon:
        try:
            self.running = True
            start_time = datetime.datetime.now()
            self.process_seconds = 0
            Post.Info(f"[{self.display}] Run statges.....")
            self._loadSettings()
            if request:
                request = self.GetSettingsFromRequest(request=request)
                differ = self._differSettings(settings=request)
                if differ:
                    self.settings = request.copy()
                    self._changeStage(differ)
            settings = self.settings.copy()
            self._saveSetting()

            dpepath = self._getDepedentPackagePaths(settings)
            stage_root = self._getStageRoot(settings["version"])
            session = self._createSession(root=stage_root, settings=settings, depdentpath=dpepath)
            self._setupEnvironment(session, stage_root, settings)

            stage_key = list(stage_root["stages"].keys())
            stage_key.sort(key=lambda k: Package.STAGES_ORDER.index(k))
            for stage in stage_key:
                if not self._isFinishedStage(stage):
                    if not self.running:
                        Post.Status(f"[{self.display}] interrupted.")
                        Post.Info(f"[{self.display}] interrupted.")
                        return Package.Reaseon.USER_INTERRUPTED
                    Post.Status(f"[{self.display}] stage: {stage}")
                    res = self._executeStage(session, stage_root["stages"][stage])

                    if res == Package.Reaseon.USER_INTERRUPTED:
                        Post.Status(f"[{self.display}] interrupted.")
                        Post.Info(f"[{self.display}] interrupted.")
                        return res
                    if res == Package.Reaseon.ERROR:
                        Post.Status(f"[{self.display}] Error.")
                        Post.Info(f"[{self.display}] Error.")
                        return res
                    self._putFinishedStage(stage)

            delta = datetime.datetime.now() - start_time
            self.process_seconds = delta.total_seconds()
            Post.Status(f"[{self.display}] finished.")
            Post.Info(f"[{self.display}] finished.")
            Post.Info(f"[{self.display}] process time: {self.process_seconds}")
            return Package.Reaseon.COMPLETED

        except Exception as e:
            Post.Error(f"[{self.display}] Except: {e}")
            Post.Error(traceback.format_exc())
            return Package.Reaseon.ERROR
