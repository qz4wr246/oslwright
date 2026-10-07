"""
Oslwright Application
"""

import os
import subprocess
import asyncio
import flet as ft

# サービス管理関数のインポート
from app.core.constants import Routes

# from app.core.context import AppContext
from app.core.theme import dark_theme, light_theme
from app.services import initialize_all_services_sync, get_service
from app.services.platform_service import PlatformService, PlatformReason, ReasonCode
from app.services.package_service import PackageService


@ft.component
def SplashScreen(status_text: str, platform_init_reason: PlatformReason, on_dialog_ok):
    """スプラッシュ画面のコンポーネント"""
    page = ft.context.page

    show_missing_vs, set_show_missing_vs = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                    ft.Text("Alert"),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text("Please Install Visual Studio.\n and restart this application."),
            actions=[
                ft.TextButton("Exit", on_click=lambda: page.run_task(on_dialog_ok, action="close")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_missing_vs
        else None
    )

    show_missing_base_tool, set_show_missing_base_tool = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                    ft.Text("Alert"),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text(
                f"Please install the following missing tools.\n and restart this application.\n\n{platform_init_reason.message}\n"
            ),
            actions=[
                ft.TextButton("Exit", on_click=lambda: page.run_task(on_dialog_ok, action="close")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_missing_base_tool
        else None
    )

    show_missing_env_tool, set_show_missing_env_tool = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                    ft.Text("Alert"),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text(
                f"The following tools are not installed.\n\n{platform_init_reason.message}\n Please press the install tools button.\n"
            ),
            actions=[
                ft.TextButton(
                    "Install tools and exit",
                    on_click=lambda: page.run_task(on_dialog_ok, action="install"),
                ),
                ft.TextButton("Exit", on_click=lambda: page.run_task(on_dialog_ok, action="close")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_missing_env_tool
        else None
    )

    show_error_tool, set_show_error_tool = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.ERROR),
                    ft.Text("Error"),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text(f"{platform_init_reason.message}"),
            actions=[
                ft.TextButton("Exit", on_click=lambda: page.run_task(on_dialog_ok, action="close")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_error_tool
        else None
    )

    if platform_init_reason.code == ReasonCode.MISSING_VISUALSTUDIO:
        set_show_missing_vs(True)

    elif platform_init_reason.code == ReasonCode.MISSING_BASE_TOOLS:
        set_show_missing_base_tool(True)

    elif platform_init_reason.code == ReasonCode.MISSING_EMBEDDED_TOOLS:
        set_show_missing_env_tool(True)

    elif platform_init_reason.code == ReasonCode.ERROR:
        set_show_error_tool(True)

    return ft.View(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SETTINGS_SUGGEST, size=60, color=ft.Colors.BLUE),
                                ft.Text("OSLwright", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                        ft.Text("C/C++ Open Source Library Builder for Windows", size=18, color=ft.Colors.GREY_400),
                        ft.Container(height=20),
                        # 初期化処理が動いている間（理由が未定のとき）だけProgressRingを表示
                        (
                            ft.ProgressRing(width=30, height=30, stroke_width=3)
                            if platform_init_reason.code == ReasonCode.UNINITIALIZED
                            else ft.Container()
                        ),
                        ft.Container(height=10),
                        ft.Text(status_text, size=18, color=ft.Colors.GREY_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        ]
    )


def AppMain(page: ft.Page):
    page.title = "OSLwright: A C/C++ Open Source Library Builder for Windows"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = None

    platform_service = None
    package_service = None

    # アプリの状態管理変数
    loading_status = "System starting up..."
    platform_init_reason = PlatformReason(ReasonCode.UNINITIALIZED)

    # ダイアログのボタンが押された時の統合コールバック
    async def handle_dialog_action(action: str):
        nonlocal loading_status, platform_service, package_service
        if action == "install":
            package_files = platform_service.get_tool_package_files()
            packages = []
            for file_path in package_files:
                packages.append(package_service.load_package_file(file_path))

            page.session.store.set("packages", packages)
            page.session.store.set("build_force", True)

            loading_status = None
            page.render_views(render)
            page.navigate(Routes.BUILD)

        elif action == "close":
            # エラー発生時：アプリケーションを終了
            await page.window.close()

    def render():

        if loading_status is not None:
            return SplashScreen(
                status_text=loading_status, platform_init_reason=platform_init_reason, on_dialog_ok=handle_dialog_action
            )
        else:
            from app.pages import PackageInfoPage, PackageSelectPage, PackageOptionPage, BuildPage, AppSettingPage

            @ft.component
            def AppRouter():
                return ft.Router(
                    routes=[
                        ft.Route(index=True, path=Routes.HOME, component=PackageSelectPage),
                        ft.Route(path=Routes.PKG_INFO, component=PackageInfoPage),
                        ft.Route(path=Routes.PKG_OPTION, component=PackageOptionPage),
                        ft.Route(path=Routes.APP_SETTING, component=AppSettingPage),
                        ft.Route(path=Routes.BUILD, component=BuildPage),
                    ],
                    manage_views=True,
                )

            return AppRouter()

    # 初回レンダリング
    page.render_views(render)

    # バックグラウンド初期化タスク
    async def initialize_app():
        nonlocal loading_status, platform_init_reason, platform_service, package_service
        try:
            await asyncio.sleep(0.1)

            loading_status = "Initializing components and validating the environment..."
            page.render_views(render)

            # バックグラウンド同期処理の実行
            await asyncio.to_thread(initialize_all_services_sync)

            platform_service = get_service("PlatformService")
            package_service = get_service("PackageService")
            platform_init_reason = platform_service.get_platform_reason()

            if platform_init_reason.code == ReasonCode.COMPLETE:
                loading_status = None
                page.render_views(render)
            else:
                loading_status = "Alert..."
                page.render_views(render)
                await page.wait_until_visible()

        except Exception as e:
            # エラー発生時の処理
            platform_init_reason = PlatformReason(ReasonCode.ERROR, str(e))
            loading_status = "Initialization failed."
            page.render_views(render)

    # 初期化タスクを即時開始
    page.run_task(initialize_app)
    # asyncio.create_task(initialize_app())


if __name__ == "__main__":
    subprocess.run(["chcp.com", "65001"])
    os.environ["PYTHONUTF8"] = "1"

    ft.run(main=AppMain)
