#   _ \  _)        |      |     _)         |
#  |   |  |   __|  __ \   |      |  __ \   |  /   __|
#  __ <   |  (     | | |  |      |  |   |    <  \__ \
# _| \_\ _| \___| _| |_| _____| _| _|  _| _|\_\ ____/

# import me
# https://www.crummy.com/software/BeautifulSoup/
# also dep lxml or change to automatically choose
# Pillow
import warnings
from ._richlinks import Richlinks


warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

# TODO add url tools
# TODO add extra utils


# Concerns:
# LXML as a dependency
# Not Python2 Compatible
# Interanlly al ack of exceptions, returning None instead
# settings handling, would be nice with another way to reach the class settings
