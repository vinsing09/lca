import sys
try:
    import setuptools._vendor.jaraco.text as _jt
    import types
    jaraco = types.ModuleType("jaraco")
    jaraco.text = _jt
    sys.modules["jaraco"] = jaraco
    sys.modules["jaraco.text"] = _jt
except Exception:
    pass
