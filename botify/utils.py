import inspect

def get_args_count(function):
    return len(inspect.getfullargspec(function).args)
