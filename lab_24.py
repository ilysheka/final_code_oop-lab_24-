# Контроль влажности в музеях. 
# Предметная область: Сохранение культурного наследия.
# Функционал: Мониторинг влажности для каждого экспоната (у каждого свои требования), 
# запись истории климата в журнал, оповещение куратора о критических рисках. 
# Возможные сущности: Гигрометр, Экспонат, Климатический сценарий, Куратор

# Задания:
# • используйте агрегацию для манипулирования данными (добавление, изменение, 
# удаление и просмотр) основных классов сущностей, согласно варианта 
# индивидуального задания;
# • разработайте консольное приложение, использующее интерактивный режим с 
# пользователем, по манипулированию данных основных классов сущностей;
# • реализуйте функциональность, указанную в индивидуальном задании;
# • протестируйте корректность выполнения действий по манипулированию данными и 
# выполнение требуемых функций с помощью unittest.

from datetime import datetime
import time
import csv
import pickle
import os


file = 'journal.csv'
fio_curator = []
now_wet = 0
_time = None
_id = 0

def _next_id():
    '''
    Функция необходима для индексирования экспонатов
    '''
    global _id
    _id += 1
    return _id
def _date_now():
    '''
    Функция возвращает сегодняшнюю дату и время в глобальную переменную _time
    '''
    global _time
    now = datetime.now()
    month = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
             'августа', 'сентября', 'октября', 'ноября', 'декабря']
    _time = f'{now.day} {month[now.month - 1]} {now.year} {now.hour}:{now.minute}'
    return _time

def time_decorator(func):
    '''Декоратор для вывода времени выполнения метода'''
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'[Log] Метод {func.__name__} выполнялся {end_time - start_time:.4f} сек.')
        return result
    return wrapper

def counter_decorator(func):
    '''Декоратор для подсчёта количества вызовов метода'''
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        print(f'[Log] Метод {func.__name__} был вызван {wrapper.calls} раз(а)')
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper


def main():
    app = MuseumTerminal()
    app.run()

class MuseumDatabase:
    '''Контейнер для агрегации объектов Экспонатов'''
    def __init__(self):
        self.database = {}
        self._keys = []
        self._index = 0

    def add_exponate(self, exponate):
        self.database[exponate.name_exp.lower()] = exponate

    def get_exponate(self, name):
        return self.database.get(name.lower())

    def delete_exponate(self, name):
        key = name.lower()
        if key in self.database:
            del self.database[key]
            return True
        return False

    def __len__(self):
        return len(self.database)

    # Реализация Итератора
    def __iter__(self):
        self._keys = list(self.database.keys())
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._keys):
            raise StopIteration
        item = self.database[self._keys[self._index]]
        self._index += 1
        return item

