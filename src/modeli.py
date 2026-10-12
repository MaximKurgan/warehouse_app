#классы для склада

from abc import ABC, abstractmethod
from datetime import datetime
from functools import total_ordering


@total_ordering
class Sushnost(ABC):
    #общий класс для всех сущностей

    @property
    @abstractmethod
    def znacheniya_dlya_sravneniya(self):
        pass

    @property
    @abstractmethod
    def tekst_dlya_pokaza(self):
        pass

    @property
    @abstractmethod
    def znachenie_dlya_sortirovki(self):
        pass

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self.znacheniya_dlya_sravneniya == other.znacheniya_dlya_sravneniya

    def __lt__(self, other):
        if type(self) is not type(other):
            return self.__class__.__name__ < other.__class__.__name__
        return self.znachenie_dlya_sortirovki < other.znachenie_dlya_sortirovki

    def __repr__(self):
        values = ", ".join(repr(value) for value in self.znacheniya_dlya_sravneniya)
        return f"{self.__class__.__name__}({values})"

    def __str__(self):
        return self.tekst_dlya_pokaza

    def __hash__(self):
        return hash((self.__class__.__name__, self.znacheniya_dlya_sravneniya))

    def __bool__(self):
        return bool(self.tekst_dlya_pokaza.strip())


class SushnostSNazvaniem(Sushnost):
    def __init__(self, nazvanie):
        self.nazvanie = nazvanie

    @property
    def nazvanie(self):
        return self._name

    @nazvanie.setter
    def nazvanie(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Название не может быть пустым")
        self._name = text

    @property
    def znacheniya_dlya_sravneniya(self):
        return (self.nazvanie.casefold(),)

    @property
    def tekst_dlya_pokaza(self):
        return self.nazvanie

    @property
    def znachenie_dlya_sortirovki(self):
        return self.nazvanie.casefold()


class Kategoriya(SushnostSNazvaniem):
    pass


class Postavshik(SushnostSNazvaniem):
    pass


class Tovar(Sushnost):
    def __init__(self, artikul, nazvanie, kategoriya, postavshik, kolichestvo, cena):
        self.artikul = artikul
        self.nazvanie = nazvanie
        self.kategoriya = kategoriya
        self.postavshik = postavshik
        self.kolichestvo = kolichestvo
        self.cena = cena

    @property
    def artikul(self):
        return self._article

    @artikul.setter
    def artikul(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Артикул не может быть пустым")
        self._article = text

    @property
    def nazvanie(self):
        return self._name

    @nazvanie.setter
    def nazvanie(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Название товара не может быть пустым")
        self._name = text

    @property
    def kategoriya(self):
        return self._category

    @kategoriya.setter
    def kategoriya(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Категория не может быть пустой")
        self._category = text

    @property
    def postavshik(self):
        return self._supplier

    @postavshik.setter
    def postavshik(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Поставщик не может быть пустым")
        self._supplier = text

    @property
    def kolichestvo(self):
        return self._quantity

    @kolichestvo.setter
    def kolichestvo(self, value):
        number = int(value)
        if number < 0:
            raise ValueError("Кол-во не может быть отрицательным")
        self._quantity = number

    @property
    def cena(self):
        return self._price

    @cena.setter
    def cena(self, value):
        number = float(value)
        if number < 0:
            raise ValueError("Цена не может быть отрицательной")
        self._price = number

    @property
    def znacheniya_dlya_sravneniya(self):
        return (self.artikul.casefold(),)

    @property
    def tekst_dlya_pokaza(self):
        return f"{self.artikul} - {self.nazvanie}"

    @property
    def znachenie_dlya_sortirovki(self):
        return (self.nazvanie.casefold(), self.artikul.casefold())

    def obshaya_stoimost(self):
        return self.kolichestvo * self.cena


class SkladskayaOperaciya(Sushnost, ABC):
    #от этого класса идут приход и списание

    DATE_FORMAT = "%d.%m.%Y %H:%M:%S"

    def __init__(self, artikul, nazvanie_tovara, kolichestvo, data_operacii=None):
        self.artikul = artikul
        self.nazvanie_tovara = nazvanie_tovara
        self.kolichestvo = kolichestvo
        self.data_operacii = data_operacii or datetime.now().strftime(
            self.DATE_FORMAT
        )

    @property
    def artikul(self):
        return self._article

    @artikul.setter
    def artikul(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Артикул операции не может быть пустым")
        self._article = text

    @property
    def nazvanie_tovara(self):
        return self._product_name

    @nazvanie_tovara.setter
    def nazvanie_tovara(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Название товара не может быть пустым")
        self._product_name = text

    @property
    def kolichestvo(self):
        return self._quantity

    @kolichestvo.setter
    def kolichestvo(self, value):
        number = int(value)
        if number <= 0:
            raise ValueError("Количество операции должно быть больше нуля")
        self._quantity = number

    @property
    def data_operacii(self):
        return self._operation_date

    @data_operacii.setter
    def data_operacii(self, value):
        text = str(value).strip()
        if not text:
            raise ValueError("Дата операции не может быть пустой")
        self._operation_date = text

    @property
    @abstractmethod
    def tip_operacii(self):
        pass

    @abstractmethod
    def primenit(self, product):
        pass

    @property
    def znacheniya_dlya_sravneniya(self):
        return (
            self.artikul.casefold(),
            self.nazvanie_tovara.casefold(),
            self.tip_operacii,
            self.kolichestvo,
            self.data_operacii,
        )

    @property
    def tekst_dlya_pokaza(self):
        return f"{self.tip_operacii}: {self.nazvanie_tovara} ({self.kolichestvo})"

    @property
    def znachenie_dlya_sortirovki(self):
        return (self.data_operacii, self.artikul.casefold())

    def kolichestvo_tekstom(self):
        return str(self.kolichestvo)


class Prihod(SkladskayaOperaciya):
    @property
    def tip_operacii(self):
        return "Приход"

    def primenit(self, product):
        product.kolichestvo += self.kolichestvo

    def kolichestvo_tekstom(self):
        return f"+{self.kolichestvo}"


class Spisanie(SkladskayaOperaciya):
    @property
    def tip_operacii(self):
        return "Списание"

    def primenit(self, product):
        if self.kolichestvo > product.kolichestvo:
            raise ValueError("Недостаточно товара на складе")
        product.kolichestvo -= self.kolichestvo

    def kolichestvo_tekstom(self):
        return f"-{self.kolichestvo}"
