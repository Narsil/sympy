"""
Caching framework.
It was shamelessly taken from django cache framework and adapted to suit
sympy's needs

This package defines set of cache backends that all conform to a simple API.
In a nutshell, a cache is a set of values -- which can be any object that
may be pickled -- identified by string keys.  For the complete API, see
the abstract BaseCache class in sympy.core.cache.backends.base.

"""
from sympy.core.decorators import wraps
import sys


class IncorrectConfiguration(Exception):
    pass

CACHES = {
        'yes': {
            'LOCATION': 'default',
            'BACKEND': 'sympy.core.cache.backends.locmem.LocMemCache',
        },
        'debug': {
            'LOCATION': 'debug',
            'BACKEND': 'sympy.core.cache.backends.locmem.DebugLocMemCache',
        },
        'no': {
            'BACKEND': 'sympy.core.cache.backends.dummy.DummyCache',
        }
}

from os import getenv
DEFAULT_CACHE_ALIAS = 'yes'
USE_CACHE = getenv('SYMPY_USE_CACHE', DEFAULT_CACHE_ALIAS).lower()

if DEFAULT_CACHE_ALIAS not in CACHES:
    raise IncorrectConfiguration(
            "You must define a '%s' cache" % DEFAULT_CACHE_ALIAS)


def parse_backend_conf(backend, **kwargs):
    """
    Helper function to parse the backend configuration
    that doesn't use the URI notation.
    """
    conf = CACHES[backend]
    args = conf.copy()
    args.update(kwargs)
    backend = args.pop('BACKEND')
    location = args.pop('LOCATION', '')
    return backend, location, args


def get_cache(backend, **kwargs):
    """
    To load a backend that is pre-defined in the settings::

        cache = get_cache('yes')
    """
    try:
        backend, location, params = parse_backend_conf(backend, **kwargs)
        mod_path, cls_name = backend.rsplit('.', 1)
        __import__(mod_path)
        mod = sys.modules[mod_path]
        backend_cls = getattr(mod, cls_name)
    except (AttributeError, ImportError), e:
        raise IncorrectConfiguration(
            "Could not find backend '%s': %s" % (backend, e))
    return backend_cls(location, params)

cache = get_cache(USE_CACHE)

def is_immutable(obj):
    return isinstance(obj, (str, int, long, bool, float, tuple))

def repr(obj):
    return '%s_%s' % (hex(id(obj)), hex(hash(obj)))

def make_key(func, args, kwargs):
    """
    Key is not a string
    """
    if kwargs:
        keys = kwargs.keys()
        keys.sort()
        items = [(k, kwargs[k]) for k in keys]
        k = (func,) + args + tuple(items)
    else:
        k = (func,) + args
    k = k + tuple(map(type, k))
    return k

    # string = "%s_%s_%s" % (
    #         '%s.%s.%s' % (func.__module__, func.__name__, repr(func)),
    #         [repr(arg) for arg in args],
    #         {key: repr(kwargs[key]) for key in keys})
    # return string
    #return hex(hash((func, args, frozenset(sorted(kwargs.items())))))


def cacheit(func):
    """caching decorator.

       important: the result of cached function must be *immutable*


       **Example**

       >>> from sympy.core.cache import cacheit
       >>> @cacheit
       ... def f(a,b):
       ...    return a+b

       >>> @cacheit
       ... def f(a,b):
       ...    return [a,b] # <-- WRONG, returns mutable object

       to force cacheit to check returned results mutability and consistency,
       set environment variable SYMPY_USE_CACHE to 'debug'
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Assemble the args and kwargs to compute the hash.
        """
        key = make_key(func, args, kwargs)
        cache_key = hex(hash(key))
        cached_values_dict = cache.get(cache_key, {})
        if cached_values_dict and key in cached_values_dict:
            r = cached_values_dict[key]
            return r
        r = func(*args, **kwargs)
        cached_values_dict[key] = r
        cache.set(cache_key, cached_values_dict)
        return r
    return wrapper


def clear_cache():
    cache.clear()
