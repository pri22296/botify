from inspect import getargspec
    
class NLParser:
    """Framework for creating tools which perform various tasks
    based on natural language.

    This framework enables developers to create a mapping between
    a natural language and user defined functions. This technique can
    then be used to create a tool which carries out certain tasks.

    Attributes
    ----------
    StrictModeEnabled : bool
        whether strict mode is enabled(Default True).
    """
    def __init__(self, strict_mode_enabled=True):
        self._parsed_list = []
        self._most_recent_report = []
        self.strict_mode_enabled = strict_mode_enabled
        self._tasks = {}
        self._rule_modifiers = {}
        self._context_modifiers = {}
        self._custom_modifiers = {}
        
    def is_data(self, value):
        """Whether the string passed is a valid data.

        If `value` is a data, it will be passed to one of the
        functions according to the rules. This method is meant to
        be overridden by the child class.

        Parameters
        ----------
        value : str
            String token extracted from user input.
        """
        return False

    def clean_data(self, value):
        """Modify the string value which is a valid data to
        a suitable form such that it can be passed to the
        tasks.

        This method is meant to be overridden by the child class.

        Parameters
        ----------
        value : str
            String token extracted from user input.
        """
        return value

    # Returns the argument count of the function at _parsed_list[index]
    @staticmethod
    def _get_args_count(function):
        return len(getargspec(function).args)

    def _get_priority_set(self):
        s = set()
        for item in self._parsed_list:
            if self.is_data(item) is False:
                s.add(item['context'][1])
        return s

    def add_task(self, keywords, context, rule):
        """Map a function to a list of keywords

        Parameters
        ----------
        keywords : iterable of str
            sequence of strings which should trigger the given function
        context : Context
            A Context object created using desired function
        rule : tuple
            A tuple of integers, which act as relative indices using which data
            is extracted to be passed to the function passed via context.
        """
        for keyword in keywords:
            self._tasks[keyword] = {'context': context, 'rule': rule}

    def add_rule_modifier(self, modifier, keywords, rule, relative_pos):
        """Modify rules for existing tasks based on presence of a keyword.

        Parameters
        ----------
        modifier : str
            A string value which would trigger the given Rule Modifier.
        keywords : iterable of str
            sequence of strings which are keywords for some task,
            for which the rule has to be modified.
        rule : tuple
            A tuple of integers, which act as the new rule for the task
            referred by `relative_pos`.
        relative_pos : int
            Relative position of the task whose rule should be modified
            in the presence of `modifier`.
        """
        modifier_dict = self._rule_modifiers.get(modifier, {})
        modifier_dict.update(dict.fromkeys(keywords, (rule, relative_pos)))
        self._rule_modifiers[modifier] = modifier_dict

    def add_context_modifier(self, modifier, keywords, context, relative_pos):
        """Modify context for existing tasks based on presence of a keyword.

        Parameters
        ----------
        modifier : str
            A string value which would trigger the given Context Modifier.
        keywords : iterable of str
            sequence of strings which are keywords for some task,
            for which the context has to be modified.
        context : Context
            A Context object, which act as the new context for the task
            referred by `relative_pos`.
        relative_pos : int
            Relative position of the task whose context should be modified
            in the presence of `modifier`.
        """
        modifier_dict = self._context_modifiers.get(modifier, {})
        modifier_dict.update(dict.fromkeys(keywords, (context, relative_pos)))
        self._context_modifiers[modifier] = modifier_dict

    def add_custom_modifier(self, modifier, keywords, action, params, relative_pos):
        """Modify existing tasks based on presence of a keyword.

        Parameters
        ----------
        modifier : str
            A string value which would trigger the given Modifier.
        keywords : iterable of str
            sequence of strings which are keywords for some task,
            which has to be modified.
        action : str
            String value representing the action which should be performed
            on the task. Action represents calling a arbitrary function
            to perform th emodification.
        params : tuple
            A tuple of values to be passed to the function represented by
            `action`.
        relative_pos : int
            Relative position of the task which should be modified
            in the presence of `modifier`.
        """
        modifier_dict = self._custom_modifiers.get(modifier, {})
        value = (action, params, relative_pos)
        modifier_dict.update(dict.fromkeys(keywords, value))
        self._custom_modifiers[modifier] = modifier_dict
    
    def parse(self, text):
        """Parse the string `UserInput` and return a tuple of left over Data

        Parameters
        ----------
        text : str
            A string to be parsed

        Returns
        -------
        result : tuple
            A tuple of left over Data after processing
        """
        self._parsed_list = []
        self._most_recent_report = []
        self._token_list = text.lower().split()
        
        for item in self._token_list:
            
            if(self.is_data(item)):
                self._parsed_list.append(self.clean_data(item))
                
            if item in self._tasks:
                d = {}
                d['context'] = self._tasks[item]['context']
                d['rule'] = self._tasks[item]['rule']
                d['keyword'] = item
                self._parsed_list.append(d)
                
            if item in self._rule_modifiers:
                for key, value in self._rule_modifiers[item].items():
                    try:
                        task_index = len(self._parsed_list) + value[1]
                        if self.is_data(self._parsed_list[task_index]):
                            pass
                        elif self._parsed_list[task_index]['keyword'] == key:
                            self._parsed_list[task_index]['rule'] = value[0]
                    except IndexError:
                        pass

            if item in self._context_modifiers:
                for key, value in self._context_modifiers[item].items():
                    try:
                        task_index = len(self._parsed_list) + value[1]
                        if self.is_data(self._parsed_list[task_index]):
                            pass
                        elif self._parsed_list[task_index]['keyword'] == key:
                            self._parsed_list[task_index]['context'] = value[0]
                    except IndexError:
                        pass

            if item in self._custom_modifiers:
                for key, value in self._custom_modifiers[item].items():
                    try:
                        task_index = len(self._parsed_list) + value[2]
                        if self.is_data(self._parsed_list[task_index]):
                            pass
                        elif self._parsed_list[task_index]['keyword'] == key:
                            getattr(self, value[0])(*value[1])
                    except IndexError:
                        pass
                    
        return self._evaluate()

    def _get_report(self):
        """Return a list of dicts with parsing info.

        The dicts contain information about how the string was parsed to
        obtain the final result. This information can be used for debugging
        purposes.
        """
        return self._most_recent_report[:]

    def _evaluate(self):
        for priority in sorted(self._get_priority_set(),reverse=True):
            while(True):
                temp = []
                offset = 0
                for index, item in enumerate(self._parsed_list):
                    if self.is_data(item) is False:
                        if(item['context'][1] == priority):
                            temp.append(index-offset)
                            offset += self._get_args_count(item['context'][0])
                if(len(temp) == 0):
                    break;
                for task_index in temp:
                    # While Debugging Uncomment the next line.
                    # It gives a very detailed output
                    # print(task_index, temp, self._parsed_list)
                    
                    # TODO: use the return value of _findData
                    self._find_data(-1, task_index)
        for item in self._parsed_list:
            if self.is_data(item):
                pass
            else:
                raise ValueError("Unable to Parse")
        return tuple(self._parsed_list)

    def _find_data(self, caller_index, task_index):
        # if task_index does not have a dict that means
        # it has already been evaluated
        # so we just need to return
        try:
            args_count = self._get_args_count(self._parsed_list[task_index]['context'][0])
        except (TypeError, IndexError):
            return False
        should_repeat = not self.strict_mode_enabled
        while(True):
            data_index_list = []
            rule = self._parsed_list[task_index]['rule']
            for i in rule:
                k = task_index + i
                if self.is_data(self._parsed_list[k]) and 0 <= k < len(self._parsed_list):
                    data_index_list.append(k)
                elif caller_index != k:
                    # the above check is necessary to prevent recursion cycles
                    status = self._find_data(task_index,k)
                    if status is True\
                       and 0 <= k < len(self._parsed_list)\
                       and self.is_data(self._parsed_list[k])\
                       and k not in data_index_list:
                        data_index_list.append(k)
                else:
                    return False
                if len(data_index_list) == args_count:
                    break
            if len(data_index_list) == args_count:
                self._apply_task(task_index, data_index_list)
                return True
            else:
                if should_repeat:
                    self._parsed_list[task_index]['rule'] = self._get_nonstrict_rule(task_index)
                    should_repeat = False
                else:
                    raise ValueError('Unable to Parse. Try a different Input')

    def delete(self, task_index):
        del self._parsed_list[len(self._parsed_list) + task_index]
            
    def _apply_task(self, task_index, data_index_list):
        task_context = self._parsed_list[task_index]['context']
        data_list = [self._parsed_list[index] for index in data_index_list]
        offset = 0
        del self._parsed_list[task_index]
        for index,item in enumerate(data_index_list):
            if item > task_index:
                data_index_list[index] -= 1
            else:
                offset += 1
        for index in sorted(data_index_list, reverse=True):
            del self._parsed_list[index]
        res = task_context[0](*data_list)
        self._most_recent_report.append({'function': task_context[0].__name__,
                                         'parameters': tuple(data_list),
                                         'result': res})
        if self.is_data(res) is True:
            self._parsed_list.insert(task_index-offset, res)
            #print(task_context[0].__name__ , tuple(data_list), ' = ', res)
            
        else:
            pass
            #print(task_context[0].__name__ , tuple(data_list))
        
    def _get_default_rule(self, task_index):
        l = []
        k = [-1,1]
        for i in range(self._get_args_count(self._parsed_list[task_index]['context'][0])):
            l += list(map(lambda x: (i+1)*x, k))
        return l

    def _get_nonstrict_rule(self, task_index):
        strictrule_list = list(self._parsed_list[task_index]['rule'])
        l = self._get_default_rule(task_index)
        for item in l:
            if item not in strictrule_list:
                strictrule_list.append(item)
        return tuple(strictrule_list)
        
