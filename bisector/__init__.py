from .bisector import *

def run_bisect(options, callback):
    b = Bisector(options)
    while not b.is_done():
        x = b.current
        status = callback(x)
        b.set_status(status)
    return b.get_result()

