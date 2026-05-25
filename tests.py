from lab_24 import (Gigrometr, Curator, Stack, ClimateScenary, 
                    Exponate, MuseumSystem, MaterialExponate, 
                    ArtExponate, WrittenExponate, PaleontologyExponate,
                    WetValueError, ExponateNameError, MuseumDatabase)
import unittest
import os
import pickle
import csv

# Импортируем глобальные переменные из модуля
import lab_24


class TestStack(unittest.TestCase):
    """Тесты для класса Stack"""
    
    def setUp(self):
        self.stack = Stack()
    
    def test_push_one_item(self):
        self.stack.push(10)
        self.assertEqual(self.stack.items, [10])
    
    def test_push_multiple_items(self):
        self.stack.push(1)
        self.stack.push(2)
        self.stack.push(3)
        self.assertEqual(self.stack.items, [1, 2, 3])
    
    def test_pop_from_non_empty_stack(self):
        self.stack.push(10)
        self.stack.push(20)
        result = self.stack.pop()
        self.assertEqual(result, 20)
        self.assertEqual(self.stack.items, [10])
    
    def test_pop_from_empty_stack(self):
        result = self.stack.pop()
        self.assertIsNone(result)
    
    def test_top_of_stack(self):
        self.stack.push(5)
        self.stack.push(15)
        result = self.stack.top()
        self.assertEqual(result, 15)
        self.assertEqual(self.stack.items, [5, 15])
    
    def test_top_from_empty_stack(self):
        result = self.stack.top()
        self.assertIsNone(result)
    
    def test_pop_all_items(self):
        for i in range(5):
            self.stack.push(i)
        
        for i in range(4, -1, -1):
            self.assertEqual(self.stack.pop(), i)
        
        self.assertIsNone(self.stack.pop())


class TestMuseumDatabase(unittest.TestCase):
    """Тесты для контейнера-агрегатора MuseumDatabase и его итератора"""
    
    def setUp(self):
        self.db = MuseumDatabase()
        self.exp1 = Exponate("Меч", 60)
        self.exp2 = Exponate("Картина", 50)

    def test_add_and_get_exponate(self):
        self.db.add_exponate(self.exp1)
        # Проверяем, что размер базы данных увеличился
        self.assertEqual(len(self.db), 1)
        
        # Получаем экспонат вне зависимости от регистра
        retrieved = self.db.get_exponate("мЕч")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name_exp, "Меч")

    def test_delete_exponate(self):
        self.db.add_exponate(self.exp1)
        self.db.add_exponate(self.exp2)
        
        # Удаляем существующий экспонат
        is_deleted = self.db.delete_exponate("Меч")
        self.assertTrue(is_deleted)
        self.assertEqual(len(self.db), 1)
        
        # Пытаемся удалить несуществующий
        is_deleted_fake = self.db.delete_exponate("Копье")
        self.assertFalse(is_deleted_fake)

    def test_iterator(self):
        self.db.add_exponate(self.exp1)
        self.db.add_exponate(self.exp2)
        
        extracted = []
        # Негласный вызов методов __iter__ и __next__
        for exp in self.db:
            extracted.append(exp.name_exp)
            
        self.assertEqual(len(extracted), 2)
        self.assertIn("Меч", extracted)
        self.assertIn("Картина", extracted)