class MuseumTerminal:
    '''Консольное приложение для работы с классами-сущностями'''
    def __init__(self):
        self.db = MuseumDatabase()
        self.gigro = Gigrometr()
        self.curator = Curator()
        self.climate = ClimateScenary()
        
    def setup(self):
        if not os.path.exists('objects.pkl'):
            print("Первый запуск программы. Настройка системы.")
            self.curator.question_about_fio_cur()
            
            coin = MaterialExponate('монетка')
            ancient_book = WrittenExponate('древняя книга')
            art = ArtExponate('Мона Лиза')
            ancient_shell = PaleontologyExponate('древняя ракушка')
            
            for exp in [coin, ancient_book, art, ancient_shell]:
                exp.question_about_max_wet()
                self.db.add_exponate(exp)
                
            self.check_climate_risks()
            MuseumSystem.serialize([self.gigro, self.curator, self.climate, self.db])
        else:
            global _id
            objects = MuseumSystem.deserialize()
            self.gigro, self.curator, self.climate, self.db, _id = objects
            self.climate.now_time = _date_now()

    def print_db(self):
        if len(self.db) == 0:
            print("Экспонатов пока нет.")
            return
        print("\n--- Список экспонатов ---")
        # Здесь негласно вызывается метод __iter__ и __next__ из MuseumDatabase
        for exp in self.db:
            print(exp)
        print("-------------------------")

    def add_exponate_dialog(self):
        types_exp = {'1': MaterialExponate, '2': ArtExponate, '3': WrittenExponate, '4': PaleontologyExponate}
        print('\nВыберите вид экспоната\n1 - материальный\n2 - рисованный\n3 - рукописный\n4 - палеонтологический')
        type_exp = input('Ваш ответ (введите цифру): ')
        
        if type_exp not in types_exp:
            print("Неверный тип.")
            return

        name = input('Введите название экспоната: ')
        if name == '' or not any(char.isalpha() for char in name):
            raise ExponateNameError(name)
            
        new_exponate = types_exp[type_exp](name)
        new_exponate.input_info()
        new_exponate.question_about_max_wet()
        self.db.add_exponate(new_exponate)
        print(f"Экспонат '{name}' успешно добавлен.")

    def delete_exponate_dialog(self):
        name = input('Введите название экспоната для удаления: ')
        if self.db.delete_exponate(name):
            print(f'Экспонат "{name}" удален.')
        else:
            print(f'Экспонат "{name}" не найден.')

    def change_exponate_dialog(self):
        name = input('Введите название экспоната для изменения влажности: ')
        exp = self.db.get_exponate(name)
        if exp:
            exp.question_about_max_wet()
            print("Данные обновлены.")
        else:
            print("Экспонат не найден.")

    def check_climate_risks(self):
        current_wet = self.gigro.check_wet()
        exponates_in_danger = []
        
        for exp in self.db:
            exp.check_crit(exponates_in_danger)
            
        if exponates_in_danger:
            print('ВНИМАНИЕ! Есть экспонаты в опасности! Уведомите куратора:')
            print(self.curator)
            
        self.climate.danger_list = exponates_in_danger
        self.climate.save_to_csv()

    def run(self):
        self.setup()
        
        # Словарь действий через lambda-функции
        choices = {
            1: lambda: self.print_db(),
            2: lambda: self.add_exponate_dialog(),
            3: lambda: self.delete_exponate_dialog(),
            4: lambda: self.change_exponate_dialog(),
            5: lambda: print(self.climate),
            6: lambda: self.check_climate_risks(),
            7: lambda: self.climate.get_transaction(),
            0: lambda: print("Выход из системы. Данные сохранены.")
        }
        
        choice = -1
        while choice != 0:
            print("\n================ МЕНЮ ================")
            print("1. Просмотр всех экспонатов (iterator)")
            print("2. Добавить экспонат")
            print("3. Удалить экспонат")
            print("4. Изменить макс. влажность экспоната")
            print("5. Последняя запись в журнале климата")
            print("6. Замерить влажность и проверить риски")
            print("7. История журнала (транзакции)")
            print("0. ВЫХОД")
            try:
                choice = int(input("Выберите пункт меню: "))
                if choice in choices:
                    choices[choice]()
                else:
                    print("Введен некорректный пункт меню.")
            except ValueError:
                print("Пожалуйста, введите число.")
            except Exception as e:
                print(f"Произошла ошибка: {e}")
        
        global _id
        MuseumSystem.serialize([self.gigro, self.curator, self.climate, self.db, _id])

class Gigrometr:
    '''
    Гигрометр необходим для измерения влажности в помещении(музее). 
    Обладает атрибутом влажность(_wet) и методом проверить влажность(check_wet)
    '''
    def __init__(self, wet = 0):
        self._wet = wet

    @counter_decorator
    def check_wet(self):
        '''
        Ввод влажности в атрибут wet
        '''
        global now_wet
        try:
            now_wet = int(input('Проверьте влажность на гигрометре и введите текущую влажность: '))
            self.wet = now_wet
            return now_wet
        except ValueError:  # ошибка преобразования в int
            print('Введены некорректные данные (не число). Попробуем снова!')
            return self.check_wet()
        except WetValueError as e: # ошибка в вводе(от 0 до 100)
            print(f'{e.message}. Попробуем снова!')
            return self.check_wet()

    @property #геттер
    def wet(self):
        return self._wet

    @wet.setter #сеттер
    def wet(self, value):
        '''
        Метод необходим для корректного ввода влажности
        '''
        if not isinstance(value, int):
            raise TypeError('Влажность может быть только числом')
        elif not(0 <= value and value < 100):
            raise WetValueError(value)
        self._wet = value


class Stack:
    '''
    Динамическая структура данных - стек. Необходим для получения последней записи в журнале.
    '''
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if len(self.items) > 0:
            return self.items.pop()
        return None

    def top(self):
        if len(self.items) > 0:
            return self.items[-1]
        return None


