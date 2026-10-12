# тут работа с базой

import sqlite3
from pathlib import Path

from modeli import (
    Kategoriya,
    Tovar,
    Prihod,
    Postavshik,
    Spisanie,
)


class Baza:
    # все запросы к sqlite

    def __init__(self, db_name=None):
        default_path = Path(__file__).resolve().parent / "sklad.db"
        self.db_path = Path(db_name) if db_name else default_path
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.sozdat_tablici()
        self.proverit_staruyu_bazu()
        self.zapolnit_spravochniki()

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, value):
        self._db_path = Path(value).resolve()

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.zakrit()
        return False

    def __repr__(self):
        return f"Baza({str(self.db_path)!r})"

    def __str__(self):
        return f"База склада: {self.db_path.name}"

    def __len__(self):
        return self.connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

    def __bool__(self):
        return self.connection is not None

    def sozdat_tablici(self):
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL DEFAULT 'Без категории',
                supplier TEXT NOT NULL DEFAULT 'Не указан'
            );

            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT NOT NULL,
                product_name TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                operation_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            """
        )
        self.connection.commit()

    def proverit_staruyu_bazu(self):
        columns = self.connection.execute("PRAGMA table_info(products)").fetchall()
        column_names = [column[1] for column in columns]
        if "category" not in column_names:
            self.connection.execute(
                "ALTER TABLE products ADD COLUMN category TEXT "
                "NOT NULL DEFAULT 'Без категории'"
            )
        if "supplier" not in column_names:
            self.connection.execute(
                "ALTER TABLE products ADD COLUMN supplier TEXT "
                "NOT NULL DEFAULT 'Не указан'"
            )
        self.connection.commit()

    def zapolnit_spravochniki(self):
        categories = self.connection.execute(
            "SELECT DISTINCT category FROM products"
        ).fetchall()
        suppliers = self.connection.execute(
            "SELECT DISTINCT supplier FROM products"
        ).fetchall()
        for row in categories:
            if row[0]:
                self.connection.execute(
                    "INSERT OR IGNORE INTO categories (name) VALUES (?)", row
                )
        for row in suppliers:
            if row[0]:
                self.connection.execute(
                    "INSERT OR IGNORE INTO suppliers (name) VALUES (?)", row
                )
        self.connection.commit()

    def dobavit_kategoriyu(self, category):
        self.connection.execute(
            "INSERT INTO categories (name) VALUES (?)", (category.nazvanie,)
        )
        self.connection.commit()

    def poluchit_kategorii(self):
        rows = self.connection.execute(
            "SELECT name FROM categories ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [Kategoriya(row[0]) for row in rows]

    def izmenit_kategoriyu(self, old_name, new_name):
        with self.connection:
            self.connection.execute(
                "UPDATE categories SET name = ? WHERE name = ?",
                (new_name, old_name),
            )
            self.connection.execute(
                "UPDATE products SET category = ? WHERE category = ?",
                (new_name, old_name),
            )

    def kategoriya_ispolzuetsya(self, name):
        count = self.connection.execute(
            "SELECT COUNT(*) FROM products WHERE category = ?", (name,)
        ).fetchone()[0]
        return count > 0

    def udalit_kategoriyu(self, name):
        self.connection.execute("DELETE FROM categories WHERE name = ?", (name,))
        self.connection.commit()

    def dobavit_postavshika(self, supplier):
        self.connection.execute(
            "INSERT INTO suppliers (name) VALUES (?)", (supplier.nazvanie,)
        )
        self.connection.commit()

    def poluchit_postavshikov(self):
        rows = self.connection.execute(
            "SELECT name FROM suppliers ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [Postavshik(row[0]) for row in rows]

    def izmenit_postavshika(self, old_name, new_name):
        with self.connection:
            self.connection.execute(
                "UPDATE suppliers SET name = ? WHERE name = ?",
                (new_name, old_name),
            )
            self.connection.execute(
                "UPDATE products SET supplier = ? WHERE supplier = ?",
                (new_name, old_name),
            )

    def postavshik_ispolzuetsya(self, name):
        count = self.connection.execute(
            "SELECT COUNT(*) FROM products WHERE supplier = ?", (name,)
        ).fetchone()[0]
        return count > 0

    def udalit_postavshika(self, name):
        self.connection.execute("DELETE FROM suppliers WHERE name = ?", (name,))
        self.connection.commit()

    def sozdat_tovar(self, product):
        # сразу записываем первый приход
        with self.connection:
            self._zapisat_tovar(product)
            if product.kolichestvo > 0:
                operation = Prihod(
                    product.artikul, product.nazvanie, product.kolichestvo
                )
                self._zapisat_operaciyu(operation)

    def dobavit_tovar(self, product):
        self._zapisat_tovar(product)
        self.connection.commit()

    def _zapisat_tovar(self, product):
        self.connection.execute(
            """
            INSERT INTO products
                (article, name, quantity, price, category, supplier)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product.artikul,
                product.nazvanie,
                product.kolichestvo,
                product.cena,
                product.kategoriya,
                product.postavshik,
            ),
        )

    def poluchit_tovari(self):
        rows = self.connection.execute(
            """
            SELECT article, name, category, supplier, quantity, price
            FROM products
            ORDER BY id
            """
        ).fetchall()
        return [Tovar(*row) for row in rows]

    def izmenit_tovar(self, old_article, product):
        self.connection.execute(
            """
            UPDATE products
            SET article = ?, name = ?, category = ?, supplier = ?,
                quantity = ?, price = ?
            WHERE article = ?
            """,
            (
                product.artikul,
                product.nazvanie,
                product.kategoriya,
                product.postavshik,
                product.kolichestvo,
                product.cena,
                old_article,
            ),
        )
        self.connection.commit()

    def udalit_tovar(self, article):
        self.connection.execute("DELETE FROM products WHERE article = ?", (article,))
        self.connection.commit()

    def dobavit_operaciyu(self, operation):
        self._zapisat_operaciyu(operation)
        self.connection.commit()

    def _zapisat_operaciyu(self, operation):
        self.connection.execute(
            """
            INSERT INTO operations
                (article, product_name, operation_type, quantity, operation_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                operation.artikul,
                operation.nazvanie_tovara,
                operation.tip_operacii,
                operation.kolichestvo,
                operation.data_operacii,
            ),
        )

    def provesti_operaciyu(self, product, operation):
        # остаток и операция сохраняются вместе
        old_quantity = product.kolichestvo
        try:
            operation.primenit(product)
            with self.connection:
                self.connection.execute(
                    "UPDATE products SET quantity = ? WHERE article = ?",
                    (product.kolichestvo, product.artikul),
                )
                self._zapisat_operaciyu(operation)
        except Exception:
            product.kolichestvo = old_quantity
            raise

    def poluchit_operacii(self):
        rows = self.connection.execute(
            """
            SELECT article, product_name, operation_type, quantity, operation_date
            FROM operations
            ORDER BY id DESC
            """
        ).fetchall()
        operations = []
        for row in rows:
            operation_class = (
                Prihod if row[2] == "Приход" else Spisanie
            )
            if row[2] in ("Приход", "Списание"):
                operations.append(
                    operation_class(row[0], row[1], row[3], row[4])
                )
        return operations

    def proverka_bazi(self):
        return self.connection.execute("PRAGMA integrity_check").fetchone()[0]

    def zakrit(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
