"""
PackageInfo Controller.
"""

import flet as ft

from ..core.constants import Routes
from ..controllers.package_info_controller import PackageInfoController
from ..models.package_model import PackageModel


@ft.component
def PackageInfoPage():
    """PackageInfo Page"""

    page = ft.context.page

    controller = ft.use_memo(lambda: PackageInfoController(), [])
    packages = page.session.store.get("packages")
    package = packages[0]
    info = controller.get_package_info(package)

    async def handle_launch_site(e):
        url_string = e.control.content
        if url_string:
            await ft.UrlLauncher().launch_url(url_string)

    async def handle_url_launch(e):
        url_string = e.data
        if url_string:
            await ft.UrlLauncher().launch_url(url_string)

    layout = ft.Column(
        controls=[
            ft.Column(
                spacing=5,
                controls=[
                    ft.Text(info.display, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(info.description, size=14),
                    ft.Text(f"Version: {info.version}"),
                    ft.Text(f"License: {info.license}"),
                    ft.Row(
                        spacing=0,
                        controls=[
                            ft.Text(f"Site: "),
                            ft.TextButton(info.site, on_click=handle_launch_site),
                        ],
                    ),
                    ft.Text(f"Process time: {info.process_time}"),
                    ft.Divider(),
                ],
            ),
            ft.Text("Details:", size=16, weight=ft.FontWeight.BOLD),
            # Markdown 表示
            ft.Column(
                controls=[
                    ft.Markdown(
                        value=info.markdown,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.NIGHT_OWL,
                        on_tap_link=handle_url_launch,
                    )
                ],
                expand=True,
                scroll=ft.ScrollMode.ALWAYS,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ],
        expand=True,
        spacing=1,
    )

    return ft.View(
        route=Routes.PKG_INFO,
        appbar=ft.AppBar(
            title=ft.Text("Package Infomation"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.navigate(Routes.HOME)),
        ),
        controls=[layout],
    )
