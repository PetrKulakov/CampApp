import flet as ft
from database import query
import database as dtb
from datetime import datetime, time
import asyncio

def MainPageView(page: ft.Page, db_config: dict, on_continue_click) -> ft.Control:
    continue_btn = ft.TextButton(
        content="Продолжить",
        icon=ft.Icons.ARROW_FORWARD,
        on_click=on_continue_click,
    )
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=60),
            ft.Text(f"Вы успешно вошли в базу: {db_config['dbname']}!", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(f"Хост: {db_config['host']}:{db_config['port']}, Пользователь: {db_config['user']}"),
            continue_btn,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )

async def pick_directory(page: ft.Page, title: str = "Выберите папку для сохранения", ) -> str | None:
    
    picker = next((s for s in page.services if isinstance(s, ft.FilePicker)), None)
    if not picker:
        picker = ft.FilePicker()
        page.services.append(picker)

    selected_path = await picker.get_directory_path(dialog_title=title)
    return selected_path


def MainMenuView(page: ft.Page, db_config: dict, on_restart_click) -> ft.Control:
    if not db_config:
        db_config = {"dbname": "Не указана", "host": "localhost", "port": 5432, "user": "postgres"}
    
    def open_backup_dialog(e=None):
        print(">>> Нажали на бэкап, открываем диалог...")  

        def choose_format(fmt: str):
            # Закрываем верхнее всплывающее окно
            page.pop_dialog()
            print(f"Выбран формат: {fmt}")
            # Показываем уведомление
            page.show_dialog(ft.SnackBar(ft.Text(f"Выгрузка в формате {fmt}...")))

        backup_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.BACKUP_ROUNDED, color=ft.Colors.PRIMARY),
                ft.Text("Формат резервной копии"),
            ], spacing=10),
            content=ft.Column(
                controls=[
                    ft.Text("Выберите формат для сохранения базы:", size=13, color=ft.Colors.GREY_400),
                    # ft.ListTile(
                    #     leading=ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.BLUE_400),
                    #     title=ft.Text("SQL Dump (.sql)"),
                    #     subtitle=ft.Text("Полная копия: схема таблиц и данные"),
                    #     on_click=lambda _: choose_format("SQL"),
                    # ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.TABLE_VIEW_ROUNDED, color=ft.Colors.GREEN_400),
                        title=ft.Text("Таблицы CSV (.csv)"),
                        subtitle=ft.Text("Удобно для Excel"),
                        on_click=handle_backup_csv
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DATA_OBJECT_ROUNDED, color=ft.Colors.ORANGE_400),
                        title=ft.Text("Документ JSON (.json)"),
                        subtitle=ft.Text("Формат JSON"),
                        on_click=handle_backup_json
                    ),
                ],
                tight=True,
                width=380,
            ),
            actions=[
                ft.TextButton(
                    content="Отмена",
                    on_click=lambda _: page.pop_dialog(),  # Закрытие в Flet 1.0
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

       
        if hasattr(page, "show_dialog"):
            page.show_dialog(backup_dialog)
        else:
            page.open(backup_dialog)

    
    action_btn = ft.PopupMenuButton(
        icon=ft.Icons.MORE_HORIZ,
        tooltip="Дополнительные функции",
        items=[
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.BACKUP_ROUNDED, size=18, color=ft.Colors.PRIMARY),
                    ft.Text("Сделать резервную копию"),
                ]),
                on_click=open_backup_dialog,  
            ),
            # ft.PopupMenuItem(
            #     content=ft.Row([
            #         ft.Icon(ft.Icons.REFRESH_ROUNDED, size=18, color=ft.Colors.PRIMARY),
            #         ft.Text("Обновить статус"),
            #     ]),
            #     on_click=lambda _: print("Обновление..."),
            # ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=18, color=ft.Colors.RED_400),
                    ft.Text("Сменить базу", color=ft.Colors.RED_400),
                ]),
                on_click= on_restart_click,
            ),
        ],
    )

    # 2. Верхняя плашка (Top Bar)
    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.STORAGE_ROUNDED, color=ft.Colors.PRIMARY, size=26),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            padding=8,
                            border_radius=8,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    f"База данных: {db_config.get('dbname')}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Хост: {db_config.get('host')}:{db_config.get('port')} • {db_config.get('user')}",
                                    size=12,
                                    color=ft.Colors.GREY_400,
                                ),
                            ],
                            spacing=2,
                            tight=True,
                        ),
                    ],
                    spacing=12,
                ),
                action_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=16, top=10, right=8, bottom=10),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        border_radius=12,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
    )

    # 3. Поле ввода запроса
    query_input = ft.TextField(
        hint_text="Введите SQL-запрос (например: SELECT * FROM users;)",
        multiline=True,
        min_lines=2,
        max_lines=5,
        expand=True,
        border=ft.OutlineInputBorder(border_radius=10),
        text_style=ft.TextStyle(font_family="monospace"),
    )

    result_content_btn_csv = None
    result_content_btn_json = None

    async def handle_export_csv(e=None):
        folder = await pick_directory(page, title="Куда сохранить CSV?")
        if not folder:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{folder}/result{db_config['dbname']}_{timestamp}.csv"
        result_content_btn_csv.disabled = True
        page.show_dialog(ft.SnackBar(ft.Text("Экспорт запущен в фоновом режиме...")))
        page.update()

        try:
            rows_count = await asyncio.to_thread(dtb.export_to_csv, query_input.value, filename, db_config)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Успех! Сохранено строк: {rows_count}\nФайл: {filename}"),
            bgcolor=ft.Colors.GREEN_800,
        ))
        except Exception as err:
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Ошибка при экспорте: {err}"),
            bgcolor=ft.Colors.RED_800,
        ))

        finally:
            result_content_btn_csv.disabled = False
            page.update()
    

    async def handle_export_json(e=None):
        folder = await pick_directory(page, title="Куда сохранить JSON?")
        if not folder:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{folder}/result{db_config['dbname']}_{timestamp}.json"
        result_content_btn_json.disabled = True
        page.show_dialog(ft.SnackBar(ft.Text("Экспорт запущен в фоновом режиме...")))
        page.update()

        try:
            rows_count = await asyncio.to_thread(dtb.export_to_json, query_input.value, filename, db_config)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Успех! Сохранено строк: {rows_count}\nФайл: {filename}"),
            bgcolor=ft.Colors.GREEN_800,
        ))
        except Exception as err:
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Ошибка при экспорте: {err}"),
            bgcolor=ft.Colors.RED_800,
        ))

        finally:
            result_content_btn_json.disabled = False
            page.update()
        
        

    async def handle_backup_csv(e=None):
        folder = await pick_directory(page, title="Куда сохранить БД?")
        if not folder:
            return
        filepath = f"{folder}"
        page.show_dialog(ft.SnackBar(ft.Text("Резервное копирование запущено")))
        page.update()

        try:
            rows_count = await asyncio.to_thread(dtb.backup_to_csv, db_config=db_config, filepath=filepath)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Успех! Сохранено строк: {rows_count}\nФайл: {filepath}"),
            bgcolor=ft.Colors.GREEN_800,
        ))
        except Exception as err:
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Ошибка при экспорте: {err}"),
            bgcolor=ft.Colors.RED_800,
        ))

        finally:
            page.update()

    async def handle_backup_csv(e=None):
        folder = await pick_directory(page, title="Куда сохранить БД?")
        if not folder:
            return
        filepath = f"{folder}"
        page.show_dialog(ft.SnackBar(ft.Text("Резервное копирование запущено")))
        page.update()

        try:
            rows_count = await asyncio.to_thread(dtb.backup_to_csv, db_config=db_config, filepath=filepath)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Успех! Сохранено строк: {rows_count}\nФайл: {filepath}"),
            bgcolor=ft.Colors.GREEN_800,
        ))
        except Exception as err:
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Ошибка при экспорте: {err}"),
            bgcolor=ft.Colors.RED_800,
        ))

        finally:
            page.update()

    async def handle_backup_json(e=None):
        folder = await pick_directory(page, title="Куда сохранить БД?")
        if not folder:
            return
        filepath = f"{folder}"
        page.show_dialog(ft.SnackBar(ft.Text("Резервное копирование запущено")))
        page.update()

        try:
            rows_count = await asyncio.to_thread(dtb.backup_to_json, db_config=db_config, filepath=filepath)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Успех! Сохранено строк: {rows_count}\nФайл: {filepath}"),
            bgcolor=ft.Colors.GREEN_800,
        ))
        except Exception as err:
            print(err)
            page.show_dialog(ft.SnackBar(
            ft.Text(f"Ошибка при экспорте: {err}"),
            bgcolor=ft.Colors.RED_800,
        ))

        finally:
            page.update()
    
        


    def create_table(data: list[dict] | dict) -> ft.Control:
        if not data:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.GREY_500),
                    ft.Text("Запрос успешно выполнен, но не вернул данных (0 строк)", color=ft.Colors.GREY_400),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=20,
            )

        if isinstance(data, dict):
            if "columns" in data and "rows" in data:
                columns_names = data["columns"]
                rows_data = data["rows"]
            else:
                columns_names = list(data.keys())
                rows_data = [list(data.values())]
        elif isinstance(data, list):
            columns_names = list(data[0].keys())
            rows_data = [[row.get(col) for col in columns_names] for row in data]

        table_columns = [
            ft.DataColumn(label=ft.Text(str(col), weight=ft.FontWeight.BOLD, size=13))
            for col in columns_names
        ]

        table_rows = []
        for row in rows_data:
            cells = []
            for val in row:
                if val is None:
                    cell_content = ft.Text("NULL", color=ft.Colors.GREY_500, italic=True)
                elif isinstance(val, bool):
                    cell_content = ft.Text(str(val), color=ft.Colors.BLUE_ACCENT if val else ft.Colors.RED_ACCENT)
                else:
                    cell_content = ft.Text(str(val), size=13)
                cells.append(ft.DataCell(cell_content))
            table_rows.append(ft.DataRow(cells=cells))

        data_table = ft.DataTable(
            columns=table_columns,
            rows=table_rows,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGH,
            horizontal_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            vertical_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[data_table],
                    scroll=ft.ScrollMode.AUTO,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    
    def on_execute_click(e):
        nonlocal result_content_btn_csv
        nonlocal result_content_btn_json
        sql = query_input.value.strip() if query_input.value else ""
        if not sql:
            return

        
        try:
            result = query(sql, config=db_config)
            result_content_table = create_table(result)
            result_content_btn_csv = ft.OutlinedButton(
                content="CSV",
                icon=ft.Icons.TABLE_VIEW_ROUNDED,
                icon_color=ft.Colors.GREEN_400,
                height=36,
                tooltip="Экспортировать результат в CSV файл",
                on_click=handle_export_csv
            )
    
            result_content_btn_json = ft.OutlinedButton(
                content="JSON",
                icon=ft.Icons.DATA_OBJECT_ROUNDED,
                icon_color=ft.Colors.ORANGE_400,
                height=36,
                tooltip="Экспортировать результат в JSON файл",
                on_click= handle_export_json
            )
            buttons_row = ft.Row(
                controls=[
                    result_content_btn_csv,
                    result_content_btn_json,
                ],
                spacing=10,
            )

            result_content = ft.Column(
                controls=[
                    buttons_row,          
                    result_content_table,  
                ],
                spacing=10,
                expand=True,
            )
            rows_count = len(result) if isinstance(result, list) else 1
            status_text = f"Успешно • Строк: {rows_count}"
            status_color = ft.Colors.GREEN_400
            status_icon = ft.Icons.CHECK_CIRCLE_OUTLINE

        except Exception as err:
            
            result_content = ft.Container(
                content=ft.Column([
                    ft.Text("Текст ошибки базы данных:", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{err}", color=ft.Colors.RED_200, font_family="monospace", size=13),
                ]),
                bgcolor=ft.Colors.BLACK_45,
                border=ft.Border.all(1, ft.Colors.RED_900),
                border_radius=8,
                padding=12,
            )
            status_text = "Ошибка синтаксиса или выполнения"
            status_color = ft.Colors.RED_400
            status_icon = ft.Icons.ERROR_OUTLINE

        
        result_box.content = ft.Column(
            controls=[
                # Верхняя плашка окна результата
                ft.Row(
                    controls=[
                        ft.Row([
                            ft.Icon(status_icon, size=20, color=status_color),
                            ft.Text("Результат выполнения", weight=ft.FontWeight.BOLD),
                            ft.Text(f"({status_text})", size=12, color=status_color),
                        ], spacing=8),
                        # Кнопка удаления/закрытия результата
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Закрыть результат",
                            on_click=lambda _: reset_to_initial_state(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Container(content=result_content, expand=True, padding=5),
            ],
            expand=True,
        )

        
        workspace.alignment = None
        workspace.content = ft.Column(
            controls=[
                query_section,
                result_box,
            ],
            spacing=15,
            expand=True,
        )
        page.update()

    
    execute_btn = ft.FilledButton(
        content="Выполнить",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        height=55,
        on_click=on_execute_click,
    )

    query_section = ft.Row(
        controls=[
            query_input,
            execute_btn,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )

    
    result_box = ft.Container(
        bgcolor=ft.Colors.BLACK_38,
        border_radius=10,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        padding=15,
        expand=True,
    )

    
    workspace = ft.Container(
        content=query_section,
        alignment=ft.Alignment.CENTER,
        expand=True,
    )

    # Функция возврата в исходное положение
    def reset_to_initial_state():
        workspace.alignment = ft.Alignment.CENTER
        workspace.content = query_section
        page.update()

    # 9. Главная сборка экрана
    return ft.Container(
        content=ft.Column(
            controls=[
                top_bar,    
                workspace,   
            ],
            spacing=15,
            expand=True,     
        ),
        padding=15,
        alignment=ft.Alignment.TOP_CENTER,  
        expand=True,
    )