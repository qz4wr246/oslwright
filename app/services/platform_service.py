"""
Platform Service.

"""

import glob
import time
import io
import os
import re
import shutil
import winreg
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Tuple, Dict

import pyjson5 as json
from fletx.core import FletXService
from natsort import natsorted

from ..core.shell import SYSTEM_PATH, Shell
from ..core.common import get_app_root, get_data_path, get_assets_dir
from ..core.logger import PostLogger as Post
from ..models.package_model import PackageModel
from ..models.app_setting_model import AppSettingModel
from ..models.platform_reason_model import PlatformReason, ReasonCode
from ..models.visual_stuido_model import VisualStudioInstallation, MsvcToolSet, VisualStuioInfomation

SYSTEM_ENVIRONMENT_NAME_LIST = [
    "ALLUSERSPROFILE",
    "APPDATA",
    "ComSpec",
    "COMPUTERNAME",
    "CommonProgramFiles",
    "CommonProgramFiles(x86)",
    "CommonProgramW6432",
    "PUBLIC",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "LOGONSERVER",
    "PATHEXT",
    "ProgramData",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "ProgramW6432",
    "PSModulePath",
    "SystemDrive",
    "SystemRoot",
    "TEMP",
    "TMP" "USERNAME",
    "USERPROFILE",
    "USERDOMAIN",
    "USERDOMAIN_ROAMINGPROFILE",
    "windir",
]


