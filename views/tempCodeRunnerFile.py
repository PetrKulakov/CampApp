 result_content_btn_json = ft.OutlinedButton(
                content="JSON",
                icon=ft.Icons.DATA_OBJECT_ROUNDED,
                icon_color=ft.Colors.ORANGE_400,
                height=36,
                tooltip="Экспортировать результат в JSON файл",
                on_click=dtb.export_to_json(sql, pick_directory(page))
            )