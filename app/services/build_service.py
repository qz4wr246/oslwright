import os
import sys
from datetime import datetime
from pathlib import Path
import glob
import regex
from typing import Any, Dict, List, Optional, Set
import copy
from graphlib import TopologicalSorter, CycleError

from fletx import FletX
from fletx.core import FletXService
from fletx.utils import run_async

from .platform_service import PlatformService
from .package_service import PackageService
from ..models.package_model import PackageModel
from ..models.package_option_model import PackageOptionModel, PackageOptionStageItem
from ..models.build_model import BuildModel, Reason
from ..models.node_model import NodeModel
from ..core.shell import SYSTEM_PATH
from ..core.common import Version, uniq_path_env, add_path_env, seconds_to_hms
from ..core.constants import STAGES_ORDER
from ..core.merge_dict import MergeDict
from ..core.logger import PostLogger as Post
from ..core.evaluate import evaluate_str, expand_envs_vars
from ..core.logger import PostLogger as Post
from ..core.shell import PipedShell
from ..core.exception import PackageValidationError

DONT_REGIST_KEYS = [
    "options",
    "dependencies",
    "environments",
    "scripts",
    "name",
    "when",
    "chdir",
    "message",
    "script",
    "fallback",
]


class BuildService(FletXService):
    def __init__(self, *args, **kwargs):
        # print("BuildService:__init__")
        self.platform_service: PlatformService = FletX.find(PlatformService)  # type: ignore[arg-type]
        self.package_service: PackageService = FletX.find(PackageService)  # type: ignore[arg-type]
        self.shell = PipedShell()
        self.model = None
        self.is_killed = False
        super().__init__(name="BuildService", auto_start=True, **kwargs)

    def on_start(self):
        """Do stuf here on BuildService start"""
        # print("BuildService:on_start")

    def on_stop(self):
        """Do stuf here on BuildService stop"""
        # print("BuildService:on_stop")

    def run_build(self, packages: List[PackageModel], model: BuildModel):
        self.is_killed = False
        run_async(lambda: self.build_task(packages, model))

    async def build_task(self, packages: List[PackageModel], model: BuildModel):
        try:
            Post.gui(f"\n======= Build start: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')} ==========")
            self.model = model
            model.is_running = True
            deps = self.find_dependent_builds(packages)
            model.package_num = len(deps)
            process_time = 0
            for pkg, opt in deps:
                if opt.versions[opt.current_version].completed:
                    process_time += 5
                else:
                    process_time += int(pkg.process_time)
            model.total_process_time = process_time
            result = Reason.COMPLETED
            model.processed_count = 0
            for pkg, opt in deps:
                result = self.build_package(pkg, opt, model)
                if result != Reason.COMPLETED:
                    break
                model.processed_count += 1
            if result == Reason.COMPLETED:
                Post.gui(f"Build Completed.")
        except Exception as e:
            Post.error(str(e))
            model.reason = Reason.EXCEPTION
        finally:
            model.is_running = False
            self.model = None
            Post.gui(f"======= Build end:  {datetime.now().strftime('%Y/%m/%d %H:%M:%S')} ==========")

    def get_environment(self, session: dict):
        environs = {}
        os.environ["CUDA_PATH"] = ""
        os.environ["CUDNN_PATH"] = ""

        environs["CUDA_PATH"] = ""
        environs["CUDNN_PATH"] = ""
        environs["DOTNET_CLI_UI_LANGUAGE"] = "en"
        environs["VSLANG"] = "1033"
        environs["PYTHONUNBUFFERED"] = "1"
        environs["PYTHONUTF8"] = "1"
        environs["PYTHONIOENCODING"] = "utf-8"
        environs["LC_ALL"] = "C"
        environs["LANG"] = "ja_JP.UTF-8"
        environs["GIT_REDIRECT_STDERR"] = "2>&1"

        # MSVC実行環境の環境変数を取得
        mscv_version = session.get("msvc_version", None)
        build_arch = session.get("build_arch", None)
        msvc_toolset_version = session.get("msvc_toolset_version", None)
        envs = self.platform_service.GetMsvcEnvironment(
            build_arch=build_arch, mscv_version=mscv_version, msvc_toolset_version=msvc_toolset_version
        )
        if envs:
            for k, v in envs.items():
                environs[k] = os.path.expandvars(v)

        # PATHから悪影響のあるパスを取り除く
        malwords = ["mingw", "python", "pyenv"]
        path_list = environs["PATH"].split(";")
        filtered_list = [p for p in path_list if p.strip() and not any(word.lower() in p.lower() for word in malwords)]

        environs["PATH"] = ";".join(filtered_list)

        # Windows標準PATH
        path = os.path.expandvars(SYSTEM_PATH)

        # スクリプトを実行したpythonをPATHへ追加
        if sys.executable:
            python_dir = str(Path(sys.executable).resolve().parent)
            path = add_path_env(path, python_dir)

        if "PATH" in environs:
            path = ";".join([environs["PATH"], path])
        toolpaths = self.platform_service.GetToolsPaths()
        if toolpaths:
            path = ";".join([path, toolpaths])

        # 重複を削除
        environs["PATH"] = uniq_path_env(path)

        return environs

    def create_session(self, package: PackageModel, option: PackageOptionModel):
        session = self.platform_service.create_session_base(
            package, option.versions[option.current_version].options.get("msvc_version", None)
        )
        session["version"] = option.current_version
        # option 変数を変数に
        for k, v in option.versions[option.current_version].options.items():
            session[k] = v
        return session

    def build_package(self, package: PackageModel, option: PackageOptionModel, model: BuildModel):
        start_time = datetime.now()
        model.package_name = package.display
        model.stage_name = "---"

        if model.build_force_packages and package.name in model.build_force_packages:
            Post.gui(f"[{package.display}] force build")
            self.package_service.revert_option(option, "download")

        if option.versions[option.current_version].completed:
            Post.gui(f"[{package.display}] skip")
            result = Reason.COMPLETED
        else:
            session = self.create_session(package, option)
            default = package.versions["default"]
            current = MergeDict(default, package.versions[option.current_version])
            dist_paths = self.get_package_depedency_paths(package, option)
            self.update_dependency_path(dist_paths, session)
            sys_env = self.get_environment(session)

            current = self.transform(current, session, sys_env)
            if isinstance(current, dict):
                stages = current["stages"]
            else:
                raise Exception("Syntax Error : undefined stages in package.jsonc")

            def_envs = current.get("environments", None)
            if def_envs:
                for k, v in def_envs.items():
                    def_envs[k] = evaluate_str(v, session) if isinstance(v, str) else v
                for k, v in def_envs.items():
                    def_envs[k] = expand_envs_vars(v, sys_env)
                sys_env |= def_envs

            # stages をorder の順に辞書を再構成する。
            stages = {k: stages[k] for k in STAGES_ORDER if k in stages}

            result = Reason.NORMAL
            Post.gui(f"[{package.display}] build for {session.get("dist_name","")}")
            Post.gui(f"[{package.display}] process time: {seconds_to_hms(int(package.process_time))}")
            Post.gui(f"[{package.display}] execute statges.....")
            for stage, body in stages.items():
                if not self.isfinished(stage, option):
                    model.stage_name = stage
                    Post.gui(f"[{package.display}] '{stage}' stage ...")
                    result = self.execute_stage(body, session, sys_env)
                    if result == Reason.COMPLETED:
                        self.update_stage(stage, option)
                        self.package_service.save_option(option)
                    else:
                        break
                else:
                    Post.gui(f"[{package.display}] skip '{stage}' stage")
            if result == Reason.COMPLETED:
                model.stage_name = "completed"
                option.versions[option.current_version].completed = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                self.package_service.save_option(option)

            exec_time = datetime.now() - start_time
            Post.gui(f"[{package.display}] execute time: {round(exec_time.total_seconds() + 0.5)} sec")
            Post.gui("")
            model.total_process_time -= int(package.process_time) - round(exec_time.total_seconds() + 0.5)
        if result == Reason.NORMAL:
            result = Reason.COMPLETED
        model.reason = result
        return result

    def isfinished(self, stage: str, option: PackageOptionModel):
        stages = option.versions[option.current_version].stages
        if stages:
            exists = any(st.stage == stage for st in stages)
            return exists
        return False

    def update_stage(self, stage: str, option: PackageOptionModel):
        stages = option.versions[option.current_version].stages
        if not stages:
            stages = []
        stages.append(PackageOptionStageItem(stage, datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
        option.versions[option.current_version].stages = stages

    def execute_stage(self, stage: dict, session: dict, environs: dict):
        environments = stage.get("environments", None)
        if environments:
            for k, v in environments.items():
                environments[k] = evaluate_str(v, session) if isinstance(v, str) else v
            for k, v in environments.items():
                environments[k] = expand_envs_vars(v, environs)
            environs |= environments

        ret = Reason.COMPLETED
        for script in stage["scripts"]:
            ret = self.execute_script(script, session, environs)
            if ret != Reason.COMPLETED:
                break
            if self.is_killed:
                ret = Reason.USER_INTERRUPTED
                break
        return ret

    def execute_script(self, script: dict, session: dict, base_environs: dict) -> Reason:
        session = copy.deepcopy(session)
        message = script.get("message", None)
        when = script.get("when", True)
        chdir = script.get("chdir", None)
        code = script.get("script", None)
        fallback = script.get("fallback", None)
        environments = script.get("environments", None)
        ignore_errors = script.get("ignore_errors", False)

        envs = copy.deepcopy(base_environs)
        if environments:
            for k, v in environments.items():
                environments[k] = evaluate_str(v, session) if isinstance(v, str) else v
            for k, v in environments.items():
                environments[k] = expand_envs_vars(v, base_environs)
            envs |= environments
        envs["ERRORLEVEL"] = "0"

        for k, v in script.items():
            if k in ["message", "when", "chdir", "script", "fallback", "environments", "ignore_errors"]:
                continue
            s = self.transform(v, session, envs)
            session[k] = s

        when = evaluate_str(when, session) if isinstance(when, str) else when
        chdir = evaluate_str(chdir, session) if isinstance(chdir, str) else chdir
        if when and chdir:
            os.chdir(chdir)
        message = evaluate_str(message, session) if isinstance(message, str) else message
        code = evaluate_str(code, session) if isinstance(code, str) else code
        fallback = evaluate_str(fallback, session) if isinstance(fallback, str) else fallback

        if when:
            if message:
                Post.gui(f"[{session.get('display', 'Unknown')}] {message}")
            if chdir:
                Post.gui(f"cd {chdir}")
            if code:
                Post.gui(code)
                result = self.shell.exec(code, env=envs, shell=True)
                if isinstance(ignore_errors, str):
                    envs["ERRORLEVEL"] = str(result.exitcode)
                    ignore_errors = expand_envs_vars(ignore_errors, envs)
                    ignore_errors = evaluate_str(ignore_errors, session)
                if result.killed:
                    Post.error(f"[{session.get('display', 'Unknown')}] ! User Interrupted !")
                    return Reason.USER_INTERRUPTED
                elif result.exitcode and fallback:
                    Post.error(
                        f"[{session.get('display', 'Unknown')}] ExitCode={result.exitcode}, Fallback: {fallback}"
                    )
                    self.shell.exec(fallback, env=envs, shell=True)
                    return Reason.ERROR
                elif result.exitcode and not ignore_errors:
                    Post.error(
                        f"[{session.get('display', 'Unknown')}] ExitCode={result.exitcode}, Check Output.log for details."
                    )
                    return Reason.ERROR
                elif result.exitcode and ignore_errors:
                    Post.info(f"[{session.get('display', 'Unknown')}] Ignore errors and continue.")
        return Reason.COMPLETED

    def update_dependency_path(self, depdentpath, session):
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
            dlst = []
            for dir in depdentpath["release"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.lib", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["dependent_libs_release"] = ";".join(set(dlst))
        else:
            session["dependent_packages_release"] = ""
            session["pkg_config_path_release"] = ""
            session["dependent_dlls_release"] = ""
            session["dependent_libs_release"] = ""

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
            for dir in depdentpath["debug"].split(";"):
                for f in glob.glob(f"{dir}\\**\\*.lib", recursive=True):
                    dlst.append(os.path.dirname(f))
            session["dependent_libs_debug"] = ";".join(set(dlst))
        else:
            session["dependent_packages_debug"] = ""
            session["pkg_config_path_debug"] = ""
            session["dependent_dlls_debug"] = ""
            session["dependent_libs_debug"] = ""

    def transform(self, node, session: dict, envs: dict | None = None, regist_vars: bool = True):
        """node を再帰的に探索し、str ノードを evaluate_str で置換する"""

        # 文字列なら変換して返す
        if isinstance(node, str):
            if envs:
                node = expand_envs_vars(node, envs)
            return evaluate_str(node, session)

        # dict の場合は、値を再帰的に処理
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "environments":
                    continue
                if k == "scripts":  #  execute_script() で再評価する
                    continue
                nregist = regist_vars
                if k in DONT_REGIST_KEYS:
                    nregist = False
                n = self.transform(v, session, envs, nregist)
                node[k] = n
                if nregist:
                    session[k] = n
            return node

        # list / tuple などのシーケンスも再帰的に処理
        if isinstance(node, list):
            return [self.transform(x, session, envs) for x in node]
        if isinstance(node, tuple):
            return tuple(self.transform(x, session, envs) for x in node)

        # それ以外の型はそのまま返す
        return node

    def get_package_depedency_paths(self, package: PackageModel, option: PackageOptionModel) -> dict:
        result = {}
        distdir_debug = []
        distdir_release = []
        deps = self.get_package_dependencies(package, option)
        deps = self.get_unique_sorted_nodes(deps)
        # deps には、親がふくまれるので削除
        deps = [t for t in deps if t.package.name != package.name]

        for node in deps:
            pkg = node.package
            opt = node.option
            dirs = self.get_distination_dirs(pkg, opt)
            if "debug" in dirs and dirs["debug"]:
                distdir_debug.append(dirs["debug"])
            if "release" in dirs and dirs["release"]:
                distdir_release.append(dirs["release"])
        if distdir_debug:
            result["debug"] = ";".join(distdir_debug)
        if distdir_release:
            result["release"] = ";".join(distdir_release)
        return result

    def get_distination_dirs(self, package: PackageModel, option: PackageOptionModel) -> dict:
        session = self.create_session(package, option)
        default = package.versions["default"]
        current = MergeDict(default, package.versions[option.current_version])
        session = self.create_session(package, option)
        current = self.transform(current, session)
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

    def find_dependent_builds(self, packages: List[PackageModel]):
        """ """
        dependencies = []
        for package in packages:
            option = self.package_service.load_option(package)
            deps = self.get_package_dependencies(package, option)
            dependencies.extend(deps)

        sorted_nodes = self.get_unique_sorted_nodes(dependencies)
        result = [(n.package, n.option) for n in sorted_nodes]
        return result

    def unique_nodes(self, node_list):
        """
        (package, option)のノードを親子関係を保ったままユニークにする
        同一キーの親ありを親なしより優先する
        """
        # key: option.get_hash(), value: list[NodeModel]
        unique_map = {}

        for node in node_list:
            oid = node.option.get_hash()
            parent_hash = node.parent.option.get_hash() if node.parent is not None else None

            # 初登場 → 新しいリストを作って追加
            if oid not in unique_map:
                unique_map[oid] = [node]
                continue

            existing_list = unique_map[oid]
            existing = existing_list[0]  # 代表（最初の要素）

            # 既存が親なし、今回が親あり → 代表を差し替え
            if existing.parent is None and node.parent is not None:
                unique_map[oid][0] = node
                continue

            # 既存が親あり、今回も親あり
            if existing.parent is not None and node.parent is not None:
                # すでに同じ親ハッシュを持つノードがあるか確認
                same_parent_exists = any(
                    n.parent is not None and n.parent.option.get_hash() == parent_hash for n in existing_list
                )
                # 親が同じなら追加しない／違う親なら追加
                if not same_parent_exists:
                    unique_map[oid].append(node)
                continue

            # それ以外（既存が親あり、今回が親なしなど）は何もしない

        # すべてのリストを平坦化して返す
        result = []
        for nodes in unique_map.values():
            result.extend(nodes)
        return result

    def build_graph_of_deps(self, nodes):
        """
        ノードをTopologicalSorterの入力へ加工
        """
        deps = {}
        for node in nodes:
            cid = node.option.get_hash()
            if node.parent:
                # 　親あり
                pid = node.parent.option.get_hash()
                if cid not in deps:
                    # 初回
                    deps[cid] = {pid}
                else:
                    # 既存あり
                    deps[cid].add(pid)
            else:
                # 親無し
                deps[cid] = set()
        return deps

    def get_unique_sorted_nodes(self, dependencies: List[NodeModel]) -> List[NodeModel]:
        """
        トポロジカルソートを用いてノードを依存関係の順番(ビルド順)にソートする
        """
        # 1. 親あり優先でユニーク化
        unique_nodes = self.unique_nodes(dependencies)

        # 2. 依存辞書を作る(ノード→ID)
        deps = self.build_graph_of_deps(unique_nodes)
        sorted_ids = []
        try:
            # 3. トポロジカルソート
            ts = TopologicalSorter(deps)
            sorted_ids = list(ts.static_order())
        except CycleError as e:
            raise e
        # 4. ID → NodeModel の逆引き
        id_to_node = {n.option.get_hash(): n for n in unique_nodes}
        sorted_nodes = [id_to_node[i] for i in sorted_ids]

        # 親→子→順を子が先に
        sorted_nodes.reverse()
        return sorted_nodes

    def get_package_dependencies(self, package: "PackageModel", option: PackageOptionModel) -> List[NodeModel]:
        """
        依存関係リストを取得。巡回参照（無限ループ）は例外を発生させる。
        """
        return self.get_package_dependencies_recursive(
            package, option, parent=None, visited=set(), stack=set(), result=[]
        )

    def get_package_dependencies_recursive(
        self,
        package: "PackageModel",
        option: PackageOptionModel,
        parent: Optional[NodeModel] = None,
        visited: Optional[Set[int]] = None,
        stack: Optional[Set[int]] = None,
        result: Optional[List[NodeModel]] = None,
    ) -> List[NodeModel]:
        """
        再帰的に(package,option)ノードの依存関係の子ノードを取得
        """
        if visited is None:
            visited = set()
        if stack is None:
            stack = set()
        if result is None:
            result = []

        # オプションのハッシュ値を一意な識別子として使用
        node_key = option.get_hash()

        # --- 巡回参照 (無限ループ) 判定 ---
        # 現在探索中の経路（stack）に同じハッシュが存在すれば例外
        if node_key in stack:
            raise Exception(
                f"Circular dependency detected for option:{parent.option.name if parent else 'None'}->{option.name}"
            )

        # ノードを作成して結果リストに追加（重複を許容するため毎回追加）
        node = NodeModel(package=package, option=option, parent=parent)
        result.append(node)

        # --- 重複 (DUPLICATE) 判定 ---
        # すでに他の経路で探索済みの場合は、このノード自体の追加は行うが、子への探索はスキップ
        if node_key in visited:
            return result

        # 状態の更新
        stack.add(node_key)
        visited.add(node_key)

        # 子ノード（依存先）の探索
        parent_option = parent.option if parent else None
        cond_reqs = self.get_cond_of_requests(package, option, parent_option)

        for name, cond in cond_reqs.items():
            try:
                child_pkg = self.package_service.find_package(name)
                child_opt = self.find_option_by_request(name, cond)
            except PackageValidationError as e:
                raise Exception(f"Error in dependency of '{package.name}': {str(e)}")

            if child_pkg and child_opt:
                self.get_package_dependencies_recursive(
                    child_pkg, child_opt, parent=node, visited=visited, stack=stack, result=result
                )

        # 探索終了：現在のパスから抜ける
        stack.remove(node_key)

        return result

    def get_cond_of_requests(
        self, package: PackageModel, option: PackageOptionModel, parent: PackageOptionModel | None = None
    ):
        """
        パッケージの依存関係を取得する(enableのみ)
        """
        options = option.versions[option.current_version].options

        session = self.platform_service.create_session_base(package, options.get("msvc_version", None))
        session |= options

        default = package.versions["default"]
        current = package.versions[option.current_version]
        merged = MergeDict(default, current)
        deps = merged.get("dependencies", {})

        requests = {}

        for name, cond in deps.items():
            cond_c = {}
            version = None
            if isinstance(cond, dict):
                for k, v in cond.items():
                    if isinstance(v, str):
                        cond_c[k] = evaluate_str(v, session)
                    else:
                        cond_c[k] = v
            elif isinstance(cond, str):
                cond_c["version"] = evaluate_str(cond, session)
            else:
                raise PackageValidationError("構文エラー")

            if "enable" in cond_c:
                if not cond_c["enable"]:
                    continue

            if options.get("build_library", "") == "interface":
                for k, v in options.items():
                    if k in ["version", "build_library", "build_type", "build_layout"]:
                        continue
                    if k not in cond_c:
                        v = None if isinstance(v, str) and not v else v
                        v = (
                            parent.versions[parent.current_version].options.get(k, None)
                            if v is None and parent
                            else None
                        )
                        if v:
                            cond_c[k] = v
            else:
                for k, v in options.items():
                    if k in ["version", "build_library", "build_type", "build_layout"]:
                        continue
                    if k not in cond_c:
                        v = None if isinstance(v, str) and not v else v
                        if v:
                            cond_c[k] = v

            requests[name] = cond_c

        return requests

    def find_option_by_request(self, name: str, cond: Dict[str, Any]) -> PackageOptionModel:
        """
        条件(cond)に該当する、パッケージ(name)のオプションを検索する
        """
        package = self.package_service.find_package(name)
        if not package:
            raise PackageValidationError(f"Undefined package referenced: {name}")

        versions = self.package_service.get_versions(package)
        version = versions[-1]
        if isinstance(cond, dict) and "version" in cond:
            version = self._find_request_version(versions, cond["version"])
        if not version:
            raise PackageValidationError(f"Unavailable version requested for '{name}': {cond.get('version')}")
        option = self.package_service.load_option(package)
        if version not in option.versions:
            Post.warning(f"Unavailable version '{version}' for '{name}' package option. Falling back to defaults.")
            option = self.package_service.create_default_option(package)

        msvc_version = cond.get(
            "msvc_version", option.versions[option.current_version].options.get("msvc_version", None)
        )
        option_ui = self.get_eval_option_ui(package, msvc_version)
        overwrite = False
        if isinstance(cond, dict):
            for k, v in cond.items():
                if k not in option.versions[version].options:
                    continue
                if not v:
                    continue
                if k in ["version", "enable"]:
                    continue
                ui = next((o for o in option_ui.options if o.name == k), None)
                if not ui or not ui.enable:
                    continue
                if option.versions[version].options.get(k, None) != v:
                    if ui.type == "choice":
                        if v in ui.items:  # type: ignore
                            option.versions[version].options[k] = v
                            overwrite = True
                        else:
                            raise PackageValidationError("未定義なオプションを要求しています。")
                    elif isinstance(option.versions[version].options[k], type(v)):
                        option.versions[version].options[k] = v
                        overwrite = True
                    else:
                        raise PackageValidationError("未定義なオプションを要求しています。")
        option.current_version = version
        if overwrite:
            self.package_service.revert_option(option)
        return option

    def get_eval_option_ui(self, package: PackageModel, msvc_version: str | None = None):
        option_ui = self.package_service.load_option_ui(package)
        session = self.platform_service.create_session_base(package, msvc_version)

        for ui in option_ui.options:
            if ui.enable and isinstance(ui.enable, str):
                ui.enable = evaluate_str(ui.enable, session)
            if ui.items and isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)
            if ui.default and isinstance(ui.default, str):
                ui.default = evaluate_str(ui.default, session)
            session[ui.name] = ui.default
        return option_ui

    def _find_request_version(self, versions: List[str], req_ver: str | None = None) -> str | None:
        reg = r"\s*([><=]=?)?\s*([^\s,;]+)(\s*[,;]+\s*([><]=?)([\w.-]+))?"

        if not len(versions):
            return None

        if not req_ver:
            return versions[-1]

        m = regex.match(reg, req_ver)
        ope1 = m.group(1)
        ver1 = m.group(2)
        ope2 = m.group(4)
        ver2 = m.group(5)

        if not ver1:
            # "Bad dependenct version in package.jsonc"
            return None

        versions = versions
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

        return versions[-1] if len(versions) else None

    def stop_build(self):
        """ビルド停止"""
        self.is_killed = True
        self.shell.kill()
        if self.model:
            self.model.is_running = False
            self.model.reason = Reason.USER_INTERRUPTED
