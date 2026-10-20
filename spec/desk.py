import threading
class NoRoute(Exception): pass
class AmbiguousRoute(Exception): pass
class Desk:
    def __init__(self):
        self._routes = {}; self._lock = threading.Lock()
    def press(self, layer, cls, fn):
        key = (layer, cls)
        with self._lock:
            if key in self._routes: raise AmbiguousRoute(f"already: {key}")
            self._routes[key] = fn
    def route(self, layer, cls, *a, **kw):
        fn = self._routes.get((layer, cls))
        if fn is None: raise NoRoute(f"no button for {(layer, cls)}; have {sorted(self._routes)}")
        return fn(*a, **kw)
    def buttons(self): return sorted(self._routes)
desk = Desk()
if __name__ == "__main__":
    d = Desk()
    d.press("domain","code", lambda x: f"code:{x}")
    assert d.route("domain","code","foo") == "code:foo"
    try: d.route("domain","doc")
    except NoRoute: pass
    else: raise SystemExit("expected NoRoute")
    try: d.press("domain","code", lambda x: x)
    except AmbiguousRoute: pass
    else: raise SystemExit("expected AmbiguousRoute")
    print("desk OK")