class TestExponate(unittest.TestCase):
    """Тесты для класса Exponate"""
    
    def setUp(self):
        lab_24.now_wet = 50
        self.exponate = Exponate("Тестовый экспонат")
    
    def test_init(self):
        self.assertEqual(self.exponate.name_exp, "Тестовый экспонат")
        self.assertEqual(self.exponate._max_wet, 100)
    
    def test_set_max_wet_manually(self):
        self.exponate.max_wet = 75
        self.assertEqual(self.exponate.max_wet, 75)
    
    def test_str_without_max_wet(self):
        expected = 'Экспонат "Тестовый экспонат" имеет максимальную допустимую влажность 100%'
        self.assertEqual(str(self.exponate), expected)
    
    def test_str_with_max_wet(self):
        self.exponate.max_wet = 80
        expected = 'Экспонат "Тестовый экспонат" имеет максимальную допустимую влажность 80%'
        self.assertEqual(str(self.exponate), expected)
    
    def test_check_crit_dangerous(self):
        lab_24.now_wet = 80
        danger_list = []
        self.exponate.max_wet = 70
        self.exponate.check_crit(danger_list)
        self.assertIn(self.exponate.name_exp, danger_list)
    
    def test_check_crit_safe(self):
        lab_24.now_wet = 50
        danger_list = []
        self.exponate.max_wet = 70
        self.exponate.check_crit(danger_list)
        self.assertNotIn(self.exponate.name_exp, danger_list)
    
    def test_check_crit_equal_values(self):
        lab_24.now_wet = 70
        danger_list = []
        self.exponate.max_wet = 70
        self.exponate.check_crit(danger_list)
        self.assertNotIn(self.exponate.name_exp, danger_list)
    
    def test_multiple_exponates_check(self):
        lab_24.now_wet = 75
        danger_list = []
        
        exp1 = Exponate("Статуя")
        exp1.max_wet = 70
        exp2 = Exponate("Картина")
        exp2.max_wet = 80
        exp3 = Exponate("Ваза")
        exp3.max_wet = 65
        
        exp1.check_crit(danger_list)
        exp2.check_crit(danger_list)
        exp3.check_crit(danger_list)
        
        self.assertIn("Статуя", danger_list)
        self.assertNotIn("Картина", danger_list)
        self.assertIn("Ваза", danger_list)
        self.assertEqual(len(danger_list), 2)

    def test_exception_when_max_wet_negative(self):
        with self.assertRaises(WetValueError):
            self.exponate.max_wet = -10

    def test_exception_when_max_wet_greater_than_100(self):
        with self.assertRaises(WetValueError):
            self.exponate.max_wet = 150

    def test_exception_when_max_wet_not_number(self):
        with self.assertRaises(TypeError):
            self.exponate.max_wet = "не число"

    def test_set_max_wet_float(self):
        self.exponate.max_wet = 75.5
        self.assertEqual(self.exponate.max_wet, 75.5)


class TestMaterialExponate(unittest.TestCase):
    """Тесты для класса MaterialExponate"""
    
    def setUp(self):
        lab_24.now_wet = 50
        self.exponate = MaterialExponate("Меч", "бронза")
    
    def test_init(self):
        self.assertEqual(self.exponate.name_exp, "Меч")
        self.assertEqual(self.exponate.material, "бронза")
        self.assertEqual(self.exponate._max_wet, 100)
    
    def test_str(self):
        self.exponate.max_wet = 60
        # Возвращаем длинную фразу, которая прописана у вас в lab_24.py
        expected = 'Материальный экспонат "Меч" из материала бронза имеет максимальную допустимую влажность 60%'
        self.assertEqual(str(self.exponate), expected)
    
    def test_check_crit_dangerous(self):
        lab_24.now_wet = 80
        danger_list = []
        self.exponate.max_wet = 70
        self.exponate.check_crit(danger_list)
        self.assertIn("Меч", danger_list)


class TestCurator(unittest.TestCase):
    """Тесты для класса Curator"""
    
    def test_init_with_params(self):
        curator = Curator("Иван", "Петров", "Сидорович")
        self.assertEqual(curator.person.f_name, "Иван")
        self.assertEqual(curator.person.s_name, "Петров")
        self.assertEqual(curator.person.o_name, "Сидорович")
    
    def test_init_without_params(self):
        curator = Curator()
        self.assertIsNone(curator.person.f_name)
        self.assertIsNone(curator.person.s_name)
        self.assertIsNone(curator.person.o_name)
    
    def test_str_with_name(self):
        curator = Curator("Мария", "Иванова", "Петровна")
        expected = 'Вашего куратора зовут Мария Иванова Петровна'
        self.assertEqual(str(curator), expected)


class TestGigrometr(unittest.TestCase):
    """Тесты для класса Gigrometr"""
    
    def setUp(self):
        lab_24.now_wet = 0
    
    def test_init_without_wet(self):
        gigro = Gigrometr()
        self.assertEqual(gigro._wet, 0)
    
    def test_init_with_wet(self):
        gigro = Gigrometr(65)
        self.assertEqual(gigro._wet, 65)
    
    def test_set_wet_manually(self):
        gigro = Gigrometr(0)
        gigro.wet = 45
        self.assertEqual(gigro.wet, 45)

    def test_exception_when_wet_negative(self):
        gigro = Gigrometr(0)
        with self.assertRaises(WetValueError):
            gigro.wet = -20


