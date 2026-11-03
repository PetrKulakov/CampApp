# views/Loginview.py
import flet as ft
from database import check_connection

def LoginView(page: ft.Page, on_login_success) -> ft.Control:
    FIELD_RADIUS = 10
    

    host_field = ft.TextField(label="Host", value="localhost", border_radius=FIELD_RADIUS, expand=2)
    port_field = ft.TextField(label="Port", value="5432", border_radius=FIELD_RADIUS, expand=1)
    user_field = ft.TextField(label="User", value="postgres", border_radius=FIELD_RADIUS, width=340)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, border_radius=FIELD_RADIUS, width=340)
    dbname_field = ft.TextField(label="Database Name", border_radius=FIELD_RADIUS, width=340)

    # Текст для ошибки (красный)
    error_text = ft.Text(color=ft.Colors.RED_400, size=13, visible=False)

    # Индикатор загрузки (чтобы пользователь видел процесс)
    progress = ft.ProgressBar(visible=False, width=340)

    def on_login_click(e):
        # 1. Забираем значения прямо из полей ввода в обычный словарь:
        config = {
            "host": host_field.value.strip(),
            "port": int(port_field.value.strip() or 5432),
            "user": user_field.value.strip(),
            "password": password_field.value,
            "dbname": dbname_field.value.strip(),
        }

        # Блокируем кнопку на время проверки
        login_btn.disabled = True
        progress.visible = True
        error_text.visible = False
        page.update()

        # 2. Вызываем функцию проверки из database.py
        success, error_msg = check_connection(config)

        if success:
            on_login_success(config)
        else:
            error_text.value = f"Ошибка: {error_msg}"
            error_text.visible = True
            login_btn.disabled = False
            progress.visible = False
            page.update()

    login_btn = ft.FilledButton(
        content="Авторизоваться",
        icon=ft.Icons.LOGIN,
        width=340,
        height=45,
        on_click=on_login_click,
    )

    config_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.PRIMARY, size=30),
                        ft.Text("Подключение к БД", size=20, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([host_field, port_field], width=340, spacing=10),
                user_field,
                password_field,
                dbname_field,
                error_text,
                progress,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                login_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        width=390,
        padding=24,
        border_radius=18,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=1,
            color=ft.Colors.BLACK_54,
            offset=ft.Offset(0, 6),
        ),
    )

    return ft.Container(
        content=config_card,
        alignment=ft.Alignment.CENTER,
        expand=True,
    )