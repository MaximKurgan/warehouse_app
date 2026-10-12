import ast
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from baza import Baza
from modeli import Kategoriya, Tovar, Prihod, Postavshik, Spisanie
from spisok_par import SpisokPar
from otchet import Otchet


class Proverka(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_directory.name)
        self.database = Baza(self.directory / "test.db")

    def tearDown(self):
        self.database.zakrit()
        self.temp_directory.cleanup()

    def test_entities_are_validated_and_comparable(self):
        first = Kategoriya("А")
        second = Kategoriya("Б")
        self.assertLess(first, second)
        self.assertEqual(first, Kategoriya("а"))
        self.assertTrue(str(first))
        self.assertTrue(repr(first))
        with self.assertRaises(ValueError):
            Tovar("", "Товар", "Категория", "Поставщик", 1, 1)

    def test_custom_mapping(self):
        values = SpisokPar()
        values["first"] = 1
        values["second"] = 2
        values["first"] = 3
        self.assertEqual(values["first"], 3)
        self.assertEqual(len(values), 2)

    def test_crud_and_atomic_operations(self):
        category = Kategoriya("Категория")
        supplier = Postavshik("Поставщик")
        self.database.dobavit_kategoriyu(category)
        self.database.dobavit_postavshika(supplier)
        product = Tovar("A-1", "Товар", category.nazvanie, supplier.nazvanie, 5, 10)
        self.database.sozdat_tovar(product)
        self.database.provesti_operaciyu(
            product, Prihod(product.artikul, product.nazvanie, 2)
        )
        self.database.provesti_operaciyu(
            product, Spisanie(product.artikul, product.nazvanie, 1)
        )
        self.assertEqual(product.kolichestvo, 6)
        with self.assertRaises(ValueError):
            self.database.provesti_operaciyu(
                product, Spisanie(product.artikul, product.nazvanie, 99)
            )
        stored = self.database.connection.execute(
            "SELECT quantity FROM products WHERE article = ?", (product.artikul,)
        ).fetchone()[0]
        self.assertEqual(stored, 6)
        self.assertEqual(self.database.proverka_bazi(), "ok")

    def test_session_report_format(self):
        report = Otchet(
            self.directory / "report.txt",
            "Student",
            datetime(2026, 10, 9, 10, 0, 0),
        )
        report.sohranit(datetime(2026, 10, 9, 11, 0, 0))
        text = report.put_k_otchetu.read_text(encoding="utf-8")
        self.assertIn("09.10.2026 10:00:00", text)
        self.assertIn("09.10.2026 11:00:00", text)

    def test_no_mapping_literals_in_application_files(self):
        root = Path(__file__).resolve().parent.parent / "src"
        names = (
            "main.py", "sklad_proga.py", "modeli.py", "baza.py",
            "spisok_par.py", "otchet.py", "elementi.py",
        )
        for name in names:
            tree = ast.parse((root / name).read_text(encoding="utf-8"))
            count = sum(isinstance(node, ast.Dict) for node in ast.walk(tree))
            self.assertEqual(count, 0, name)


if __name__ == "__main__":
    unittest.main()