class TestClimateScenary(unittest.TestCase):
    """Тесты для класса ClimateScenary"""
    
    def setUp(self):
        self.temp_file = 'test_journal.csv'
        lab_24.file = self.temp_file
        
        with open(self.temp_file, 'w') as f:
            pass
        
        lab_24.now_wet = 50
        self.danger_list = ["Статуя", "Картина"]
        self.climate = ClimateScenary(self.danger_list.copy())
    
    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
        if os.path.exists('objects.pkl'):
            os.unlink('objects.pkl')
    
    def test_init_with_danger_list(self):
        self.assertEqual(self.climate.name_log, self.temp_file)
        self.assertEqual(self.climate.danger_list, ["Статуя", "Картина"])
        self.assertIsInstance(self.climate.log, Stack)
        self.assertIsNotNone(self.climate.now_time)
    
    def test_str_no_records(self):
        if os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
        climate = ClimateScenary([])
        result = str(climate)
        self.assertEqual(result, 'Записей пока нет')
    
    def test_save_to_csv_with_danger(self):
        lab_24.now_wet = 65
        self.climate.save_to_csv()
        self.assertTrue(os.path.exists(self.temp_file))
        
        with open(self.temp_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Влажность'], '65')
        self.assertEqual(rows[0]['Экспонаты в опасности'], 'Статуя, Картина')


class TestMuseumSystem(unittest.TestCase):
    """Тесты для класса MuseumSystem"""
    
    def setUp(self):
        self.gigro = Gigrometr(50)
        self.curator = Curator("Иван", "Петров", "Сидорович")
        self.climate = ClimateScenary([])
        self.db = MuseumDatabase()
        
        exp1 = Exponate("Статуя")
        exp1.max_wet = 70
        exp2 = Exponate("Картина")
        exp2.max_wet = 60
        self.db.add_exponate(exp1)
        self.db.add_exponate(exp2)
        
        self.objects = [self.gigro, self.curator, self.climate, self.db]
    
    def tearDown(self):
        if os.path.exists('objects.pkl'):
            os.unlink('objects.pkl')
    
    def test_serialize_creates_file(self):
        MuseumSystem.serialize(self.objects)
        self.assertTrue(os.path.exists('objects.pkl'))
    
    def test_serialize_content(self):
        MuseumSystem.serialize(self.objects)
        
        with open('objects.pkl', 'rb') as f:
            data = pickle.load(f)
        
        # Должно быть 4 базовых объекта
        self.assertEqual(len(data), 4)
        self.assertIsInstance(data[0], Gigrometr)
        self.assertIsInstance(data[1], Curator)
        self.assertIsInstance(data[2], ClimateScenary)
        self.assertIsInstance(data[3], MuseumDatabase)
    
    def test_serialize_and_deserialize(self):
        MuseumSystem.serialize(self.objects)
        result = MuseumSystem.deserialize()
        
        self.assertEqual(len(result), 4)
        restored_db = result[3]
        
        # Проверяем, что в БД сохранились экспонаты
        self.assertEqual(len(restored_db), 2)
        self.assertIsNotNone(restored_db.get_exponate("Статуя"))
        self.assertEqual(restored_db.get_exponate("Статуя").max_wet, 70)


class TestExponateNameError(unittest.TestCase):
    """Тесты для исключения ExponateNameError"""
    def test_exception_message_contains_name(self):
        invalid_name = "!!!"
        with self.assertRaises(ExponateNameError) as context:
            raise ExponateNameError(invalid_name)
        self.assertIn(invalid_name, str(context.exception))


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        self.temp_csv = 'test_integration.csv'
        lab_24.file = self.temp_csv
        
        with open(self.temp_csv, 'w') as f:
            pass
        
        lab_24.now_wet = 0
        if os.path.exists('objects.pkl'):
            os.unlink('objects.pkl')
    
    def tearDown(self):
        if os.path.exists(self.temp_csv):
            os.unlink(self.temp_csv)
        if os.path.exists('objects.pkl'):
            os.unlink('objects.pkl')
    
    def test_full_serialization_cycle(self):
        gigro = Gigrometr(50)
        curator = Curator("Анна", "Смирнова", "Игоревна")
        climate = ClimateScenary(["Экспонат1"])
        db = MuseumDatabase()
        
        for name in ["Статуя", "Картина", "Ваза"]:
            exp = Exponate(name)
            exp.max_wet = 70
            db.add_exponate(exp)
        
        objects = [gigro, curator, climate, db]
        MuseumSystem.serialize(objects)
        
        loaded = MuseumSystem.deserialize()
        
        self.assertEqual(len(loaded), 4)
        self.assertEqual(loaded[1].person.f_name, "Анна")
        self.assertEqual(loaded[1].person.s_name, "Смирнова")
        self.assertEqual(len(loaded[3]), 3)


if __name__ == '__main__':
    unittest.main()