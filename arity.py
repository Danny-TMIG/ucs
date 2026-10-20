"""Arity verification and checking module."""
import inspect

def check_arity(func, *args, **kwargs):
    sig = inspect.signature(func)
    try:
        sig.bind(*args, **kwargs)
        return True
    except TypeError:
        return False

if __name__ == "__main__":
    print("arity.py OK")
