import sys

if sys.version_info < (3, 8):
    from ._buffered_3_7 import buffered
else:
    from ._buffered_3_8 import buffered