class PlatformService(FletXService):
    """Platform Service"""

    def __init__(self):
        # print("PlatformService:__init__")
        self.packages = []
        self.git_exe: Path | None = None
        self.gitlfs_exe: Path | None = None
        self.cmake_exe: Path | None = None
        self.sevenzip_exe: Path | None = None
        self.python_exe: Path | None = None
        self.py_exe: Path | None = None
        self.nasm_exe: Path | None = None
        self.perl_exe: Path | None = None
        self.pkg_config_exe: Path | None = None
        self.ninja_exe: Path | None = None
        self.meson_exe: Path | None = None
        self.jinja2_exe: Path | None = None
        self.gn_exe: Path | None = None
        self.msys2_exe: Path | None = None
        self.bison_flex_exe: Path | None = None
        self.yasm_exe: Path | None = None

        self.rootdir = get_app_root()
        self.package_rootdir = get_data_path("packages")
        self.option_rootdir = get_data_path("options")
        self.source_rootdir = get_data_path("sources")
        self.dist_rootdir = get_data_path("dist")
        self.cache_rootdir = get_data_path("cache")
        self.tools_rootdir = get_data_path("tools")
        self.logs_rootdir = get_data_path("logs")
        self.assets_rootdir = get_assets_dir()
        self.msvc_environment_cache = {}
        self.msvc_generator = None
        self.visual_studio_infos = None
        self.visual_studio_current = None
        self.msvc_toolset_version_default = None
        self.msvc_toolset_versions = None
        self.msvc_runtime_library_default = "md"
        self.build_arch_default = "x64"
        self.build_library_default = "shared"
        self.cuda_root = None
        self.cuda_enable_default = False
        self.cuda_versions = None
        self.cuda_version_default = None
        self.cuda_latest_version = None
        self.cuda_path_default = None
        self.app_setting = None
        self.reason = PlatformReason(code=ReasonCode.UNINITIALIZED)
        self.system_envitonment = {}
        # Init base class
        super().__init__(name="PlatformService")

    def on_start(self):
        """Do stuf here on PlatformService start"""
        # print("PlatformService:on_start")
        self.package_rootdir.mkdir(parents=True, exist_ok=True)
        self.option_rootdir.mkdir(parents=True, exist_ok=True)
        self.source_rootdir.mkdir(parents=True, exist_ok=True)
        self.dist_rootdir.mkdir(parents=True, exist_ok=True)
        self.cache_rootdir.mkdir(parents=True, exist_ok=True)
        self.tools_rootdir.mkdir(parents=True, exist_ok=True)
        self.logs_rootdir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
        self.reason = self.check_platform()
        self.system_envitonment = self.get_system_default_environment()

    def on_stop(self):
        """Do stuf here on PlatformService stop"""
        # print("PlatformService:on_stop")

    def get_platform_reason(self):
        return self.reason

    def check_platform(self) -> PlatformReason:
        self.visual_studio_infos = self._getVisualStudioInofs()
        if not self.visual_studio_infos:
            return PlatformReason(code=ReasonCode.MISSING_VISUALSTUDIO)
        if self.visual_studio_infos:
            self.visual_studio_current = self.visual_studio_infos[0]
        if self.visual_studio_current:
            self.msvc_toolset_versions = [v.name for v in self.visual_studio_current.msvc_toolset_versions]
            self.msvc_toolset_version_default = self.visual_studio_current.msvc_toolset_version_default.name
            self.msvc_generator = self.visual_studio_current.generator
            self.msvc_version_default = self.visual_studio_current.generator

        self.cuda_root = self._getCudaRoot()
        self.cuda_versions = self._getCudaVersions()
        if self.cuda_versions:
            self.cuda_latest_version = self.cuda_versions[-1]
            self.cuda_version_default = self.cuda_latest_version
            self.cuda_enable_default = True
            self.cuda_path_default = self._getCudaPath(self.cuda_latest_version)
            Post.gui(f"Found CUDA: {self.cuda_versions}")

        setting = self.load_setting()
        msvc_version = setting.values["msvc_version_default"]
        vs_target = next((x for x in self.visual_studio_infos if x.generator == msvc_version), None)
        if vs_target:
            self.visual_studio_current = vs_target
            self.msvc_toolset_versions = [v.name for v in self.visual_studio_current.msvc_toolset_versions]
            self.msvc_toolset_version_default = self.visual_studio_current.msvc_toolset_version_default.name
            self.msvc_generator = self.visual_studio_current.generator

        self._updateToolPath()
        if (
            not self.cmake_exe
            or not self.git_exe
            or not self.gitlfs_exe
            or not self.sevenzip_exe
            or not self.python_exe
        ):
            mesg = ""
            mesg += "CMake not found.\n" if not self.cmake_exe else ""
            mesg += "Git not found.\n" if not self.git_exe else ""
            mesg += "Git LFS not found.\n" if not self.gitlfs_exe else ""
            mesg += "7z not found.\n" if not self.sevenzip_exe else ""
            mesg += "Python not found.\n" if not self.python_exe else ""
            mesg += "Python Launcher not found.\n" if not self.py_exe else ""
            return PlatformReason(code=ReasonCode.MISSING_BASE_TOOLS, message=mesg)

        if (
            not self.nasm_exe
            or not self.perl_exe
            or not self.pkg_config_exe
            or not self.ninja_exe
            or not self.meson_exe
            or not self.jinja2_exe
            or not self.gn_exe
            or not self.msys2_exe
            or not self.bison_flex_exe
            or not self.yasm_exe
        ):
            mesg = ""
            mesg += "NASM not found.\n" if not self.nasm_exe else ""
            mesg += "YASM not found.\n" if not self.yasm_exe else ""
            mesg += "Perl not found.\n" if not self.perl_exe else ""
            mesg += "pkg-config not found.\n" if not self.pkg_config_exe else ""
            mesg += "Ninja not found.\n" if not self.ninja_exe else ""
            mesg += "Meson not found.\n" if not self.meson_exe else ""
            mesg += "Jinja2 not found.\n" if not self.jinja2_exe else ""
            mesg += "gn not found.\n" if not self.gn_exe else ""
            mesg += "MSYS2 not found.\n" if not self.msys2_exe else ""
            mesg += "Bison,Flex not found.\n" if not self.bison_flex_exe else ""
            return PlatformReason(code=ReasonCode.MISSING_EMBEDDED_TOOLS, message=mesg)

        return PlatformReason(code=ReasonCode.COMPLETE)

    def _getBuildToolsetVersions(self, installationPath: str) -> List[MsvcToolSet]:
        toolset_dict = {}
        # Auxiliary\Build 以下の全 .txt と .props を対象にする
        search_pattern = os.path.join(installationPath, r"VC\Auxiliary\Build\**\*.*")

        for file_path in glob.glob(search_pattern, recursive=True):
            filename = os.path.basename(file_path)

            # 1. ツールセット名 (vc14x) を特定
            # パスに v142, v143, v145 が含まれるか確認
            toolset_match = re.search(r"v(1\d{2})", file_path)
            if not toolset_match:
                continue
            toolset_key = f"vc{toolset_match.group(1)}"

            ver_num = None

            # 2. バージョン番号の抽出
            if filename.endswith(".props"):
                # ファイル名から抽出 (例: Microsoft.VCToolsVersion.VC.14.40.33810.props)
                ver_match = re.search(r"(\d{2}\.\d{2}\.\d{5})", filename)
                if ver_match:
                    ver_num = ver_match.group(1)

            elif filename.endswith(".txt"):
                # ファイルの中身から抽出 (例: 14.40.33810)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        ver_match = re.search(r"(\d{2}\.\d{2}\.\d{5})", content)
                        if ver_match:
                            ver_num = ver_match.group(1)
                except Exception:
                    continue

            # 3. 辞書に格納 (最新版を優先)
            if ver_num:
                if toolset_key not in toolset_dict or ver_num > toolset_dict[toolset_key]:
                    toolset_dict[toolset_key] = ver_num
        result = []
        for n, v in toolset_dict.items():
            result.append(MsvcToolSet(n, v))

        result[-1].default = True
        return result

    def _getVisualStudioInofs(self) -> list[VisualStuioInfomation] | None:
        Post.info("Checking for Visual Studio...")
        vs_where_exe = Path(os.environ.get("ProgramFiles(x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"  # type: ignore
        if not os.path.isfile(vs_where_exe):
            Post.error("Visual Studio is not installed.")
            return None
        Post.info("Found Visual Studio Installer.")
        shell = Shell()
        result = shell.exec(
            f'"{vs_where_exe}" -prerelease -nocolor -nologo -legacy -sort -format json -utf8', with_content=True
        )
        if result.exitcode:
            Post.error("Cannot get information about Visual Studio.")
            return None
        elif not len(result.stdout) if result.stdout else False:
            Post.error("vswhere returned no result.")
            return None
        vs_infos = []
        infos = []
        try:
            infos_dict = json.loads(result.stdout) if result.stdout else []
            for info in infos_dict:
                infos.append(VisualStudioInstallation.from_dict(info))

        except Exception as e:
            Post.error("Failed to parse vswhere output.")
            return None
        finally:
            if not infos:
                Post.error("No Visual Studio installations found.")
                return None

        for info in infos:  # type: ignore
            m = re.match(r"^(\d+)\..*$", info.catalog.buildVersion)
            version_short = m.group(1)  # type: ignore
            if info.catalog.featureReleaseYear:
                version_year = info.catalog.featureReleaseYear
            else:
                version_year = info.catalog.productLineVersion
            msvc_generator = f"Visual Studio {version_short} {version_year}"
            msvc_toolset_versions = self._getBuildToolsetVersions(info.installationPath)
            toolset_default = next(filter(lambda d: d.default, msvc_toolset_versions), None)

            msvc_versions = {}
            for toolset in msvc_toolset_versions:
                cl_exe = os.path.join(
                    info.installationPath, "VC", "Tools", "MSVC", toolset.version, "bin", "HostX64", "x64", "cl.exe"
                )
                result = shell.exec(f'"{cl_exe}"', with_content=True)
                if result.exitcode:
                    Post.error("Cannot get information about MSVC version.")
                    return None
                lines = io.StringIO(result.stderr).read().splitlines()
                m = re.match(r".*Version\s+(((\d+)\.\d+)(\.\d+)+).*", lines[0])
                msvc_version_full = m.group(1)  # type: ignore
                msvc_version = m.group(2).replace(".", "")  # type: ignore
                msvc_version_short = m.group(3)  # type: ignore
                msvc_versions[toolset.name] = {}
                msvc_versions[toolset.name]["version_full"] = msvc_version_full
                msvc_versions[toolset.name]["version_short"] = msvc_version_short
                msvc_versions[toolset.name]["version"] = msvc_version

            vs_info = VisualStuioInfomation(
                displayname=info.displayName,
                description=info.description,
                installationpath=info.installationPath,
                installationVersion=info.installationVersion,
                generator=msvc_generator,
                msvc_toolset_versions=msvc_toolset_versions,
                msvc_toolset_version_default=toolset_default,
                msvc_versions=msvc_versions,
            )
            vs_infos.append(vs_info)
            Post.info(f"Found {info.displayName}.")
        return vs_infos

    def GetMsvcEnvironment(
        self,
        build_arch: str | None = None,
        mscv_version: str | None = None,
        msvc_toolset_version: str | None = None,
        mscv_runtime_library: str | None = None,
    ) -> dict | None:

        mscv_version = mscv_version if mscv_version else self.visual_studio_current.generator
        visual_studio = next((vc for vc in self.visual_studio_infos if vc.generator == mscv_version), None)

        arch = "x86" if build_arch and build_arch == "x32" else "amd64"
        vcver = msvc_toolset_version if msvc_toolset_version else visual_studio.msvc_toolset_version_default.name  # type: ignore

        key = (visual_studio.installationpath, arch, vcver)  # type: ignore
        if key in self.msvc_environment_cache:
            return self.msvc_environment_cache[key]

        vs_environment = {}

        path = os.path.expandvars(SYSTEM_PATH)
        path_old = os.environ["PATH"]

        vcver_item = next(
            filter(lambda d: d.name == vcver, visual_studio.msvc_toolset_versions),  # type: ignore
            None,
        )
        vcvars_ver = vcver_item.version if vcver_item else visual_studio.msvc_toolset_version_default.version  # type: ignore

        try:
            # os.environ["PATH"] = path
            dev_cmd_bat = Path(visual_studio.installationpath) / "Common7" / "Tools" / "VsDevCmd.bat"  # type: ignore
            cmd_line = (
                f'cmd /c ""{str(dev_cmd_bat)}" -arch={arch} -host_arch=amd64 -vcvars_ver={vcvars_ver} >nul && set"'
            )

            shell = Shell()
            result = shell.exec(cmd_line, with_content=True, shell=True)
            if result.exitcode:
                Post.error("Cannot get information about MSVC")
                return None
            if not len(result.stdout) if result.stdout else False:
                Post.error("devcmd.bat not result")
                return None

            lines = io.StringIO(result.stdout).read().splitlines()
            for line in lines:
                k, v = line.split("=", 1)
                vs_environment[k] = v

        except:
            Post.error("Exception devcmd ")
        finally:
            os.environ["PATH"] = path_old

        self.msvc_environment_cache[key] = vs_environment
        return vs_environment

    def GetToolsPaths(self) -> str | None:
        path = str()
        if self.git_exe:
            path = ";".join([path, str(self.git_exe.parent)])

        if self.gitlfs_exe:
            path = ";".join([path, str(self.gitlfs_exe.parent)])

        if self.cmake_exe:
            path = ";".join([path, str(self.cmake_exe.parent)])

        if self.ninja_exe:
            path = ";".join([path, str(self.ninja_exe.parent)])

        if self.sevenzip_exe:
            path = ";".join([path, str(self.sevenzip_exe.parent)])

        if self.nasm_exe:
            path = ";".join([path, str(self.nasm_exe.parent)])

        if self.yasm_exe:
            path = ";".join([path, str(self.yasm_exe.parent)])

        if self.pkg_config_exe:
            path = ";".join([path, str(self.pkg_config_exe.parent)])

        if self.perl_exe:
            path = ";".join([path, str(self.perl_exe.parent)])
            path = ";".join(
                [
                    path,
                    str(self.perl_exe.parent / ".." / "site" / "bin"),
                ]
            )

        if self.gn_exe:
            path = ";".join([path, str(self.gn_exe.parent)])

        if self.python_exe:
            path = ";".join([path, str(self.python_exe.parent)])
            path = ";".join([path, os.path.join(str(self.python_exe.parent), "Scripts")])

        if self.py_exe:
            path = ";".join([path, str(self.py_exe.parent)])

        if self.meson_exe:
            path = ";".join([path, str(self.meson_exe.parent)])

        if self.jinja2_exe:
            path = ";".join([path, str(self.jinja2_exe.parent)])

        if self.msys2_exe:
            path = ";".join([path, str(self.msys2_exe.parent)])

        if self.bison_flex_exe:
            path = ";".join([path, str(self.bison_flex_exe.parent)])

        return path[1:]

    def _getCudaRoot(self) -> Path | None:
        cuda_root = Path(os.environ.get("ProgramFiles")) / "NVIDIA GPU Computing Toolkit" / "CUDA"  # type: ignore
        if not cuda_root.is_dir():
            return None
        return cuda_root

    def _getCudaVersions(self):
        versions = []
        vers = [os.path.basename(p.rstrip(os.sep))[1:] for p in glob.glob("v*", root_dir=self.cuda_root)]
        return natsorted(vers)

    def _getCudaPath(self, version: str) -> Path | None:
        if not self.cuda_root:
            return None
        cuda_path = self.cuda_root / f"v{version}"
        if not cuda_path.is_dir():
            return None
        return cuda_path

    def _findGit(self) -> Tuple[Path | None, str | None]:
        git_exe = None
        git_version = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows")
            instpath, _ = winreg.QueryValueEx(key, "InstallPath")
            _exe = Path(instpath) / "bin" / "git.exe"
            if _exe.is_file():
                git_exe = _exe
        except:
            pass
        if not git_exe:
            _exe = Path(os.environ.get("LocalAppData")) / "Programs" / "Git" / "bin" / "git.exe"  # type: ignore
            if _exe.is_file():
                git_exe = _exe
        if not git_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "Git" / "bin" / "git.exe"  # type: ignore
            if _exe.is_file():
                git_exe = _exe
        if not git_exe:
            _exe = shutil.which("git.exe")
            if _exe and Path(_exe).is_file():
                git_exe = Path(_exe)
        if not git_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{git_exe}" -v', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            git_version = ver[2] if len(ver) == 3 else None
        return (git_exe, git_version)

    def _findGitLFS(self) -> Tuple[Path | None, str | None]:
        gitlfs_exe = None
        gitlfs_version = None
        _exe = Path(os.environ.get("ProgramFiles")) / "Git LFS" / "git-lfs.exe"  # type: ignore
        if _exe.is_file():
            gitlfs_exe = _exe

        if not gitlfs_exe:
            _exe = shutil.which("git-lfs.exe")
            if _exe and Path(_exe).is_file():
                gitlfs_exe = Path(_exe)
        if not gitlfs_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{gitlfs_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = re.split(r"[ /]+", result.stdout)
            gitlfs_version = ver[1] if len(ver) >= 2 else None
        return (gitlfs_exe, gitlfs_version)

    def _findCMake(self) -> Tuple[Path | None, str | None]:
        cmake_exe = None
        cmake_version = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Kitware\CMake")
            instpath, _ = winreg.QueryValueEx(key, "InstallDir")
            _exe = Path(instpath) / "bin" / "cmake.exe"
            if _exe.is_file():
                cmake_exe = _exe
        except:
            pass
        if not cmake_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "CMake" / "bin" / "cmake.exe"  # type: ignore
            if _exe.is_file():
                cmake_exe = _exe
        if not cmake_exe:
            _exe = shutil.which("cmake.exe")
            if _exe and Path(_exe).is_file():
                cmake_exe = Path(_exe)
        if not cmake_exe:
            return (None, None)

        shell = Shell()
        result = shell.exec(f'"{cmake_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            cmake_version = ver[2] if len(ver) >= 3 else None
        return (cmake_exe, cmake_version)

    def _findNinja(self) -> Tuple[Path | None, str | None]:
        ninja_exe = None
        ninja_version = None
        _exe = Path(self.rootdir) / ".venv" / "Scripts" / "ninja.exe"
        if _exe.is_file():
            ninja_exe = _exe
        if not ninja_exe:
            _exe = shutil.which("ninja.exe")
            if _exe and Path(_exe).is_file():
                ninja_exe = Path(_exe)

        if not ninja_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{ninja_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = re.split(r"[.]+", result.stdout)
            ninja_version = f"{ver[0]}.{ver[1]}.{ver[2]}" if len(ver) >= 3 else None
        return (ninja_exe, ninja_version)

    def _findNasm(self) -> Tuple[Path | None, str | None]:
        nasm_exe = None
        nasm_verson = None
        if not nasm_exe:
            _exe = self.tools_rootdir / "nasm" / "bin" / "nasm.exe"
            if _exe.is_file():
                nasm_exe = _exe
        if not nasm_exe:
            _exe = Path(os.environ.get("LocalAppData")) / "bin" / "NASM" / "nasm.exe"  # type: ignore
            if _exe.is_file():
                nasm_exe = _exe
        if not nasm_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "NASM" / "nasm.exe"  # type: ignore
            if _exe.is_file():
                nasm_exe = _exe
        if not nasm_exe:
            _exe = shutil.which("nasm.exe")
            if _exe and Path(_exe).is_file():
                nasm_exe = Path(_exe)
        if not nasm_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{nasm_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            nasm_verson = ver[2] if len(ver) >= 3 else None
        return (nasm_exe, nasm_verson)

    def _findYasm(self) -> Tuple[Path | None, str | None]:
        yasm_exe = None
        yasm_version = None
        _exe = self.tools_rootdir / "yasm" / "vsyasm.exe"
        if _exe.is_file():
            yasm_exe = _exe

        if not yasm_exe:
            _exe = Path(os.environ.get("LocalAppData")) / "bin" / "YASM" / "vsyasm.exe"  # type: ignore
            if _exe.is_file():
                yasm_exe = _exe
        if not yasm_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "YASM" / "vsyasm.exe"  # type: ignore
            if _exe.is_file():
                yasm_exe = _exe
        if not yasm_exe:
            _exe = shutil.which("vsyasm.exe")
            if _exe and Path(_exe).is_file():
                yasm_exe = Path(_exe)

        if not yasm_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{yasm_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            yasm_version = ver[1] if len(ver) >= 2 else None
        return (yasm_exe, yasm_version)

    def _findPerl(self) -> Tuple[Path | None, str | None]:
        perl_exe = None
        perl_version = None
        _exe = self.tools_rootdir / "perl" / "perl" / "bin" / "perl.exe"
        if _exe.is_file():
            perl_exe = _exe

        if not perl_exe:
            _exe = Path("C:") / "Strawberry" / "perl" / "bin" / "perl.exe"
            if _exe.is_file():
                perl_exe = _exe
        if not perl_exe:
            _exe = shutil.which("perl.exe")
            if _exe and Path(_exe).is_file():
                perl_exe = Path(_exe)

        if not perl_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{perl_exe}" -v | findstr /C:"perl"', with_content=True, shell=True)
        if not result.exitcode:
            ver = re.split(r"[ ,.()]+", result.stdout)
            perl_version = f"{ver[3]}.{ver[5]}.{ver[7]}"
        return (perl_exe, perl_version)

    def _findPython(self) -> Tuple[Path | None, str | None]:
        python_exe = None
        python_version = None
        _exe = self.rootdir / ".venv" / "Scripts" / "python.exe"
        if _exe.is_file():
            python_exe = _exe
        if not python_exe:
            _root = Path(os.environ.get("LocalAppData")) / "Programs" / "Python"  # type: ignore
            if _root.is_dir():
                vers = glob.glob("*", root_dir=_root)
                vers = natsorted(vers)
                _exe = _root / vers[0] / "python.exe"
                if _exe.is_file():
                    python_exe = _exe
        if not python_exe:
            _root = Path(os.environ.get("ProgramFiles")) / "Python"  # type: ignore
            if _root.is_dir():
                vers = glob.glob("*", root_dir=_root)
                vers = natsorted(vers)
                _exe = _root / vers[0] / "python.exe"
                if _exe.is_file():
                    python_exe = _exe
        if not python_exe:
            _root = Path(os.environ.get("ProgramFiles(x86)")) / "Python"  # type: ignore
            if _root.is_dir():
                vers = glob.glob("*", root_dir=_root)
                vers = natsorted(vers)
                _exe = _root / vers[0] / "python.exe"
                if _exe.is_file():
                    python_exe = _exe
        if not python_exe:
            _exe = shutil.which("python.exe")
            if _exe and Path(_exe).is_file():
                python_exe = Path(_exe)
        if not python_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{python_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            python_version = ver[1] if len(ver) >= 2 else None
        return (python_exe, python_version)

    def _findPythonLauncher(self) -> Tuple[Path | None, str | None]:
        py_exe = None
        py_version = None

        _exe = Path(os.environ.get("LocalAppData")) / "Programs" / "Python" / "Launcher" / "py.exe"  # type: ignore
        if _exe.is_file():
            py_exe = _exe
        if not py_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "Python" / "Launcher" / "py.exe"  # type: ignore
            if _exe.is_file():
                py_exe = _exe
        if not py_exe:
            _exe = shutil.which("py.exe")
            if _exe and Path(_exe).is_file():
                py_exe = Path(_exe)
        if not py_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{py_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            py_version = ver[1] if len(ver) >= 2 else None
        return (py_exe, py_version)

    def _findPkgConfig(self) -> Tuple[Path | None, str | None]:
        pkgcnf_exe = None
        pkgcnf_version = None
        if not pkgcnf_exe:
            _exe = self.tools_rootdir / "pkg-config" / "bin" / "pkg-config.exe"
            if _exe.is_file():
                pkgcnf_exe = _exe
        if not pkgcnf_exe:
            _exe = Path("C:") / "pkg-config" / "bin" / "pkg-config.exe"
            if _exe.is_file():
                pkgcnf_exe = _exe

        if not pkgcnf_exe:
            _exe = shutil.which("pkg-config.exe")
            if _exe and Path(_exe).is_file():
                return Path(_exe)
        if not pkgcnf_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{pkgcnf_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            pkgcnf_version = result.stdout.split()[0] if result.stdout else None
        return (pkgcnf_exe, pkgcnf_version)

    def _findGN(self) -> Tuple[Path | None, str | None]:
        gn_exe = None
        gn_version = None
        _exe = self.tools_rootdir / "gn" / "gn.exe"
        if _exe.is_file():
            gn_exe = _exe
        if not gn_exe:
            _exe = shutil.which("gn.exe")
            if _exe and Path(_exe).is_file():
                gn_exe = Path(_exe)
        if not gn_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{gn_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            gn_version = ver[0] if len(ver) >= 1 else None
        return (gn_exe, gn_version)

    def _findMeson(self) -> Tuple[Path | None, str | None]:
        meson_exe = None
        meson_version = None

        _exe = self.rootdir / ".venv" / "Scripts" / "meson.exe"
        if _exe.is_file():
            meson_exe = _exe

        if not meson_exe:
            _exe = shutil.which("meson.exe")
            if _exe and Path(_exe).is_file():
                meson_exe = Path(_exe)
        if not meson_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{meson_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            meson_version = result.stdout.split()[0] if result.stdout else None
        return (meson_exe, meson_version)

    def _findJinja2(self) -> Tuple[Path | None, str | None]:
        jinja2_exe = None
        jinja2_version = None
        if not jinja2_exe:
            _exe = self.rootdir / ".venv" / "Scripts" / "jinja2.exe"
            if _exe.is_file():
                jinja2_exe = _exe
        if not jinja2_exe:
            _exe = shutil.which("jinja2.exe")
            if _exe and Path(_exe).is_file():
                jinja2_exe = Path(_exe)
        if not jinja2_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{jinja2_exe}" --version 2>&1| findstr /C:"- Jinja2"', with_content=True, shell=True)
        if not result.exitcode:
            _ver = result.stdout.split()
            jinja2_version = _ver[2] if len(_ver) >= 3 else None
        return (jinja2_exe, jinja2_version)

    def _find7zip(self) -> Tuple[Path | None, str | None]:
        svnzip_exe = None
        svnzip_versoin = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\7-Zip")
            instpath, _ = winreg.QueryValueEx(key, "Path64")
            _exe = Path(instpath) / "7z.exe"
            if _exe.is_file():
                svnzip_exe = _exe
        except:
            pass
        if not svnzip_exe:
            _exe = Path(os.environ.get("ProgramFiles")) / "7-zip" / "7z.exe"  # type: ignore
            if _exe.is_file():
                svnzip_exe = _exe
        if not svnzip_exe:
            _exe = shutil.which("7z.exe")
            if _exe and Path(_exe).is_file():
                svnzip_exe = Path(_exe)

        if not svnzip_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{svnzip_exe}" | findstr /C:"7-Zip"', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            svnzip_versoin = ver[1] if len(ver) >= 2 else None
        return (svnzip_exe, svnzip_versoin)

    def _findMsys2(self) -> Tuple[Path | None, str | None]:
        msys2_exe = None
        msys2_version = None
        if not msys2_exe:
            _exe = self.tools_rootdir / "msys2" / "msys64" / "msys2_shell.cmd"
            if _exe.is_file():
                msys2_exe = _exe
        if not msys2_exe:
            _exe = shutil.which("msys2_shell.cmd")
            if _exe and Path(_exe).is_file():
                msys2_exe = Path(_exe)
        if not msys2_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(
            f'"{msys2_exe}" -defterm -no-start -msys -c "pacman -Q msys2-runtime" 2>&1', with_content=True, shell=True
        )
        if not result.exitcode:
            ver = result.stdout.split()
            msys2_version = ver[1] if len(ver) >= 2 else None
        return (msys2_exe, msys2_version)

    def _findBisonFlex(self) -> Tuple[Path | None, str | None]:
        bison_flex_exe = None
        bison_flex_version = None
        if not bison_flex_exe:
            _exe = self.tools_rootdir / "winflexbison" / "winflexbison" / "bison.exe"
            if _exe.is_file():
                bison_flex_exe = _exe
        if not bison_flex_exe:
            _exe = shutil.which("bison.exe")
            if _exe and Path(_exe).is_file():
                bison_flex_exe = Path(_exe)
        if not bison_flex_exe:
            return (None, None)
        shell = Shell()
        result = shell.exec(f'"{bison_flex_exe}" --version', with_content=True, shell=True)
        if not result.exitcode:
            ver = result.stdout.split()
            bison_flex_version = ver[3] if len(ver) >= 4 else None
        return (bison_flex_exe, bison_flex_version)

    def _updateToolPath(self) -> None:
        Post.info("Checking for tools...")
        self.git_exe, version = self._findGit()
        if self.git_exe:
            Post.info(f'Found Git: {self.git_exe} (found version "{version}")')
        else:
            Post.warning("Not found Git.")
        self.gitlfs_exe, version = self._findGitLFS()
        if self.gitlfs_exe:
            Post.info(f'Found Git-lfs: {self.gitlfs_exe} (found version "{version}")')
        else:
            Post.warning("Not found Git-lfs.")
        self.cmake_exe, version = self._findCMake()
        if self.cmake_exe:
            Post.info(f'Found CMake: {self.cmake_exe} (found version "{version}")')
        else:
            Post.warning("Not found CMake.")
        self.ninja_exe, version = self._findNinja()
        if self.ninja_exe:
            Post.info(f'Found Ninja: {self.ninja_exe} (found version "{version}")')
        else:
            Post.warning("Not found Ninja.")
        self.sevenzip_exe, version = self._find7zip()
        if self.sevenzip_exe:
            Post.info(f'Found 7z: {self.sevenzip_exe} (found version "{version}")')
        else:
            Post.warning("Not found 7z.")
        self.nasm_exe, version = self._findNasm()
        if self.nasm_exe:
            Post.info(f'Found NASM: {self.nasm_exe} (found version "{version}")')
        else:
            Post.warning("Not found NASM.")
        self.yasm_exe, version = self._findYasm()
        if self.yasm_exe:
            Post.info(f'Found YASM: {self.yasm_exe} (found version "{version}")')
        else:
            Post.warning("Not found YASM.")
        self.perl_exe, version = self._findPerl()
        if self.perl_exe:
            Post.info(f'Found Perl: {self.perl_exe} (found version "{version}")')
        else:
            Post.warning("Not found Perl.")
        self.pkg_config_exe, version = self._findPkgConfig()
        if self.pkg_config_exe:
            Post.info(f'Found pkg-config: {self.pkg_config_exe} (found version "{version}")')
        else:
            Post.warning("Not found pkg-config.")
        self.gn_exe, version = self._findGN()
        if self.gn_exe:
            Post.info(f'Found gn: {self.gn_exe} (found version "{version}")')
        else:
            Post.warning("Not found gn.")
        self.python_exe, version = self._findPython()
        if self.python_exe:
            Post.info(f'Found Python: {self.python_exe} (found version "{version}")')
        else:
            Post.warning("Not found Python.")
        self.py_exe, version = self._findPythonLauncher()
        if self.py_exe:
            Post.info(f'Found Python Launcher: {self.py_exe} (found version "{version}")')
        else:
            Post.warning("Not found Python Launcher.")
        self.meson_exe, version = self._findMeson()
        if self.meson_exe:
            Post.info(f'Found Meson: {self.meson_exe} (found version "{version}")')
        else:
            Post.warning("Not found Meson.")
        self.jinja2_exe, version = self._findJinja2()
        if self.jinja2_exe:
            Post.info(f'Found Jinja2: {self.jinja2_exe} (found version "{version}")')
        else:
            Post.warning("Not found Jinja2.")
        self.msys2_exe, version = self._findMsys2()
        if self.msys2_exe:
            Post.info(f'Found MYSYS2: {self.msys2_exe} (found version "{version}")')
        else:
            Post.warning("Not found MYSYS2.")
        self.bison_flex_exe, version = self._findBisonFlex()
        if self.bison_flex_exe:
            Post.info(f'Found Bison Flex: {self.bison_flex_exe} (found version "{version}")')
        else:
            Post.warning("Not found Bison Flex.")

    def get_package_files(self) -> list[Path]:
        files = list(self.package_rootdir.rglob("package.jsonc"))
        exclude_package_root = self.package_rootdir / "__sample__"
        files = [f for f in files if not f.is_relative_to(exclude_package_root)]
        return files

    def get_tool_package_files(self) -> list[Path]:
        pkgs = []
        if not self.nasm_exe:
            pkgs.append(self.tools_rootdir / "nasm" / "package.jsonc")
        if not self.yasm_exe:
            pkgs.append(self.tools_rootdir / "yasm" / "package.jsonc")
        if not self.perl_exe:
            pkgs.append(self.tools_rootdir / "perl" / "package.jsonc")
        if not self.pkg_config_exe:
            pkgs.append(self.tools_rootdir / "pkg-config" / "package.jsonc")
        if not self.gn_exe:
            pkgs.append(self.tools_rootdir / "gn" / "package.jsonc")
        if not self.msys2_exe:
            pkgs.append(self.tools_rootdir / "msys2" / "package.jsonc")
        if not self.bison_flex_exe:
            pkgs.append(self.tools_rootdir / "winflexbison" / "package.jsonc")
        return pkgs

    def create_session_base(self, package: PackageModel, msvc_version: str | None = None) -> dict:
        if msvc_version:
            visual_studio = next((vc for vc in self.visual_studio_infos if vc.generator == msvc_version), None)
            msvc_toolset_versions = [v.name for v in visual_studio.msvc_toolset_versions]
            msvc_toolset_version_default = visual_studio.msvc_toolset_version_default.name
            msvc_version_default = msvc_version
            msvc_version = msvc_version
            msvc_generator = msvc_version

        else:
            msvc_version = self.app_setting.values["msvc_version_default"]
            visual_studio = next((vc for vc in self.visual_studio_infos if vc.generator == msvc_version), None)
            msvc_toolset_versions = [v.name for v in visual_studio.msvc_toolset_versions]
            msvc_toolset_version_default = self.app_setting.values["msvc_toolset_version_default"]
            msvc_version_default = visual_studio.generator
            msvc_version = visual_studio.generator
            msvc_generator = visual_studio.generator

        plat_vers = {
            "rootdir": self.rootdir,
            "package_rootdir": str(self.package_rootdir),
            "option_rootdir": str(self.option_rootdir),
            "tools_rootdir": str(self.tools_rootdir),
            "cache_rootdir": str(self.cache_rootdir),
            "source_rootdir": str(self.source_rootdir),
            "dist_rootdir": str(self.dist_rootdir),
            "assets_rootdir": str(self.assets_rootdir),
            "cuda_root": str(self.cuda_root),
            "cuda_versions": self.cuda_versions,
            "cuda_enable_default": self.app_setting.values["cuda_enable_default"],
            "cuda_version_default": self.app_setting.values["cuda_version_default"],
            "cuda_latest_version": self.cuda_latest_version,
            "visual_studio_infos": self.visual_studio_infos,
            "visual_studio_current": visual_studio,
            "msvc_toolset_versions": msvc_toolset_versions,
            "msvc_toolset_version_default": msvc_toolset_version_default,
            "msvc_runtime_library_default": self.app_setting.values["msvc_runtime_library_default"],
            "build_arch_default": self.app_setting.values["build_arch_default"],
            "build_library_default": self.app_setting.values["build_library_default"],
            "msvc_generator": msvc_generator,
            "msvc_version_default": msvc_version_default,
            "msvc_versions": [msvc.generator for msvc in self.visual_studio_infos],
            "msvc_version": msvc_generator,
        }
        vers = [k for k in package.versions.keys() if k != "default"]
        session = {
            "name": package.name,
            "package_dir": str(Path(package.path).parent),
            "versions": vers,
            "latest_version": vers[-1],
            "dependent_packages_release": "",
            "dependent_packages_debug": "",
            "dependent_dlls_release": "",
            "dependent_dlls_debug": "",
            "pkg_config_path_release": "",
            "pkg_config_path_debug": "",
        }
        session |= plat_vers
        return session

    def get_default_setting(self):
        default = {
            "msvc_version_default": self.msvc_version_default,
            "build_arch_default": self.build_arch_default,
            "msvc_toolset_version_default": self.msvc_toolset_version_default,
            "msvc_runtime_library_default": self.msvc_runtime_library_default,
            "build_library_default": self.build_library_default,
            "cuda_enable_default": self.cuda_enable_default,
            "cuda_version_default": self.cuda_latest_version,
        }
        return AppSettingModel(default)

    def load_setting(self) -> AppSettingModel:
        path = self.rootdir / "oslwright_setting.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                self.app_setting = AppSettingModel.from_dict(data)
        else:
            self.app_setting = self.get_default_setting()
            self.save_setting(self.app_setting)
        return self.app_setting

    def save_setting(self, setting: AppSettingModel):
        path = self.rootdir / "oslwright_setting.json"
        with path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(setting.to_dict(), f, ensure_ascii=False, indent=2, quote_keys=True)
        self.app_setting = setting

    def get_system_default_environment(self):
        envs = {}
        for name in SYSTEM_ENVIRONMENT_NAME_LIST:
            v = os.environ.get(name)
            if v is not None:
                envs[name] = v
        return envs

    def setup_logging(self):
        logdir = self.logs_rootdir
        basename = "Output.log"
        max_generations = 10
        pattern = re.compile(r"Output\.log\.(\d+)$")

        # 1. 番号付きログを収集
        indexed = []
        for p in logdir.glob(f"{basename}.*"):
            m = pattern.match(p.name)
            if m:
                indexed.append((int(m.group(1)), p))

        # 2. 古い世代を削除（max_generations を超えるもの）
        indexed.sort()  # 小さい順
        for n, p in indexed:
            if n >= max_generations:
                p.unlink()  # 削除
        indexed = [(n, p) for n, p in indexed if n < max_generations]

        # 3. 残った番号付きログを大きい順に +1 へリネーム
        indexed.sort(reverse=True)
        for n, oldpath in indexed:
            newpath = logdir / f"{basename}.{n+1}"
            oldpath.rename(newpath)

        # 4. 番号なし Output.log → Output.log.1
        plain = logdir / basename
        if plain.exists():
            plain.rename(logdir / f"{basename}.1")

        # FletXがinfo以下を無効化しているのを強制的に復活
        logging.disable(logging.NOTSET)
        logging.basicConfig(level=logging.INFO, force=True)

        # ログ出力ファイルを設定
        logfile = self.logs_rootdir / basename
        # ファイル出力用のハンドラーを作成
        file_handler = RotatingFileHandler(
            str(logfile), mode="w", encoding="utf-8", maxBytes=1024 * 1024 * 5, backupCount=10
        )
        formatter = logging.Formatter("%(message)s")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        Post.addHandler(file_handler)

        Post.info("#=============================================================================================")
        Post.info(time.strftime("# OSLwright Start. %Y-%m-%d %H:%M:%S"))
        Post.info("#=============================================================================================")
