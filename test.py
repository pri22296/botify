import unittest
from botify import Botify, Context

class BotifyTestCase(unittest.TestCase):
    def setUp(self):
        self.flag = 0
        self.bot = Botify(self.is_data_callback, self.clean_data_callback)

    def is_data_callback(self):
        return False

    def clean_data_callback(self, value):
        return value

    def task1(self):
        self.flag = 1
        
    def test_add_task(self):
        context = Context(self.task1, 0)
        rule = (-1,)
        keywords = ('keyword1', 'keyword2')
        self.bot.add_task(keywords, context, rule)
        for keyword in keywords:
            self.assertEqual(self.bot._tasks[keyword]['context'], context)
            self.assertEqual(self.bot._tasks[keyword]['rule'], rule)

    def test_add_modifier(self):
        modifier = 'hello'
        keywords = ('keyword1', 'keyword2')
        relative_pos = 1
        action = Botify.ACTION_UPDATE_RULE
        parameter = (1,)
        self.bot.add_modifier(modifier, keywords, relative_pos,
                              action, parameter)
        self.assertTrue(modifier in self.bot._modifiers)
        for keyword in keywords:
            self.assertTrue(keyword in self.bot._modifiers[modifier])
            value = (action, parameter, relative_pos)
            self.assertTrue(value in self.bot._modifiers[modifier][keyword])


if __name__ == '__main__':
    unittest.main()
