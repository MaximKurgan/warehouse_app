# мои элементы flet

import flet as ft


class MoyTekst(ft.Text):
    def __init__(self, value="", size=None, weight=None, color=None, expand=None):
        super().__init__(
            value=value,
            size=size,
            weight=weight,
            color=color,
            expand=expand,
            text_align=ft.TextAlign.CENTER,
        )


class MoyaKnopka(ft.Button):
    def __init__(self, text, icon=None, on_click=None, data=None):
        super().__init__(
            content=text,
            icon=icon,
            on_click=on_click,
            data=data,
            height=42,
        )


class MoyaKnopkaIkonka(ft.IconButton):
    def __init__(self, icon, tooltip, on_click=None, data=None):
        super().__init__(
            icon=icon,
            tooltip=tooltip,
            on_click=on_click,
            data=data,
        )


class MoePole(ft.TextField):
    def __init__(
        self,
        label,
        value="",
        expand=True,
        prefix_icon=None,
        on_change=None,
        on_submit=None,
    ):
        super().__init__(
            label=label,
            value=value,
            expand=expand,
            prefix_icon=prefix_icon,
            on_change=on_change,
            on_submit=on_submit,
            text_align=ft.TextAlign.LEFT,
        )


class MoySpisok(ft.Dropdown):
    def __init__(self, label, value=None, expand=True, on_change=None):
        super().__init__(
            label=label,
            value=value,
            expand=expand,
            on_select=on_change,
            text_align=ft.TextAlign.CENTER,
        )


class MoyaTablica(ft.DataTable):
    def __init__(self, columns, rows=None):
        super().__init__(
            columns=columns,
            rows=rows or [],
            horizontal_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            vertical_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        )


class MoyBlok(ft.Container):
    def __init__(self, content, expand=None, width=None, height=None, padding=16):
        super().__init__(
            content=content,
            expand=expand,
            width=width,
            height=height,
            padding=padding,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=14,
            alignment=ft.Alignment.CENTER,
        )


class MoyaStroka(ft.Row):
    def __init__(self, controls=None, alignment=ft.MainAxisAlignment.CENTER,
                 expand=None, scroll=None, wrap=False,
                 vertical_alignment=ft.CrossAxisAlignment.CENTER):
        super().__init__(
            controls=controls or [],
            alignment=alignment,
            vertical_alignment=vertical_alignment,
            expand=expand,
            scroll=scroll,
            wrap=wrap,
        )


class MoyaKolonka(ft.Column):
    def __init__(self, controls=None, expand=None, visible=True, scroll=None,
                 spacing=14):
        super().__init__(
            controls=controls or [],
            expand=expand,
            visible=visible,
            scroll=scroll,
            spacing=spacing,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )


class MoeOkno(ft.AlertDialog):
    def __init__(self, title, content, actions=None, modal=True):
        super().__init__(
            title=MoyTekst(title, size=20, weight=ft.FontWeight.BOLD),
            content=content,
            actions=actions or [],
            modal=modal,
            actions_alignment=ft.MainAxisAlignment.CENTER,
            alignment=ft.Alignment.CENTER,
        )
