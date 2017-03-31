from inspect import getargspec
    
class Botify:
    """Framework for creating tools which perform various tasks
    based on natural language.

    This framework enables developers to create a mapping between
    a natural language and user defined functions. This technique can
    then be used to create a tool which carries out certain tasks.

    Attributes
    ----------
    StrictModeEnabled : bool
        whether strict mode is enabled(Default True).

    Parameters
    ----------
    is_token_data_callback : function
        A function to determine whether a string token is a valid data.

        The function should take a single parameter as input and return
        True or False based on whether the token recieved is a valid data.
        `data` is defined as a token which yields information which needs
        to be passed to one of the defined tasks.

    clean_data_callback : function
        A function to perform any modification prior to passing the string
        token to the appropriate task. This callback if specified, will be used
        to generate the parameters which are to be passed to the tasks.
    """
    ACTION_DELETE = 'delete'
    ACTION_UPDATE_RULE = 'update_rule'
    ACTION_UPDATE_CONTEXT = 'update_context'
    
    def __init__(self, is_token_data_callback=None,
                 clean_data_callback=None):
        self._parsed_list = []
        self._most_recent_report = []
        
        if is_token_data_callback is None:
            self._is_token_data_callback = lambda x: False
        else:
            self._is_token_data_callback = is_token_data_callback
        
        if clean_data_callback is None:
            self._clean_data_callback = lambda x: x
        else:
            self._clean_data_callback = clean_data_callback
        
        self._clean_data_callback = clean_data_callback
        self.strict_mode_enabled = True
        self._tasks = {}
        #self._rule_modifiers = {}
        #self._context_modifiers = {}
        self._modifiers = {}

    # Returns the argument count of the function at _parsed_list[index]
    @staticmethod
    def _get_args_count(function):
        return len(getargspec(function).args)

    def _get_priority_set(self):
        s = set()
        for item in self._parsed_list:
            if self._is_token_data_callback(item) is False:
                s.add(item['context'][1])
        return s

    def _get_action_mapping(self):
        return {ACTION_DELETE : self._action_delete,
                ACTION_UPDATE_RULE : self._action_update_rule,
                ACTION_UPDATE_CONTEXT : self._action_update_context,
        }

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

    def add_modifier(self, modifier, keywords, relative_pos, action, parameter=None):
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
            in the presence of `modifier`. It's value can never be 0. Data
            fields should also be considered when calculating the relative
            position.

        """
        if relative_pos == 0:
            raise ValueError("relative_pos cannot be 0")
        modifier_dict = self._modifiers.get(modifier, {})
        value = (action, parameter, relative_pos)
        for keyword in keywords:
            action_list = list(modifier_dict.get(keyword, []))
            action_list.append(value)
            modifier_dict[keyword] = tuple(action_list)
        self._modifiers[modifier] = modifier_dict
    
    def parse(self, text):
        """Parse the string `text` and return a tuple of left over Data fields.

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

        modifier_index_list = []
        
        for item in self._token_list:
            
            if(self._is_token_data_callback(item)):
                self._parsed_list.append(self._clean_data_callback(item))
                
            if item in self._tasks:
                d = {}
                d['context'] = self._tasks[item]['context']
                d['rule'] = self._tasks[item]['rule']
                d['task'] = item
                self._parsed_list.append(d)

            if item in self._modifiers:
                modifier_index_list.append((len(self._parsed_list), item))

        self._apply_modifiers(modifier_index_list)
        return self._evaluate()

    def _apply_modifiers(self, modifier_index_list):
        for pos, item in modifier_index_list:
            for key, action_list in self._modifiers[item].items():
                for value in action_list:
                    try:
                        task_index = pos + value[2]
                        if value[2] > 0:
                            task_index -= 1
                        if self._is_token_data_callback(self._parsed_list[task_index]):
                            pass
                        elif self._parsed_list[task_index]['task'] == key:
                            action = self._get_action_mapping[value[0]]
                            if value[1] is None:
                                action(task_index)
                            else:
                                action(task_index, value[1])
                    except IndexError:
                        pass

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
                    if self._is_token_data_callback(item) is False:
                        if(item['context'][1] == priority):
                            temp.append(index-offset)
                            offset += self._get_args_count(item['context'][0])
                if(len(temp) == 0):
                    break;
                for task_index in temp:
                    # While Debugging Uncomment the next line.
                    # It gives a very detailed output
                    #print(task_index, temp, self._parsed_list)
                    
                    # TODO: use the return value of _find_data
                    self._find_data(-1, task_index)
        for item in self._parsed_list:
            if self._is_token_data_callback(item):
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
                if  0 <= k < len(self._parsed_list):
                    if self._is_token_data_callback(self._parsed_list[k]):
                        data_index_list.append(k)
                    elif caller_index != k:
                        # the above check is necessary to prevent recursion cycles
                        status = self._find_data(task_index,k)
                        if status is True\
                           and 0 <= k < len(self._parsed_list)\
                           and self._is_token_data_callback(self._parsed_list[k])\
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

    def _action_delete(self, task_index):
        del self._parsed_list[len(self._parsed_list) + task_index]

    def _action_update_rule(self, task_index, rule):
        self._parsed_list[task_index]['rule'] = rule

    def _action_update_context(self, task_index, context):
        self._parsed_list[task_index]['context'] = context
            
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
        if self._is_token_data_callback(res) is True:
            self._parsed_list.insert(task_index-offset, res)
        
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
        
