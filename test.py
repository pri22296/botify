import unittest
from botify import Botify, Context
from botify.utils import get_args_count


class BotifyTestCase(unittest.TestCase):
    def setUp(self):
        self.flag = 0
        self.bot = Botify(self.is_data_callback, self.clean_data_callback)

    def is_data_callback(self, value):
        return False

    def clean_data_callback(self, value):
        return value

    def task1(self):
        self.flag = 1

    def add_task(self):
        context = Context(self.task1, 0)
        rule = (-1,)
        keywords = ('keyword1', 'keyword2')
        self.bot.add_task(keywords, context, rule)

    def add_modifier(self):
        modifier = 'hello'
        keywords = ('keyword1', 'keyword2')
        relative_pos = 1
        action = Botify.ACTION_UPDATE_RULE
        parameter = ()
        self.bot.add_modifier(modifier, keywords, relative_pos,
                              action, parameter)

    def test_add_task(self):
        self.add_task()
        for keyword in ('keyword1', 'keyword2'):
            self.assertEqual(self.bot._tasks[keyword]['context'], Context(self.task1, 0))
            self.assertEqual(self.bot._tasks[keyword]['rule'], (-1,))

    def test_add_modifier(self):
        self.add_modifier()
        self.assertTrue('hello' in self.bot._modifiers)
        for keyword in ('keyword1', 'keyword2'):
            self.assertTrue(keyword in self.bot._modifiers['hello'])
            value = (Botify.ACTION_UPDATE_RULE, (), 1)
            self.assertTrue(value in self.bot._modifiers['hello'][keyword])

    def test_parse(self):
        self.add_task()
        #self.add_modifier()
        result = self.bot.parse("hello keyword1")
        self.assertEqual(len(result), 0)
        self.assertEqual(self.flag, 1)

def free_method(params):
    pass

class ArgsCountTestCase(unittest.TestCase):
    def method1(self):
        pass

    def method2(self, param):
        pass

    @staticmethod
    def method3(params):
        pass

    @classmethod
    def method4(cls, params):
        pass

    def test_with_no_params(self):
        self.assertEqual(get_args_count(self.method1), 0)

    def test_with_params(self):
        self.assertEqual(get_args_count(self.method2), 1)

    def test_static_method(self):
        self.assertEqual(get_args_count(self.method3), 1)

    def test_class_method(self):
        self.assertEqual(get_args_count(self.method4), 1)

    def test_free_method(self):
        self.assertEqual(get_args_count(free_method), 1)


if __name__ == '__main__':
    unittest.main()