class ClimateScenary:
    '''
    Климатический сценарий необходим для сохранения и получения данных о влажности и экспонатах.
    Обладает атрибутами "дата и время в данный момент (now_time)", "название журнала(name_log)",
    "журнал"(log - стек), "список экспонатов в опасности"(danger_list),
    методами "сохранить в журнале(save_to_csv)", "получить все записи(транзакции)(get_transaction)",
    а также перегрузкой методов str и del.
    '''
    def __init__(self, danger_list=None):
        global file
        self.now_time = _date_now()
        self.name_log = file
        self.log = Stack()
        self.danger_list = danger_list if danger_list is not None else []

    def __str__(self):
        '''
        Выводит последнюю запись в журнале
        '''
        last_node = self._last_node()
        if last_node is not None:
            info = last_node.get('Экспонаты в опасности', '')
            if info != 'нет':
                output = f"Последняя запись в журнале:\n{last_node.get('Время', '')} влажность составляла {last_node.get('Влажность', '')}%, что критично для {last_node.get('Экспонаты в опасности', '')}"
            else:
                output = f"Последняя запись в журнале:\n{last_node.get('Время', '')} влажность составляла {last_node.get('Влажность', '')}%, экспонатов в опасности нет"
            return output
        return 'Записей пока нет'

    def _last_node(self):
        try:
            with open(self.name_log, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i in reader:
                    self.log.push(i)
            return self.log.top()
        except:
            return None

    @time_decorator
    def save_to_csv(self):
        '''
        Сохраняет запись об экспонатах в опасности, влажности и экспонатах в опасности в журнале
        '''
        global now_wet
        if not self.danger_list:
            self.danger_list = ['нет']
        self._save_to_csv()

    def _save_to_csv(self):
        try:
            data = {
                'Время': self.now_time,
                'Влажность': now_wet,
                'Экспонаты в опасности': ', '.join(self.danger_list)
            }
            with open(self.name_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f,
                                        fieldnames=data.keys())  # Ключи словаря используются как названия колонок, в нашем случае - self.now_time
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow(data)
        except:
            return False

    def get_transaction(self):
        '''
        Метод необходим для получения транзакций
        '''
        if self.log.top() is None:
            self._last_node()

        while self.log.top() is not None:
            node = self.log.pop()
            info = node.get('Экспонаты в опасности', '')
            if info != 'нет':
                output = f"\n{node.get('Время', '')} влажность составляла {node.get('Влажность', '')}%, что критично для {node.get('Экспонаты в опасности', '')}"
            else:
                output = f"\n{node.get('Время', '')} влажность составляла {node.get('Влажность', '')}%, экспонатов в опасности нет"
            print(output)

    def __del__(self):
        print(f'Объект ClimateScenary удалён. Журнал: {self.name_log}')


class Person:
    '''Класс, хранящий личные данные человека'''
    def __init__(self, f_name=None, s_name=None, o_name=None):
        self.f_name = f_name
        self.s_name = s_name
        self.o_name = o_name

class Curator:
    '''
    Класс для сохранения информации о кураторе.
    Обладает атрибутами: ФИО куратора(first name - fname_cur, second name - sname_cur, surname - ot_cur)
    а также методом "вопрос о ФИО куратора(question_about_fio_cur)"
    '''
    def __init__(self, f_cur=None, s_cur=None, o_cur=None):
        # Ассоциация: класс Curator использует класс Person для хранения данных
        self.person = Person(f_cur, s_cur, o_cur)

    def __str__(self):
        return 'Вашего куратора зовут {0} {1} {2}'.format(self.person.f_name, self.person.s_name, self.person.o_name)

    @time_decorator
    def question_about_fio_cur(self):
        try:
            f, s, o = input('Введите ФИО куратора: ').split()
            self.person.f_name = f
            self.person.s_name = s
            self.person.o_name = o
        except:
            print('Неверный ввод данных. Повторим!')
            return self.question_about_fio_cur()

        global fio_curator
        fio_curator.append(self.person.f_name)
        fio_curator.append(self.person.s_name)
        fio_curator.append(self.person.o_name)
        return ' '.join(fio_curator)


class Exponate:
    '''
    Экспонат в музее.
    Обладает атрибутами: название экспоната(name_exp), максимальная влажность(_max_wet), Id экспоната(_id)
    а также методами "вопрос о максимальной влажности экспоната(question_about_max_wet)"
    и "проверить критическую влажность, т.е. влажность в данный момент превышает ли максимальную экспоната(check_crit)".
    Является родительским классом для следующих
    '''
    def __init__(self, name_exp, max_wet = 100):
        '''
        Экспонат с названием и максимальной влажностью
        '''
        self.name_exp = name_exp
        self._max_wet = max_wet
        self._id = _next_id()

    def __str__(self):
        return 'Экспонат "{0}" имеет максимальную допустимую влажность {1}%'.format(self.name_exp, self.max_wet)
    
    def __add__(self, other_exponate):
        return min(self.max_wet, other_exponate.max_wet)

    @property  # геттер
    def max_wet(self):
        return self._max_wet

    @max_wet.setter  # сеттер
    def max_wet(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError('Влажность может быть только числом')
        elif not (0 <= value and value < 100):
            raise WetValueError(value)
        self._max_wet = value

    @counter_decorator
    def question_about_max_wet(self):
        '''
        Ввод максимальной допустимой влажности в атрибут max_wet
        '''
        try:
            value = int(
                input(f'Спросите у куратора, какова наибольшая влажность у экспоната "{self.name_exp}", и напишите: '))
            self.max_wet = value
        except:
            print('Данные введены некорректно. Повторим')
            self.question_about_max_wet()
        return self.max_wet

    def check_crit(self, danger_list):
        global now_wet
        if now_wet > self.max_wet:
            danger_list.append(self.name_exp)


class MaterialExponate(Exponate):
    '''
    Экспонаты, созданные древними людьми(инструменты, посуда, и тд.).
    Дочерний класс от Exponate.
    Дополняется атрибутом материал(material) и изменяет метод check_crit(в основном вывод).
    Для полиморфизма добавлен метод input_info(в следующих он также добавлен)
    '''

    def __init__(self, name_exp, mat='железо'):
        super().__init__(name_exp)
        self.material = mat

    def __str__(self):
        return f'[ID: {self._id}] Материальный экспонат "{self.name_exp}" из материала {self.material} имеет максимальную допустимую влажность {self.max_wet}%'

    def input_info(self):
        try:
            self.material = input('Введите материал, из которого создан экспонат: ')
        except:
            print('Данные введены некорректно. Повторим')
            return self.input_info()
        return self.material


class ArtExponate(Exponate):
    '''
    Рисунки людей любой эпохи.
    Дочерний класс от Exponate.
    Дополняется атрибутом объект рисунка(art_object) и изменяет метод check_crit(в основном вывод).
    '''

    def __init__(self, name_exp, art='женщина'):
        super().__init__(name_exp)
        self.art_object = art

    def __str__(self):
        return f'[ID: {self._id}] Экспонат искусства "{self.name_exp}" с изображением "{self.art_object}" имеет максимальную допустимую влажность {self.max_wet}%'

    def input_info(self):
        try:
            self.art_object = input('Введите то, что изображено на экспонате: ')
        except:
            print('Данные введены некорректно. Повторим')
            return self.input_info()
        return self.art_object


class WrittenExponate(Exponate):
    '''
    Рукописные экспонаты людей любой эпохи.
    Дочерний класс от Exponate.
    Дополняется атрибутом язык, на котором написан текст(language) и изменяет метод check_crit(в основном вывод).
    '''

    def __init__(self, name_exp, lang='русский'):
        super().__init__(name_exp)
        self.language = lang

    def __str__(self):
        return f'[ID: {self._id}] Рукописный экспонат "{self.name_exp}" на языке {self.language} имеет максимальную допустимую влажность {self.max_wet}%'

    def input_info(self):
        try:
            self.language = input('Введите язык, на котором написан экспонат: ')
        except:
            print('Данные введены некорректно. Повторим')
            return self.input_info()
        return self.language


class PaleontologyExponate(Exponate):
    '''
    Палеонтологические экспонаты - кости, скелеты животных, динозавров.
    Дочерний класс от Exponate.
    Дополняется атрибутом возраст(age) и изменяет метод check_crit(в основном вывод).
    '''

    def __init__(self, name_exp, a='1000'):
        super().__init__(name_exp)
        self.age = a

    def __str__(self):
        return f'[ID: {self._id}] Палеонтологический экспонат "{self.name_exp}" с возрастом {self.age} лет имеет максимальную допустимую влажность {self.max_wet}%'

    def input_info(self):
        try:
            self.age = input('Введите возраст экспоната: ')
        except:
            print('Данные введены некорректно. Повторим')
            return self.input_info()
        return self.age


class MuseumSystem:
    @staticmethod
    def serialize(objects):
        with open('objects.pkl', 'wb') as f:
            pickle.dump(objects, f)

    @staticmethod
    def deserialize():
        with open('objects.pkl', 'rb') as f:
            objects = pickle.load(f)
        return objects

    @staticmethod
    def deserialize():
        '''
        Десериализируем все объекты
        '''
        with open('objects.pkl', 'rb') as f:
            objects = pickle.load(f)
        return objects

class WetValueError(Exception):
    '''
    Исключение для влажности
    '''
    def __init__(self, value, message='Некорректное значение влажности'):
        self.message = f'{message}: {value}. Влажность должна быть в пределе от 0 до 100'
        super().__init__(self.message)

class ExponateNameError(Exception):
    '''
    Исключение для некорректного названия экспоната
    '''
    def __init__(self, name, message='Некорректное название экспоната'):
        self.message = f'{message}: "{name}". Название не может быть пустым или содержать только цифры'
        super().__init__(self.message)


if __name__ == '__main__':
    main()