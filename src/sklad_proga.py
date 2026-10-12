#главное окно и все кнопки

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

import flet as ft

from baza import Baza
from modeli import (
    Kategoriya,
    Tovar,
    Prihod,
    Postavshik,
    Spisanie,
)
from spisok_par import SpisokPar
from otchet import Otchet
from elementi import (
    MoyaKnopka,
    MoyaKolonka,
    MoyBlok,
    MoyaTablica,
    MoeOkno,
    MoySpisok,
    MoyaKnopkaIkonka,
    MoyaStroka,
    MoyTekst,
    MoePole,
)


class SkladProga:
    #главный класс проги

    MALO_TOVARA = 10
    VSE_KATEGORII = "Все категории"
    VSE_POSTAVSHIKI = "Все поставщики"

    def __init__(self, page, baza=None, put_k_otchetu=None):
        self.page = page
        self.baza = baza or Baza()
        default_report = Path(__file__).resolve().parent / "otchet_seansa.txt"
        self.otchet = Otchet(put_k_otchetu or default_report)
        self.tovari = []
        self.operacii = []
        self.kategorii = []
        self.postavshiki = []
        self.stranici = SpisokPar()
        self.zakrita = False
        self.nastroit_okno()
        self.sozdat_elementi()
        self.sozdat_stranici()
        self.zagruzit_dannie()
        self.page.on_close = self.zakrit_programmu
        self.page.on_disconnect = self.zakrit_programmu
        self.page.add(self.sobrat_okno())
        self.page.run_task(self.chasi)
        self.page.update()

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = value

    @property
    def baza(self):
        return self._baza

    @baza.setter
    def baza(self, value):
        self._baza = value

    @property
    def otchet(self):
        return self._otchet

    @otchet.setter
    def otchet(self, value):
        self._otchet = value

    def __repr__(self):
        return f"SkladProga(products={len(self.tovari)})"

    def __str__(self):
        return "Складской учёт"

    def __len__(self):
        return len(self.tovari)

    def __bool__(self):
        return not self.zakrita

    @staticmethod
    def zapusk(page):
        page.data = SkladProga(page)

    @staticmethod
    def dengi_tekstom(value):
        return f"{value:,.2f} ₽".replace(",", " ")

    @staticmethod
    def poluchit_cenu(value):
        return float(str(value).replace(",", ".").strip())

    @staticmethod
    def kolonki_tablici(*titles):
        return [ft.DataColumn(label=MoyTekst(title)) for title in titles]

    def nastroit_okno(self):
        self.page.title = "Складской учёт"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def sozdat_elementi(self):
        self.status_text = MoyTekst("")
        self.date_text = MoyTekst("")
        self.time_text = MoyTekst("", size=20, weight=ft.FontWeight.BOLD)
        self.theme_button = MoyaKnopkaIkonka(
            ft.Icons.DARK_MODE, "Тёмная тема", self.smenit_temu
        )

        self.positions_text = MoyTekst("0", size=28, weight=ft.FontWeight.BOLD)
        self.units_text = MoyTekst("0", size=28, weight=ft.FontWeight.BOLD)
        self.value_text = MoyTekst("0 ₽", size=28, weight=ft.FontWeight.BOLD)
        self.low_stock_text = MoyTekst("0", size=28, weight=ft.FontWeight.BOLD)

        self.article_input = MoePole("Артикул")
        self.name_input = MoePole("Название товара")
        self.category_input = MoySpisok("Категория")
        self.supplier_input = MoySpisok("Поставщик")
        self.quantity_input = MoePole("Начальное количество")
        self.price_input = MoePole("Цена")

        self.search_input = MoePole(
            "Поиск по товару, артикулу, категории или поставщику",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self.filtr_tovarov,
        )
        self.category_filter = MoySpisok(
            "Категория", self.VSE_KATEGORII, on_change=self.filtr_tovarov
        )
        self.supplier_filter = MoySpisok(
            "Поставщик", self.VSE_POSTAVSHIKI, on_change=self.filtr_tovarov
        )
        self.product_result_text = MoyTekst("")

        self.new_category_input = MoePole("Новая категория")
        self.new_supplier_input = MoePole("Новый поставщик")
        self.directory_status_text = MoyTekst("")

        self.tovari_table = MoyaTablica(
            self.kolonki_tablici(
                "Артикул", "Название", "Категория", "Поставщик",
                "Остаток", "Цена", "Стоимость", "Действия",
            )
        )
        self.low_stock_table = MoyaTablica(
            self.kolonki_tablici("Артикул", "Товар", "Категория", "Остаток")
        )
        self.operacii_table = MoyaTablica(
            self.kolonki_tablici("Дата", "Артикул", "Товар", "Операция", "Количество")
        )
        self.kategorii_table = MoyaTablica(
            self.kolonki_tablici("Категория", "Действия")
        )
        self.postavshiki_table = MoyaTablica(
            self.kolonki_tablici("Поставщик", "Действия")
        )
        self.category_report_table = MoyaTablica(
            self.kolonki_tablici("Категория", "Позиций", "Единиц", "Стоимость")
        )
        self.receipt_count_text = MoyTekst("0", size=26, weight=ft.FontWeight.BOLD)
        self.writeoff_count_text = MoyTekst("0", size=26, weight=ft.FontWeight.BOLD)
        self.receipt_units_text = MoyTekst("0", size=26, weight=ft.FontWeight.BOLD)
        self.writeoff_units_text = MoyTekst("0", size=26, weight=ft.FontWeight.BOLD)

    def sozdat_stranici(self):
        self.stranici[0] = self.glavnaya_stranica()
        self.stranici[1] = self.stranica_tovarov()
        self.stranici[2] = self.stranica_operacii()
        self.stranici[3] = self.stranica_spravochnikov()
        self.stranici[4] = self.stranica_otchetov()

    def sobrat_okno(self):
        navigation = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=175,
            expand=True,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Главная",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INVENTORY_2_OUTLINED,
                    selected_icon=ft.Icons.INVENTORY_2,
                    label="Товары",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                    selected_icon=ft.Icons.RECEIPT_LONG,
                    label="Операции",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.LIST_ALT_OUTLINED,
                    selected_icon=ft.Icons.LIST_ALT,
                    label="Справочники",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ASSESSMENT_OUTLINED,
                    selected_icon=ft.Icons.ASSESSMENT,
                    label="Отчёты",
                ),
            ],
            on_change=self.smenit_stranicu,
        )
        sidebar = MoyBlok(
            MoyaKolonka(
                [
                    MoyaStroka(
                        [
                            ft.Icon(ft.Icons.WAREHOUSE, size=30),
                            MoyTekst("СКЛАД", size=20, weight=ft.FontWeight.BOLD),
                        ]
                    ),
                    navigation,
                    self.theme_button,
                    MoyTekst(f"Пользователь: {self.otchet.login}", size=11),
                ],
                expand=True,
            ),
            width=195,
            expand=False,
            padding=10,
        )
        content = MoyaKolonka([view for _, view in self.stranici.items()], expand=True)
        return MoyaStroka(
            [sidebar, ft.VerticalDivider(width=1), MoyBlok(content, expand=True)],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def zagolovok_stranici(self, title, subtitle):
        return MoyaStroka(
            [
                MoyaKolonka(
                    [
                        MoyTekst(title, size=28, weight=ft.FontWeight.BOLD),
                        MoyTekst(subtitle, size=14),
                    ],
                    spacing=3,
                ),
                MoyaKolonka(
                    [self.date_text, self.time_text], spacing=3
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def zagolovok_razdela(self, text):
        return MoyTekst(text, size=20, weight=ft.FontWeight.BOLD)

    def kartochka(self, caption, value_control, icon, description):
        return MoyBlok(
            MoyaKolonka(
                [
                    ft.Icon(icon, size=30),
                    value_control,
                    MoyTekst(caption, weight=ft.FontWeight.BOLD),
                    MoyTekst(description, size=12),
                ],
                spacing=5,
            ),
            expand=True,
            height=160,
        )

    def panel_tablici(self, table):
        # без expand таблица не превращается в серый блок
        return MoyBlok(MoyaStroka([table], scroll=ft.ScrollMode.AUTO))

    def glavnaya_stranica(self):
        return MoyaKolonka(
            [
                self.zagolovok_stranici("Главная", "Обзор текущего состояния склада"),
                MoyaStroka(
                    [
                        self.kartochka(
                            "Товарных позиций", self.positions_text,
                            ft.Icons.INVENTORY_2, "Разных товаров",
                        ),
                        self.kartochka(
                            "Всего единиц", self.units_text,
                            ft.Icons.NUMBERS, "Общий остаток",
                        ),
                    ]
                ),
                MoyaStroka(
                    [
                        self.kartochka(
                            "Стоимость", self.value_text,
                            ft.Icons.ATTACH_MONEY, "По текущим ценам",
                        ),
                        self.kartochka(
                            "Низкий остаток", self.low_stock_text,
                            ft.Icons.WARNING, f"Менее {self.MALO_TOVARA} шт",
                        ),
                    ]
                ),
                self.zagolovok_razdela("Товары с низким остатком"),
                self.panel_tablici(self.low_stock_table),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def stranica_tovarov(self):
        form = MoyBlok(
            MoyaKolonka(
                [
                    MoyaStroka([self.article_input, self.name_input]),
                    MoyaStroka([self.category_input, self.supplier_input]),
                    MoyaStroka([self.quantity_input, self.price_input]),
                    MoyaKnopka(
                        "Сохранить товар", ft.Icons.SAVE, self.dobavit_tovar
                    ),
                    self.status_text,
                ]
            )
        )
        return MoyaKolonka(
            [
                self.zagolovok_stranici("Товары", "Добавление, поиск и управление"),
                self.zagolovok_razdela("Добавление товара"),
                form,
                self.zagolovok_razdela("Товары на складе"),
                MoyaStroka(
                    [
                        self.search_input,
                        MoyaKnopka("Найти", ft.Icons.SEARCH, self.filtr_tovarov),
                        MoyaKnopka("Сбросить", ft.Icons.REFRESH, self.sbrosit_filtri),
                    ]
                ),
                MoyaStroka([self.category_filter, self.supplier_filter]),
                self.panel_tablici(self.tovari_table),
                self.product_result_text,
            ],
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
        )

    def stranica_operacii(self):
        return MoyaKolonka(
            [
                self.zagolovok_stranici(
                    "Складские операции", "История прихода и списания товаров"
                ),
                self.panel_tablici(self.operacii_table),
            ],
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
        )

    def stranica_spravochnikov(self):
        categories_panel = MoyBlok(
            MoyaKolonka(
                [
                    self.zagolovok_razdela("Категории"),
                    MoyaStroka(
                        [
                            self.new_category_input,
                            MoyaKnopka("Добавить", ft.Icons.ADD, self.dobavit_kategoriyu),
                        ]
                    ),
                    MoyaStroka([self.kategorii_table], scroll=ft.ScrollMode.AUTO),
                ]
            )
        )
        suppliers_panel = MoyBlok(
            MoyaKolonka(
                [
                    self.zagolovok_razdela("Поставщики"),
                    MoyaStroka(
                        [
                            self.new_supplier_input,
                            MoyaKnopka("Добавить", ft.Icons.ADD, self.dobavit_postavshika),
                        ]
                    ),
                    MoyaStroka([self.postavshiki_table], scroll=ft.ScrollMode.AUTO),
                ]
            )
        )
        return MoyaKolonka(
            [
                self.zagolovok_stranici(
                    "Справочники", "Управление категориями и поставщиками"
                ),
                categories_panel,
                suppliers_panel,
                self.directory_status_text,
            ],
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
        )

    def stranica_otchetov(self):
        return MoyaKolonka(
            [
                self.zagolovok_stranici("Отчёты", "Основные показатели склада"),
                MoyaKnopka("Обновить", ft.Icons.REFRESH, self.obnovit_otcheti_knopkoy),
                self.zagolovok_razdela("Отчёт по категориям"),
                self.panel_tablici(self.category_report_table),
                self.zagolovok_razdela("Складские операции"),
                MoyaStroka(
                    [
                        self.kartochka(
                            "Операций прихода", self.receipt_count_text,
                            ft.Icons.ADD, "Количество приходов",
                        ),
                        self.kartochka(
                            "Операций списания", self.writeoff_count_text,
                            ft.Icons.REMOVE, "Количество списаний",
                        ),
                    ]
                ),
                MoyaStroka(
                    [
                        self.kartochka(
                            "Принято единиц", self.receipt_units_text,
                            ft.Icons.MOVE_TO_INBOX, "Всего принято",
                        ),
                        self.kartochka(
                            "Списано единиц", self.writeoff_units_text,
                            ft.Icons.OUTBOX, "Всего списано",
                        ),
                    ]
                ),
            ],
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.AUTO,
        )

    def zagruzit_dannie(self):
        self.tovari = self.baza.poluchit_tovari()
        self.operacii = self.baza.poluchit_operacii()
        self.kategorii = self.baza.poluchit_kategorii()
        self.postavshiki = self.baza.poluchit_postavshikov()
        self.obnovit_vse()

    def obnovit_vse(self):
        self.obnovit_spiski()
        self.obnovit_tablicu_tovarov()
        self.obnovit_tablicu_operacii()
        self.obnovit_spravochniki()
        self.obnovit_glavnuyu()
        self.obnovit_otcheti()

    def obnovit_spiski(self):
        self.category_input.options = [
            ft.dropdown.Option(item.nazvanie) for item in self.kategorii
        ]
        self.supplier_input.options = [
            ft.dropdown.Option(item.nazvanie) for item in self.postavshiki
        ]
        self.category_filter.options = [ft.dropdown.Option(self.VSE_KATEGORII)]
        self.category_filter.options.extend(
            ft.dropdown.Option(item.nazvanie) for item in self.kategorii
        )
        self.supplier_filter.options = [ft.dropdown.Option(self.VSE_POSTAVSHIKI)]
        self.supplier_filter.options.extend(
            ft.dropdown.Option(item.nazvanie) for item in self.postavshiki
        )
        category_names = [item.nazvanie for item in self.kategorii]
        supplier_names = [item.nazvanie for item in self.postavshiki]
        if self.category_filter.value not in category_names + [self.VSE_KATEGORII]:
            self.category_filter.value = self.VSE_KATEGORII
        if self.supplier_filter.value not in supplier_names + [self.VSE_POSTAVSHIKI]:
            self.supplier_filter.value = self.VSE_POSTAVSHIKI

    def vibrannie_tovari(self):
        query = (self.search_input.value or "").strip().casefold()
        category = self.category_filter.value or self.VSE_KATEGORII
        supplier = self.supplier_filter.value or self.VSE_POSTAVSHIKI
        selected = []
        for product in self.tovari:
            searchable = " ".join(
                (product.artikul, product.nazvanie, product.kategoriya, product.postavshik)
            ).casefold()
            matches_category = (
                category == self.VSE_KATEGORII or product.kategoriya == category
            )
            matches_supplier = (
                supplier == self.VSE_POSTAVSHIKI or product.postavshik == supplier
            )
            if query in searchable and matches_category and matches_supplier:
                selected.append(product)
        return selected

    def obnovit_tablicu_tovarov(self):
        self.tovari_table.rows.clear()
        for product in self.vibrannie_tovari():
            actions = MoyaStroka(
                [
                    MoyaKnopkaIkonka(
                        ft.Icons.SWAP_HORIZ, "Приход / списание",
                        self.okno_operacii, product,
                    ),
                    MoyaKnopkaIkonka(
                        ft.Icons.EDIT, "Редактировать",
                        self.okno_izmeneniya_tovara, product,
                    ),
                    MoyaKnopkaIkonka(
                        ft.Icons.DELETE, "Удалить",
                        self.okno_udaleniya_tovara, product,
                    ),
                ]
            )
            self.tovari_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(MoyTekst(product.artikul)),
                        ft.DataCell(MoyTekst(product.nazvanie)),
                        ft.DataCell(MoyTekst(product.kategoriya)),
                        ft.DataCell(MoyTekst(product.postavshik)),
                        ft.DataCell(MoyTekst(str(product.kolichestvo))),
                        ft.DataCell(MoyTekst(self.dengi_tekstom(product.cena))),
                        ft.DataCell(MoyTekst(self.dengi_tekstom(product.obshaya_stoimost()))),
                        ft.DataCell(actions),
                    ]
                )
            )
        self.product_result_text.value = (
            f"Найдено товаров: {len(self.tovari_table.rows)}"
            if self.tovari_table.rows else "По заданным условиям товары не найдены"
        )

    def obnovit_tablicu_operacii(self):
        self.operacii_table.rows.clear()
        for operation in self.operacii:
            self.operacii_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(MoyTekst(operation.data_operacii)),
                        ft.DataCell(MoyTekst(operation.artikul)),
                        ft.DataCell(MoyTekst(operation.nazvanie_tovara)),
                        ft.DataCell(MoyTekst(operation.tip_operacii)),
                        ft.DataCell(MoyTekst(operation.kolichestvo_tekstom())),
                    ]
                )
            )

    def obnovit_spravochniki(self):
        self.kategorii_table.rows.clear()
        for category in sorted(self.kategorii):
            actions = MoyaStroka(
                [
                    MoyaKnopkaIkonka(
                        ft.Icons.EDIT, "Редактировать",
                        self.okno_izmeneniya_kategorii, category,
                    ),
                    MoyaKnopkaIkonka(
                        ft.Icons.DELETE, "Удалить",
                        self.okno_udaleniya_kategorii, category,
                    ),
                ]
            )
            self.kategorii_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(MoyTekst(category.nazvanie)), ft.DataCell(actions)])
            )
        self.postavshiki_table.rows.clear()
        for supplier in sorted(self.postavshiki):
            actions = MoyaStroka(
                [
                    MoyaKnopkaIkonka(
                        ft.Icons.EDIT, "Редактировать",
                        self.okno_izmeneniya_postavshika, supplier,
                    ),
                    MoyaKnopkaIkonka(
                        ft.Icons.DELETE, "Удалить",
                        self.okno_udaleniya_postavshika, supplier,
                    ),
                ]
            )
            self.postavshiki_table.rows.append(
                ft.DataRow(cells=[ft.DataCell(MoyTekst(supplier.nazvanie)), ft.DataCell(actions)])
            )

    def obnovit_glavnuyu(self):
        self.positions_text.value = str(len(self.tovari))
        self.units_text.value = str(sum(product.kolichestvo for product in self.tovari))
        self.value_text.value = self.dengi_tekstom(
            sum(product.obshaya_stoimost() for product in self.tovari)
        )
        low_stock = [
            product for product in self.tovari
            if product.kolichestvo < self.MALO_TOVARA
        ]
        self.low_stock_text.value = str(len(low_stock))
        self.low_stock_table.rows.clear()
        for product in low_stock:
            self.low_stock_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(MoyTekst(product.artikul)),
                        ft.DataCell(MoyTekst(product.nazvanie)),
                        ft.DataCell(MoyTekst(product.kategoriya)),
                        ft.DataCell(MoyTekst(str(product.kolichestvo))),
                    ]
                )
            )

    def obnovit_otcheti(self):
        category_totals = SpisokPar()
        for category in self.kategorii:
            category_totals[category.nazvanie] = [0, 0, 0.0]
        for product in self.tovari:
            if product.kategoriya not in category_totals:
                category_totals[product.kategoriya] = [0, 0, 0.0]
            totals = category_totals[product.kategoriya]
            totals[0] += 1
            totals[1] += product.kolichestvo
            totals[2] += product.obshaya_stoimost()
        self.category_report_table.rows.clear()
        for category_name, totals in category_totals.items():
            self.category_report_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(MoyTekst(category_name)),
                        ft.DataCell(MoyTekst(str(totals[0]))),
                        ft.DataCell(MoyTekst(str(totals[1]))),
                        ft.DataCell(MoyTekst(self.dengi_tekstom(totals[2]))),
                    ]
                )
            )
        receipts = [
            item for item in self.operacii if isinstance(item, Prihod)
        ]
        writeoffs = [
            item for item in self.operacii if isinstance(item, Spisanie)
        ]
        self.receipt_count_text.value = str(len(receipts))
        self.writeoff_count_text.value = str(len(writeoffs))
        self.receipt_units_text.value = str(sum(item.kolichestvo for item in receipts))
        self.writeoff_units_text.value = str(sum(item.kolichestvo for item in writeoffs))

    def soobshenie(self, message, is_error=False, directory=False):
        control = self.directory_status_text if directory else self.status_text
        control.value = message
        control.color = ft.Colors.RED if is_error else ft.Colors.GREEN

    def dobavit_tovar(self, event=None):
        try:
            product = Tovar(
                self.article_input.value,
                self.name_input.value,
                self.category_input.value or "",
                self.supplier_input.value or "",
                int((self.quantity_input.value or "").strip()),
                self.poluchit_cenu(self.price_input.value or ""),
            )
            self.baza.sozdat_tovar(product)
        except (ValueError, TypeError) as error:
            self.soobshenie(str(error), True)
        except sqlite3.IntegrityError:
            self.soobshenie("Товар с таким артикулом уже существует", True)
        else:
            self.ochistit_formu_tovara()
            self.zagruzit_dannie()
            self.soobshenie(f"Товар «{product.nazvanie}» добавлен")
        self.page.update()

    def ochistit_formu_tovara(self):
        for field in (
            self.article_input, self.name_input, self.quantity_input, self.price_input
        ):
            field.value = ""
        self.category_input.value = None
        self.supplier_input.value = None

    def dobavit_kategoriyu(self, event=None):
        try:
            category = Kategoriya(self.new_category_input.value)
            self.baza.dobavit_kategoriyu(category)
        except ValueError as error:
            self.soobshenie(str(error), True, True)
        except sqlite3.IntegrityError:
            self.soobshenie("Такая категория уже существует", True, True)
        else:
            self.new_category_input.value = ""
            self.zagruzit_dannie()
            self.soobshenie(f"Категория «{category.nazvanie}» добавлена", directory=True)
        self.page.update()

    def dobavit_postavshika(self, event=None):
        try:
            supplier = Postavshik(self.new_supplier_input.value)
            self.baza.dobavit_postavshika(supplier)
        except ValueError as error:
            self.soobshenie(str(error), True, True)
        except sqlite3.IntegrityError:
            self.soobshenie("Такой поставщик уже существует", True, True)
        else:
            self.new_supplier_input.value = ""
            self.zagruzit_dannie()
            self.soobshenie(f"Поставщик «{supplier.nazvanie}» добавлен", directory=True)
        self.page.update()

    def filtr_tovarov(self, event=None):
        self.obnovit_tablicu_tovarov()
        self.page.update()

    def sbrosit_filtri(self, event=None):
        self.search_input.value = ""
        self.category_filter.value = self.VSE_KATEGORII
        self.supplier_filter.value = self.VSE_POSTAVSHIKI
        self.filtr_tovarov()

    def okno_izmeneniya_tovara(self, event):
        product = event.control.data
        article = MoePole("Артикул", product.artikul)
        name = MoePole("Название", product.nazvanie)
        category = MoySpisok("Категория", product.kategoriya)
        supplier = MoySpisok("Поставщик", product.postavshik)
        price = MoePole("Цена", str(product.cena))
        category.options = [ft.dropdown.Option(item.nazvanie) for item in self.kategorii]
        supplier.options = [ft.dropdown.Option(item.nazvanie) for item in self.postavshiki]
        data = (product, article, name, category, supplier, price)
        dialog = MoeOkno(
            "Редактирование товара",
            MoyaKolonka([article, name, category, supplier, price]),
            [
                MoyaKnopka("Сохранить", ft.Icons.SAVE, self.sohranit_izmenenie_tovara, data),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def sohranit_izmenenie_tovara(self, event):
        original, article, name, category, supplier, price = event.control.data
        try:
            edited = Tovar(
                article.value, name.value, category.value or "", supplier.value or "",
                original.kolichestvo, self.poluchit_cenu(price.value),
            )
            self.baza.izmenit_tovar(original.artikul, edited)
        except (ValueError, TypeError) as error:
            self.soobshenie(str(error), True)
        except sqlite3.IntegrityError:
            self.soobshenie("Товар с таким артикулом уже существует", True)
        else:
            self.page.pop_dialog()
            self.zagruzit_dannie()
            self.soobshenie(f"Товар «{edited.nazvanie}» обновлён")
        self.page.update()

    def okno_udaleniya_tovara(self, event):
        product = event.control.data
        dialog = MoeOkno(
            "Удаление товара",
            MoyTekst(f"Удалить «{product.nazvanie}»? История операций сохранится"),
            [
                MoyaKnopka("Удалить", ft.Icons.DELETE, self.udalit_tovar, product),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def udalit_tovar(self, event):
        product = event.control.data
        self.baza.udalit_tovar(product.artikul)
        self.page.pop_dialog()
        self.zagruzit_dannie()
        self.soobshenie(f"Товар «{product.nazvanie}» удалён")
        self.page.update()

    def okno_operacii(self, event):
        product = event.control.data
        kind = MoySpisok("Тип операции", "Приход")
        kind.options = [ft.dropdown.Option("Приход"), ft.dropdown.Option("Списание")]
        quantity = MoePole("Количество")
        data = (product, kind, quantity)
        dialog = MoeOkno(
            f"Операция: {product.nazvanie}",
            MoyaKolonka([kind, quantity, MoyTekst(f"Текущий остаток: {product.kolichestvo}")]),
            [
                MoyaKnopka("Провести", ft.Icons.SAVE, self.sohranit_operaciyu, data),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def sohranit_operaciyu(self, event):
        product, kind, quantity = event.control.data
        try:
            amount = int((quantity.value or "").strip())
            operation_class = (
                Prihod if kind.value == "Приход" else Spisanie
            )
            operation = operation_class(product.artikul, product.nazvanie, amount)
            self.baza.provesti_operaciyu(product, operation)
        except (ValueError, TypeError) as error:
            self.soobshenie(str(error), True)
        else:
            self.page.pop_dialog()
            self.zagruzit_dannie()
            self.soobshenie(f"Операция «{operation.tip_operacii}» проведена")
        self.page.update()

    def okno_izmeneniya_kategorii(self, event):
        category = event.control.data
        name = MoePole("Название категории", category.nazvanie)
        dialog = MoeOkno(
            "Редактирование категории",
            name,
            [
                MoyaKnopka(
                    "Сохранить", ft.Icons.SAVE, self.sohranit_izmenenie_kategorii,
                    (category, name),
                ),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def sohranit_izmenenie_kategorii(self, event):
        category, name_field = event.control.data
        try:
            edited = Kategoriya(name_field.value)
            self.baza.izmenit_kategoriyu(category.nazvanie, edited.nazvanie)
        except ValueError as error:
            self.soobshenie(str(error), True, True)
        except sqlite3.IntegrityError:
            self.soobshenie("Такая категория уже существует", True, True)
        else:
            self.page.pop_dialog()
            self.zagruzit_dannie()
            self.soobshenie(f"Категория «{edited.nazvanie}» обновлена", directory=True)
        self.page.update()

    def okno_udaleniya_kategorii(self, event):
        category = event.control.data
        if self.baza.kategoriya_ispolzuetsya(category.nazvanie):
            self.soobshenie("Нельзя удалить категорию, которая используется", True, True)
            self.page.update()
            return
        dialog = MoeOkno(
            "Удаление категории",
            MoyTekst(f"Удалить категорию «{category.nazvanie}»?"),
            [
                MoyaKnopka("Удалить", ft.Icons.DELETE, self.udalit_kategoriyu, category),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def udalit_kategoriyu(self, event):
        category = event.control.data
        self.baza.udalit_kategoriyu(category.nazvanie)
        self.page.pop_dialog()
        self.zagruzit_dannie()
        self.soobshenie(f"Категория «{category.nazvanie}» удалена", directory=True)
        self.page.update()

    def okno_izmeneniya_postavshika(self, event):
        supplier = event.control.data
        name = MoePole("Название поставщика", supplier.nazvanie)
        dialog = MoeOkno(
            "Редактирование поставщика",
            name,
            [
                MoyaKnopka(
                    "Сохранить", ft.Icons.SAVE, self.sohranit_izmenenie_postavshika,
                    (supplier, name),
                ),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def sohranit_izmenenie_postavshika(self, event):
        supplier, name_field = event.control.data
        try:
            edited = Postavshik(name_field.value)
            self.baza.izmenit_postavshika(supplier.nazvanie, edited.nazvanie)
        except ValueError as error:
            self.soobshenie(str(error), True, True)
        except sqlite3.IntegrityError:
            self.soobshenie("Такой поставщик уже существует", True, True)
        else:
            self.page.pop_dialog()
            self.zagruzit_dannie()
            self.soobshenie(f"Поставщик «{edited.nazvanie}» обновлён", directory=True)
        self.page.update()

    def okno_udaleniya_postavshika(self, event):
        supplier = event.control.data
        if self.baza.postavshik_ispolzuetsya(supplier.nazvanie):
            self.soobshenie("Нельзя удалить используемого поставщика", True, True)
            self.page.update()
            return
        dialog = MoeOkno(
            "Удаление поставщика",
            MoyTekst(f"Удалить поставщика «{supplier.nazvanie}»?"),
            [
                MoyaKnopka("Удалить", ft.Icons.DELETE, self.udalit_postavshika, supplier),
                MoyaKnopka("Отмена", ft.Icons.CLOSE, self.zakrit_okno),
            ],
        )
        self.page.show_dialog(dialog)

    def udalit_postavshika(self, event):
        supplier = event.control.data
        self.baza.udalit_postavshika(supplier.nazvanie)
        self.page.pop_dialog()
        self.zagruzit_dannie()
        self.soobshenie(f"Поставщик «{supplier.nazvanie}» удалён", directory=True)
        self.page.update()

    def zakrit_okno(self, event=None):
        self.page.pop_dialog()

    def smenit_stranicu(self, event):
        selected = event.control.selected_index
        for index, view in self.stranici.items():
            view.visible = index == selected
        if selected == 4:
            self.obnovit_otcheti()
        self.page.update()

    def smenit_temu(self, event=None):
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.LIGHT_MODE
            self.theme_button.tooltip = "Светлая тема"
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.DARK_MODE
            self.theme_button.tooltip = "Тёмная тема"
        self.page.update()

    def obnovit_otcheti_knopkoy(self, event=None):
        self.zagruzit_dannie()
        self.page.update()

    async def chasi(self):
        while not self.zakrita:
            now = datetime.now()
            self.date_text.value = now.strftime("%d.%m.%Y")
            self.time_text.value = now.strftime("%H:%M:%S")
            try:
                self.page.update()
            except Exception:
                return
            await asyncio.sleep(1)

    def zakrit_programmu(self, event=None):
        if self.zakrita:
            return
        self.otchet.sohranit()
        self.baza.zakrit()
        self.zakrita = True


if __name__ == "__main__":
    ft.run(SkladProga.zapusk)
