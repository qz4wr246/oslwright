import glob
import io
import locale
import os
import re
import shutil
import subprocess
import sys
import winreg
from enum import Enum, auto

import jsonc
from natsort import natsorted

from oslwright.ow_package import Package
from oslwright.ow_utils import SYSTEM_PATH, DictDotNotation, LoadJson5, Post, SaveJson5, Shell


class ReasonCode(Enum):
    COMPLETE = auto()
    MISSING_VISUALSTUDIO = auto()
    MISSING_BASE_TOOLS = auto()
    MISSING_EMBEDDED_TOOLS = auto()


class Reason(DictDotNotation):
    def __init__(self, code: ReasonCode = ReasonCode.COMPLETE, message: str | None = None):
        self.code: ReasonCode = code
        self.message = message


class Platform:
    """ """

    def __init__(self):
        self.packages = []
        self.git_exe = None
        self.gitlfs_exe = None
        self.cmake_exe = None
        self.sevenzip_exe = None
        self.python_exe = None
        self.py_exe = None
        self.nasm_exe = None
        self.perl_exe = None
        self.pkg_config_exe = None
        self.ninja_exe = None
        self.meson_exe = None
        self.jinja2_exe = None
        self.gn_exe = None
        self.msys2_exe = None
        self.bison_flex_exe = None

        if os.path.basename(sys.executable).lower() == "python.exe":
            self.rootdir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
        else:
            self.rootdir = os.path.abspath(os.path.join(sys.executable, os.pardir))

        self.package_rootdir = os.path.join(self.rootdir, "packages")
        self.setting_rootdir = os.path.join(self.rootdir, "settings")
        self.source_rootdir = os.path.join(self.rootdir, "sources")
        self.dist_rootdir = os.path.join(self.rootdir, "dist")
        self.cache_rootdir = os.path.join(self.rootdir, "cache")
        self.tools_rootdir = os.path.join(self.rootdir, "tools")
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
        self.cuda_version_default = None
        self.cuda_latest_version = None

        os.makedirs(self.setting_rootdir, exist_ok=True)
        os.makedirs(self.source_rootdir, exist_ok=True)
        os.makedirs(self.dist_rootdir, exist_ok=True)
        os.makedirs(self.cache_rootdir, exist_ok=True)

    def __del__(self):
        pass

    def CheckPlatform(self) -> Reason:
        self.visual_studio_infos = self._getVisualStudioInofs()
        if not self.visual_studio_infos:
            return Reason(ReasonCode.MISSING_VISUALSTUDIO)
        if self.visual_studio_infos:
            self.visual_studio_current = self.visual_studio_infos[0]
        if self.visual_studio_current:
            self.msvc_toolset_versions = [v["name"] for v in self.visual_studio_current.msvc_toolset_versions]
            self.msvc_toolset_version_default = self.visual_studio_current.msvc_toolset_version_default["name"]
            self.msvc_generator = self.visual_studio_current.generator
            self.msvc_version_short = self

        self.cuda_root = self._getCudaRoot()
        self.cuda_versions = self._getCudaVersions()
        if self.cuda_versions:
            self.cuda_latest_version = self.cuda_versions[-1]
            self.cuda_version_default = self.cuda_latest_version
            self.cuda_enable_default = True

        self.LoadDefaultSetting()
        self.SaveDefaultSetting()

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
            return Reason(ReasonCode.MISSING_BASE_TOOLS, message=mesg)

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
        ):
            mesg = ""
            mesg += "NASM not found.\n" if not self.nasm_exe else ""
            mesg += "Perl not found.\n" if not self.perl_exe else ""
            mesg += "pkg-config not found.\n" if not self.pkg_config_exe else ""
            mesg += "Ninja not found.\n" if not self.ninja_exe else ""
            mesg += "Meson not found.\n" if not self.meson_exe else ""
            mesg += "Jinja2 not found.\n" if not self.jinja2_exe else ""
            mesg += "gn not found.\n" if not self.gn_exe else ""
            mesg += "MSYS2 not found.\n" if not self.msys2_exe else ""
            mesg += "Bison,Flex not found.\n" if not self.bison_flex_exe else ""
            return Reason(ReasonCode.MISSING_EMBEDDED_TOOLS, message=mesg)

        return Reason(ReasonCode.COMPLETE)

    def GetToolsPackage(self) -> list[Package]:
        pkgs = []
        if not self.nasm_exe:
            package_file = os.path.join(self.tools_rootdir, "nasm", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        if not self.perl_exe:
            package_file = os.path.join(self.tools_rootdir, "perl", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        if not self.pkg_config_exe:
            package_file = os.path.join(self.tools_rootdir, "pkg-config", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        if not self.gn_exe:
            package_file = os.path.join(self.tools_rootdir, "gn", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        if not self.msys2_exe:
            package_file = os.path.join(self.tools_rootdir, "msys2", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        if not self.bison_flex_exe:
            package_file = os.path.join(self.tools_rootdir, "winflexbison", "package.jsonc")
            pkgs.append(Package(package_file, platform=self))

        return pkgs

    def LoadPackages(self) -> list[Package]:
        Post.Info("Loading packages....")
        packages = []
        names = glob.glob("*/package.jsonc", root_dir=self.package_rootdir)
        names = [os.path.dirname(x) for x in names]
        if names:
            for name in names:
                pkg = Package(name, self)
                if pkg:
                    packages.append(pkg)
        self.packages = packages
        return packages

    def FindPacakge(self, name: str):
        return next((p for p in self.packages if name == p.name), None)

    def GetTargetPackages(self, target_packages: list[Package]) -> list[Package]:
        build_packages = []
        dependent_requests = []
        for target in target_packages:
            settings = target.GetSettings()
            build_packages.append({"package": target, "settings": settings, "depth": 0})
            deps = target.GetDependencies(request=settings)
            for dep_req in deps:
                dep_pkg = self.FindPacakge(dep_req["name"])
                if not dep_pkg:
                    Post.Error(f"Found not package. '{dep_req['name']}'")
                    raise
                dependent_requests.append({"package": dep_pkg, "settings": dep_req, "depth": 1})

        depth = 2
        while len(dependent_requests):
            n_dependent_requests = []
            for dep in dependent_requests:
                build_packages.append(dep)
                ndeps = dep["package"].GetDependencies(request=dep["settings"])
                for dep_req in ndeps:
                    dep_pkg = self.FindPacakge(dep_req["name"])
                    n_dependent_requests.append({"package": dep_pkg, "settings": dep_req, "depth": depth})
            dependent_requests = n_dependent_requests
            depth += 1

        bld_pkgs = sorted(build_packages, key=lambda x: x["depth"], reverse=True)
        pkg_set = []
        build_packages = []
        for bld in bld_pkgs:
            hit = False
            for ps in pkg_set:
                if bld["settings"] == ps:
                    hit = True
                    break
            if not hit:
                build_packages.append(bld)
                pkg_set.append(bld["settings"])
        return build_packages

    def LoadDefaultSetting(self) -> None:
        setting_file_path = os.path.join(self.rootdir, ".oslwright_setting.jsonc")
        if os.path.isfile(setting_file_path):
            data = LoadJson5(setting_file_path)
            settings = data["settings"]
            msvc_toolset_version_default = settings.get(
                "msvc_toolset_version_default", self.msvc_toolset_version_default
            )
            if msvc_toolset_version_default in self.msvc_toolset_versions:
                self.msvc_toolset_version_default = msvc_toolset_version_default

            self.msvc_runtime_library_default = settings.get(
                "msvc_runtime_library_default", self.msvc_runtime_library_default
            )
            self.build_arch_default = settings.get("build_arch_default", self.build_arch_default)
            self.build_library_default = settings.get("build_library_default", self.build_library_default)
            self.cuda_enable_default = settings.get("cuda_enable_default", self.cuda_enable_default)
            cuda_version_default = settings.get("cuda_version_default", self.cuda_version_default)
            if cuda_version_default in self.cuda_versions:
                self.cuda_version_default = cuda_version_default

    def SaveDefaultSetting(self) -> None:
        setting_file_path = os.path.join(self.rootdir, ".oslwright_setting.jsonc")
        data = {
            "settings": {
                "msvc_toolset_version_default": self.msvc_toolset_version_default,
                "msvc_runtime_library_default": self.msvc_runtime_library_default,
                "build_arch_default": self.build_arch_default,
                "build_library_default": self.build_library_default,
                "cuda_enable_default": self.cuda_enable_default,
                "cuda_version_default": self.cuda_version_default,
            }
        }
        SaveJson5(setting_file_path, data)

    def _getBuildToolsetVersions(self, installationPath: str) -> list[DictDotNotation]:
        content_path = os.path.join(installationPath, "VC", "Auxiliary", "Build")
        def_ver_path = os.path.join(content_path, "Microsoft.VCToolsVersion.default.txt")
        def_ver = ""
        with open(def_ver_path, "r") as f:
            def_ver = f.readline().replace("\n", "")
        vs_versions = []
        files = glob.glob(os.path.join(content_path, "Microsoft.VCToolsVersion.v*.default.txt"))
        for file in files:
            with open(file, "r") as f:
                toolset_version = f.readline().replace("\n", "")
                toolset = DictDotNotation()
                toolset.name = "vc" + toolset_version.replace(".", "")[:3]
                toolset.version = toolset_version
                toolset.default = False
                vs_versions.append(toolset)
        for item in vs_versions:
            if item.version == def_ver:
                item.default = True
                break
        vs_versions = natsorted(vs_versions, key=lambda x: x.version)
        return vs_versions

    def _getVisualStudioInofs(self) -> DictDotNotation | None:
        Post.Info("Checking for Visual Studio...")
        vs_where_exe = os.path.join(
            os.environ.get("ProgramFiles(x86)"), "Microsoft Visual Studio", "Installer", "vswhere.exe"
        )
        if not os.path.isfile(vs_where_exe):
            Post.Error("Visual Studio is not installed.")
            return None
        Post.Info("Found Visual Studio Installer.")
        shell = Shell()
        result = shell.exec(
            f'"{vs_where_exe}" -prerelease -nocolor -nologo -legacy -sort -format json -utf8', with_content=True
        )
        if result.exitcode:
            Post.Error("Cannot get information about Visual Studio.")
            return None
        elif not len(result.stdout):
            Post.Error("vswher not result.")
            return None
        vs_infos = []
        infos = jsonc.loads(result.stdout, object_hook=DictDotNotation)
        for info in infos:
            m = re.match(r"^(\d+)\..*$", info.catalog.buildVersion)
            version_short = m.group(1)
            version_year = info.catalog.productLineVersion
            msvc_generator = f"Visual Studio {version_short} {version_year}"

            cmake_exe = os.path.join(
                info.installationPath,
                "Common7",
                "IDE",
                "CommonExtensions",
                "Microsoft",
                "CMake",
                "CMake",
                "bin",
                "cmake.exe",
            )
            if not os.path.isfile(cmake_exe):
                cmake_exe = None

            ninja_exe = os.path.join(
                info.installationPath,
                "Common7",
                "IDE",
                "CommonExtensions",
                "Microsoft",
                "CMake",
                "Ninja",
                "ninja.exe",
            )
            if not os.path.isfile(ninja_exe):
                ninja_exe = None

            git_exe = os.path.join(
                info.installationPath,
                "Common7",
                "IDE",
                "CommonExtensions",
                "Microsoft",
                "TeamFoundation",
                "Team Explorer",
                "Git",
                "cmd",
                "git.exe",
            )
            if not os.path.isfile(git_exe):
                git_exe = None

            msvc_toolset_versions = self._getBuildToolsetVersions(info.installationPath)
            toolset_default = next(filter(lambda d: d.default, msvc_toolset_versions), None)

            msvc_versions = {}
            for item in msvc_toolset_versions:
                cl_exe = os.path.join(
                    info.installationPath, "VC", "Tools", "MSVC", item["version"], "bin", "HostX64", "x64", "cl.exe"
                )
                result = shell.exec(f'"{cl_exe}"', with_content=True)
                if result.exitcode:
                    Post.Error("Cannot get information about MSVC version.")
                    return None
                lines = io.StringIO(result.stdout).read().splitlines()
                m = re.match(r".*Version\s+(((\d+)\.\d+)(\.\d+)+).*", lines[0])
                msvc_version_full = m.group(1)
                msvc_version = m.group(2).replace(".", "")
                msvc_version_short = m.group(3)
                msvc_versions[item["name"]] = {}
                msvc_versions[item["name"]]["version_full"] = msvc_version_full
                msvc_versions[item["name"]]["version_short"] = msvc_version_short
                msvc_versions[item["name"]]["version"] = msvc_version

            vs_info = DictDotNotation()
            vs_info.displayname = info.displayName
            vs_info.description = info.description
            vs_info.installationpath = info.installationPath
            vs_info.installationVersion = info.installationVersion
            vs_info.generator = msvc_generator
            vs_info.msvc_toolset_versions = msvc_toolset_versions
            vs_info.msvc_toolset_version_default = toolset_default
            vs_info.msvc_versions = msvc_versions
            vs_info.extensions = DictDotNotation()
            vs_info.extensions.cmake = cmake_exe
            vs_info.extensions.git = git_exe
            vs_info.extensions.ninja = ninja_exe
            vs_infos.append(vs_info)
            Post.Info(f"Found {info.displayName}.")
        return vs_infos

    def GetMsvcEnvironment(
        self,
        build_arch: str | None = None,
        msvc_toolset_version: str | None = None,
        mscv_runtime_library: str | None = None,
    ) -> dict | None:
        if build_arch:
            arch = "x86" if build_arch == "x32" else "amd64"
        else:
            arch = "amd64"
        if msvc_toolset_version:
            vcver = msvc_toolset_version
        else:
            vcver = self.msvc_toolset_version_default

        key = (self.visual_studio_current.installationpath, arch, vcver)
        if key in self.msvc_environment_cache:
            return self.msvc_environment_cache[key]

        vs_environment = {}
        if not self.visual_studio_current:
            return vs_environment

        path = os.path.expandvars(SYSTEM_PATH)
        path_old = os.environ["PATH"]

        vcver_item = next(
            filter(lambda d: d.name == vcver, self.visual_studio_current.msvc_toolset_versions),
            None,
        )
        if vcver_item:
            vcvars_ver = vcver_item.version
        else:
            vcvars_ver = self.visual_studio_current.msvc_toolset_version_default.version

        try:
            # os.environ["PATH"] = path
            dev_cmd_bat = os.path.join(
                self.visual_studio_current.installationpath,
                "Common7",
                "Tools",
                "VsDevCmd.bat",
            )
            shell = Shell()
            result = shell.exec(
                f'cmd /c ""{dev_cmd_bat}" -arch={arch} -host_arch=amd64 -vcvars_ver={vcvars_ver} >nul && set"',
                with_content=True,
            )
            if result.exitcode:
                Post.Error("Cannot get information about MSVC")
                return None
            if not len(result.stdout):
                Post.Error("devcmd.bat not result")
                return None

            lines = io.StringIO(result.stdout).read().splitlines()
            for line in lines:
                k, v = line.split("=", 1)
                vs_environment[k] = v

        except:
            Post.Error("Exception devcmd ")
        finally:
            os.environ["PATH"] = path_old

        self.msvc_environment_cache[key] = vs_environment
        return vs_environment

    def GetToolsPaths(self) -> str | None:
        path = str()
        if self.git_exe:
            path = ";".join([path, os.path.dirname(self.git_exe)])

        if self.gitlfs_exe:
            path = ";".join([path, os.path.dirname(self.gitlfs_exe)])

        if self.cmake_exe:
            path = ";".join([path, os.path.dirname(self.cmake_exe)])

        if self.ninja_exe:
            path = ";".join([path, os.path.dirname(self.ninja_exe)])

        if self.sevenzip_exe:
            path = ";".join([path, os.path.dirname(self.sevenzip_exe)])

        if self.nasm_exe:
            path = ";".join([path, os.path.dirname(self.nasm_exe)])

        if self.pkg_config_exe:
            path = ";".join([path, os.path.dirname(self.pkg_config_exe)])

        if self.perl_exe:
            path = ";".join([path, os.path.dirname(self.perl_exe)])
            path = ";".join(
                [
                    path,
                    os.path.join(os.path.dirname(self.perl_exe), "..", "site", "bin"),
                ]
            )

        if self.gn_exe:
            path = ";".join([path, os.path.dirname(self.gn_exe)])

        if self.python_exe:
            path = ";".join([path, os.path.dirname(self.python_exe)])
            path = ";".join([path, os.path.join(os.path.dirname(self.python_exe), "Scrits")])

        if self.py_exe:
            path = ";".join([path, os.path.dirname(self.py_exe)])

        if self.meson_exe:
            path = ";".join([path, os.path.dirname(self.meson_exe)])

        if self.jinja2_exe:
            path = ";".join([path, os.path.dirname(self.jinja2_exe)])

        if self.msys2_exe:
            path = ";".join([path, os.path.dirname(self.msys2_exe)])

        if self.bison_flex_exe:
            path = ";".join([path, os.path.dirname(self.bison_flex_exe)])

        return path[1:]

    def _getCudaRoot(self):
        cuda_root = os.path.join(os.environ.get("ProgramFiles"), "NVIDIA GPU Computing Toolkit", "CUDA")
        if not os.path.isdir(cuda_root):
            return None
        Post.Info("CUDA Found.")
        return cuda_root

    def _getCudaVersions(self):
        versions = []
        vers = [os.path.basename(p.rstrip(os.sep))[1:] for p in glob.glob("v*", root_dir=self.cuda_root)]
        return natsorted(vers)

    def _getCudaPath(self, version: str) -> str | None:
        cuda_path = os.path.join(self.cuda_root, f"v{version}")
        if not os.path.isdir(cuda_path):
            return None
        return cuda_path

    def _findGit(self) -> str | None:
        git_exe = None
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows")
            (instpath, _) = winreg.QueryValueEx(key, "InstallPath")
            git_exe = os.path.join(instpath, "bin", "git.exe")
            return git_exe
        except:
            pass
        git_exe = os.path.join(os.environ.get("LocalAppData"), "Programs", "Git", "bin", "git.exe")
        if os.path.isfile(git_exe):
            return git_exe

        git_exe = os.path.join(os.environ.get("ProgramFiles"), "Git", "bin", "git.exe")
        if os.path.isfile(git_exe):
            return git_exe

        git_exe = shutil.which("git.exe")
        if git_exe and os.path.isfile(git_exe):
            return git_exe

        git_exe = None
        # if self.visual_studio_current:
        #     git_exe = self.visual_studio_current.extensions.git

        return git_exe

    def _findGitLFS(self) -> str | None:
        gitlfs_exe = os.path.join(os.environ.get("ProgramFiles"), "Git LFS", "git-lfs.exe")
        if os.path.isfile(gitlfs_exe):
            return gitlfs_exe

        gitlfs_exe = shutil.which("git-lfs.exe")
        if gitlfs_exe and os.path.isfile(gitlfs_exe):
            return gitlfs_exe
        return None

    def _findCMake(self) -> str | None:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Kitware\CMake")
            (instpath, _) = winreg.QueryValueEx(key, "InstallDir")
            cmake_exe = os.path.join(instpath, "bin", "cmake.exe")
            return cmake_exe
        except:
            pass

        cmake_exe = os.path.join(os.environ.get("ProgramFiles"), "CMake", "bin", "cmake.exe")
        if os.path.isfile(cmake_exe):
            return cmake_exe

        cmake_exe = shutil.which("cmake.exe")
        if cmake_exe and os.path.isfile(cmake_exe):
            return cmake_exe

        cmake_exe = None
        if self.visual_studio_current:
            cmake_exe = self.visual_studio_current.extensions.cmake

        return cmake_exe

    def _findNinja(self) -> str | None:

        ninja_exe = os.path.join(self.rootdir, ".venv", "Scripts", "ninja.exe")
        if os.path.isfile(ninja_exe):
            return ninja_exe

        ninja_exe = shutil.which("ninja.exe")
        if ninja_exe and os.path.isfile(ninja_exe):
            return ninja_exe

        ninja_exe = None
        if self.visual_studio_current:
            ninja_exe = self.visual_studio_current.extensions.ninja_exe

        return ninja_exe

    def _findNasm(self) -> str | None:
        nasm_exe = os.path.join(os.environ.get("LocalAppData"), "bin", "NASM", "nasm.exe")
        if os.path.isfile(nasm_exe):
            return nasm_exe

        nasm_exe = os.path.join(os.environ.get("ProgramFiles"), "NASM", "nasm.exe")
        if os.path.isfile(nasm_exe):
            return nasm_exe

        nasm_exe = os.path.join(self.tools_rootdir, "nasm", "bin", "nasm.exe")
        if os.path.isfile(nasm_exe):
            return nasm_exe

        nasm_exe = shutil.which("nasm.exe")
        return nasm_exe

    def _findPerl(self) -> str | None:
        perl_exe = None
        perl_exe = os.path.join(self.tools_rootdir, "perl", "perl", "bin", "perl.exe")
        if os.path.isfile(perl_exe):
            return perl_exe

        perl_exe = os.path.join("C:", os.sep, "Strawberry", "perl", "bin", "perl.exe")
        if os.path.isfile(perl_exe):
            return perl_exe

        perl_exe = shutil.which("perl.exe")
        return perl_exe

    def _findPython(self) -> str | None:
        python_exe = os.path.join(self.rootdir, ".venv", "Scripts", "python.exe")
        if os.path.isfile(python_exe):
            return python_exe

        python_root = os.path.join(os.environ.get("LocalAppData"), "Programs", "Python")
        if os.path.isfile(python_root):
            vers = glob.glob("*", root_dir=python_root)
            vers = natsorted(vers)
            python_exe = os.path.join(python_root, vers[0], "python.exe")
            if os.path.isfile(python_exe):
                return python_exe

        python_root = os.path.join(os.environ.get("ProgramFiles"), "Python")
        if os.path.isfile(python_root):
            vers = glob.glob("*", root_dir=python_root)
            vers = natsorted(vers)
            python_exe = os.path.join(python_root, vers[0], "python.exe")
            if os.path.isfile(python_exe):
                return python_exe

        python_root = os.path.join(os.environ.get("ProgramFiles(x86)"), "Python")
        if os.path.isfile(python_root):
            vers = glob.glob("*", root_dir=python_root)
            vers = natsorted(vers)
            python_exe = os.path.join(python_root, vers[0], "python.exe")
            if os.path.isfile(python_exe):
                return python_exe

        python_exe = shutil.which("python.exe")
        return python_exe

    def _findPythonLauncher(self) -> str | None:
        py_exe = os.path.join(os.environ.get("LocalAppData"), "Programs", "Python", "Launcher", "py.exe")
        if os.path.isfile(py_exe):
            return py_exe

        py_exe = shutil.which("py.exe")
        return py_exe

    def _findPkgConfig(self) -> str | None:
        pkgcnf_exe = os.path.join("C:", os.sep, "pkg-config", "bin", "pkg-config.exe")
        if os.path.isfile(pkgcnf_exe):
            return pkgcnf_exe

        pkgcnf_exe = os.path.join(self.tools_rootdir, "pkg-config", "bin", "pkg-config.exe")
        if os.path.isfile(pkgcnf_exe):
            return pkgcnf_exe

        pkgcnf_exe = shutil.which("pkg-config.exe")
        return pkgcnf_exe

    def _findGN(self) -> str | None:
        gn_exe = os.path.join(self.tools_rootdir, "gn", "gn.exe")
        if os.path.isfile(gn_exe):
            return gn_exe
        gn_exe = shutil.which("gn.exe")

    def _findMeson(self) -> str | None:
        meson_exe = os.path.join(self.rootdir, ".venv", "Scripts", "meson.exe")
        if os.path.isfile(meson_exe):
            return meson_exe

        meson_exe = shutil.which("meson.exe")
        return meson_exe

    def _findJinja2(self) -> str | None:
        jinja2_exe = os.path.join(self.rootdir, ".venv", "Scripts", "jinja2.exe")
        if os.path.isfile(jinja2_exe):
            return jinja2_exe

        jinja2_exe = shutil.which("jinja2.exe")
        return jinja2_exe

    def _find7zip(self) -> str | None:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\7-Zip")
            (instpath, _) = winreg.QueryValueEx(key, "Path64")
            svnzip_exe = os.path.join(instpath, "7z.exe")
            return svnzip_exe
        except:
            pass

        svnzip_exe = os.path.join(os.environ.get("ProgramFiles"), "7-zip", "7z.exe")
        if os.path.isfile(svnzip_exe):
            return svnzip_exe

        svnzip_exe = shutil.which("7z.exe")
        return svnzip_exe

    def _findMsys2(self) -> str | None:
        msys2_exe = os.path.join(self.tools_rootdir, "msys2", "msys64", "msys2_shell.cmd")
        if os.path.isfile(msys2_exe):
            return msys2_exe
        msys2_exe = shutil.which("msys2_shell.cmd")
        return msys2_exe

    def _findBisonFlex(self) -> str | None:
        bison_flex_exe = os.path.join(self.tools_rootdir, "winflexbison", "winflexbison", "bison.exe")
        if os.path.isfile(bison_flex_exe):
            return bison_flex_exe
        bison_flex_exe = shutil.which("bison.exe")
        return bison_flex_exe

    def _updateToolPath(self) -> None:
        Post.Info("Checking for tools...")
        self.git_exe = self._findGit()
        if self.git_exe:
            Post.Info("Found GIT.")
        self.gitlfs_exe = self._findGitLFS()
        if self.gitlfs_exe:
            Post.Info("Found GIT LFS.")
        self.cmake_exe = self._findCMake()
        if self.cmake_exe:
            Post.Info("Found CMake.")
        self.ninja_exe = self._findNinja()
        if self.ninja_exe:
            Post.Info("Found Ninja.")
        self.sevenzip_exe = self._find7zip()
        if self.sevenzip_exe:
            Post.Info("Found 7z.")
        self.nasm_exe = self._findNasm()
        if self.nasm_exe:
            Post.Info("Found NASM.")
        self.perl_exe = self._findPerl()
        if self.perl_exe:
            Post.Info("Found Perl.")
        self.pkg_config_exe = self._findPkgConfig()
        if self.pkg_config_exe:
            Post.Info("Found pkg-config.")
        self.gn_exe = self._findGN()
        if self.gn_exe:
            Post.Info("Found gn")
        self.python_exe = self._findPython()
        if self.python_exe:
            Post.Info("Found Python.")
        self.py_exe = self._findPythonLauncher()
        if self.py_exe:
            Post.Info("Found Python Launcher.")
        self.meson_exe = self._findMeson()
        if self.meson_exe:
            Post.Info("Found Meson.")
        self.jinja2_exe = self._findJinja2()
        if self.jinja2_exe:
            Post.Info("Found Jinja2.")
        self.msys2_exe = self._findMsys2()
        if self.msys2_exe:
            Post.Info("Found MYSYS2.")
        self.bison_flex_exe = self._findBisonFlex()
        if self.bison_flex_exe:
            Post.Info("Found Bison Flex.")
