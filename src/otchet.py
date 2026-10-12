# отчет о входе и выходе

import getpass
from datetime import datetime
from pathlib import Path

from modeli import Sushnost


class Otchet(Sushnost):
    #данные 1 запуска

    TIME_FORMAT = "%d.%m.%Y %H:%M:%S"

    def __init__(self, put_k_otchetu, login=None, vremya_vhoda=None):
        self.put_k_otchetu = put_k_otchetu
        self.login = login or getpass.getuser()
        self.vremya_vhoda = vremya_vhoda or datetime.now()
        self.vremya_vihoda = None

    @property
    def put_k_otchetu(self):
        return self._put_k_otchetu

    @put_k_otchetu.setter
    def put_k_otchetu(self, value):
        self._put_k_otchetu = Path(value).resolve()

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Логин не может быть пустым")
        self._login = text

    @property
    def vremya_vhoda(self):
        return self._vremya_vhoda

    @vremya_vhoda.setter
    def vremya_vhoda(self, value):
        if not isinstance(value, datetime):
            raise TypeError("vremya_vhoda должен иметь тип datetime")
        self._vremya_vhoda = value

    @property
    def vremya_vihoda(self):
        return self._vremya_vihoda

    @vremya_vihoda.setter
    def vremya_vihoda(self, value):
        if value is not None and not isinstance(value, datetime):
            raise TypeError("vremya_vihoda должен иметь тип datetime или None")
        self._vremya_vihoda = value

    @property
    def znacheniya_dlya_sravneniya(self):
        return (self.login.casefold(), self.vremya_vhoda)

    @property
    def tekst_dlya_pokaza(self):
        return f"Сеанс {self.login}"

    @property
    def znachenie_dlya_sortirovki(self):
        return (self.vremya_vhoda, self.login.casefold())

    @staticmethod
    def format_vremeni(value):
        return value.strftime(Otchet.TIME_FORMAT)

    def sobrat_otchet(self):
        end_time = self.vremya_vihoda or datetime.now()
        login = self.login[:16]
        vremya_vhoda = self.format_vremeni(self.vremya_vhoda)
        vremya_vihoda = self.format_vremeni(end_time)
        border = "+------------------+---------------------+---------------------+"
        return "\n".join(
            (
                border,
                "| login            | time_in             | time_out            |",
                "+------------------+---------------------+---------------------+",
                f"| {login:<16} | {vremya_vhoda:<19} | {vremya_vihoda:<19} |",
                border,
            )
        )

    def sohranit(self, vremya_vihoda=None):
        self.vremya_vihoda = vremya_vihoda or datetime.now()
        self.put_k_otchetu.write_text(self.sobrat_otchet() + "\n", encoding="utf-8")
        return self.put_k_otchetu
