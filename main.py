# main.py
import flet as ft
from views.Loginview import LoginView
from views.MainPageview import MainPageView, MainMenuView


def main(page: ft.Page):
    page.title = "CampApp"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1000
    page.window.height = 700

    content_area = ft.Container(expand=True)

    
    def change_to_main_page(config: dict):
        page.session.store.set("db_config", config)
        content_area.content = MainPageView(page, config, on_continue_click=change_to_main_menu)
        page.update()

    def change_to_main_menu(e=None):
        content_area.content = MainMenuView(page, page.session.store.get("db_config"), on_restart_click=change_to_login_page)
        page.update()

    def change_to_login_page(e=None):
        page.session.store.clear()
        content_area.content = LoginView(page, on_login_success=change_to_main_page)
        page.update()

    content_area.content = LoginView(page, on_login_success=change_to_main_page)

    page.add(content_area)

if __name__ == "__main__":
    ft.run(main)