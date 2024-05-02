import operator
import logging
from functools import reduce  # forward compatibility for Python 3


class Transformer:
    def __init__(self, transform_map):
        self.transform_map = transform_map

    # Takes item and runs it trough provided mapping.
    # Leaves unmapped keys as is.
    # Meaning the return value is a new object containing all keys of the former object.
    def transform(self, item, transformation=None):
        if not transformation:
            return self.transform(item, self.transform_map)

        if isinstance(transformation, Transformer):
            return transformation.transform(item)
        if isinstance(transformation, dict):
            return self.transform_dict(item, transformation)
        if isinstance(transformation, list):
            return self.transform_list(item, transformation)
        if isinstance(transformation, tuple):
            first_transform = transformation[0]
            rest = tuple(list(transformation)[1:])
            transformed_item = self.transform(item, first_transform)
            if len(rest) == 0:
                return transformed_item
            return self.transform(transformed_item, rest)
        if callable(transformation):
            return transformation(item)
        if isinstance(transformation, str):
            return safe_dot_get(item, transformation)
        raise ValueError(f"Type of transformation is wrong {type(transformation)}")

    def transform_dict(self, item, transformation):
        return {k: self.transform(item, v) for k, v in transformation.items()}

    def transform_list(self, item, transformation):
        return [self.transform(item, v) for v in transformation]

    # Takes item and runs it trough provided mapping.
    # Returns a subset of the input. Only the mapped values.
    def transform_to_subset(self, item):
        result = {}
        for key, mapping in self.transform_map.items():
            # value = item[key]
            result = {**result, **self.transform_key(key, mapping, item)}
        return result

    def exclusive_transform_to_subset(self, item):
        result = {}
        for key, mapping in self.transform_map.items():
            # value = item[key]
            result = {**result, **self.exclusive_transform_key(key, mapping, item)}
        return result

    # Will drop keys that couldn't be found
    def exclusive_transform_key(self, key, mapping, item):
        try:
            return self.transform_key(key, mapping, item)
        except Exception as e:
            logging.warn("Transformer raised an execption. Ignoring intentionally.")
            logging.warn(e)
            return {}

    # name is required or it will fail
    def transform_key(self, key, mapping, item):
        # key = mapping["name"]
        try:
            meth = mapping.get("method")
            if meth:
                return {key: meth(item)}
            from_field = mapping["from"]
            value = dot_get(item, from_field)  # Can raise KeyError. Enables using dot notation to access nested dicts.
            fun = mapping.get("function")
            if fun:
                value = fun(value)
            return {key: value}
        except DropKey:
            return {}


def OR_DROPKEY(func):
    def wrapper(arg):
        res = func(arg)
        if not res:
            raise DropKey
        return res

    return wrapper


def OR(func, default=None):
    def wrapper(arg):
        try:
            return func(arg)
        except:
            return default

    return wrapper


# def OR_DROPKEY(func):
#     return OR(func, {})


class DropKey(Exception):
    pass


# def dot_get_or(root, lookup, default):
#     try:
#         return dot_get(root, lookup)


def safe_dot_get(root, lookup):
    if root is None:
        return None
    try:
        return dot_get(root, lookup)
    except KeyError:
        return None
    except TypeError:
        return None


def dot_get(root, lookup):
    items = lookup.split(".")
    _items = []
    for i in items:
        try:
            _items.append(int(i))
        except:
            _items.append(i)
    return reduce(operator.getitem, _items, root)


def first_not_none(items):
    for item in items:
        if not item is None:
            return item


def remove_none(items):
    """
    Removes every element that is None in the given list. If the list is None itself, None is returned
    """
    if not items is None:
        return [item for item in items if not item is None]


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, int):
        return False
    if len(value) == 0:
        return True
    if isinstance(value, list) and all([el is None for el in value]):
        return True
    return False


def if_not_empty(func):
    """
    if_not_empty

    returns a function that applys the given function to the argument if it is not None or its lenght greater then zero
    
    :param func: function that is applied
    """

    def wrapped(value):
        if is_empty(value):
            return None
        return func(value)

    return wrapped


def constant(c):
    return lambda _: c


def value_if_empty(default_value):
    """
    returns a functions thats returns the default_value if its argument is empty (None, '')
    """

    def wrapped(value):
        if value is None or len(value) == 0:
            return default_value
        if isinstance(value, list) and all([el is None for el in value]):
            return default_value
        return value

    return wrapped


def for_each(func):
    return lambda x: list(map(func, x))


def for_each_key(func):
    return lambda x: {k: func(v) for k, v in x.items()}


def should_call(validator, function):
    def wrapper(obj):
        if validator(obj):
            return function(obj)
        return None

    return wrapper


def has_keys(keys):
    def wrapper(obj):
        for k in keys:
            if obj.get(k) is None:
                return False
        return True

    return wrapper


def unpack_kwargs_for(func):
    def wrapper(obj):
        return func(**obj)

    return wrapper


def drop_key_if_empty(*args):
    keys = list(args)

    def wrapped(item):
        return {k: v for k, v in item.items() if not (k in keys and is_empty(v))}

    return wrapped


def max_length(length, ellipse="..."):
    def wrapped(item):
        if item is None:
            return None
        if len(item) > length:
            return item[0 : (length - len(ellipse))] + ellipse
        return item

    return wrapped


def without_keys(x, keys):
    return {k: v for k, v in x.items() if not k in keys}


def switch(cases):
    def do(item):
        for case, action in cases.items():
            if case(item):
                return action(item)
        raise NotImplementedError(f"No case implemented for value {item}")

    return do


def keys_are_none(*keys):
    def evaluate(item):
        return all([item.get(k) is None for k in keys])

    return evaluate


def default(_):
    return True


def is_none(item):
    return item is None


def is_empty_list(item):
    return isinstance(item, list) and len(item) == 0


def is_list(item):
    return isinstance(item, list)


def if_else(condition, true_func, false_func):
    def wrapped(data):
        if condition(data):
            return true_func(data)
        return false_func(data)

    return wrapped


def transform(mapping):
    return Transformer(mapping).transform
