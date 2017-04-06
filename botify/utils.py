import inspect

def _get_args_count_helper(function, argspec_func):
    args = argspec_func(function).args
    try:
        if args[0] == 'self':
            return len(args) - 1
    except IndexError:
        pass
    return len(args)

def get_args_count(function):
    try:
        return len(inspect.signature(function).parameters)
    except AttributeError:
        try:
            return _get_args_count_helper(function, inspect.getfullargspec)
        except AttributeError:
            return _get_args_count_helper(function, inspect.getargspec)
        
