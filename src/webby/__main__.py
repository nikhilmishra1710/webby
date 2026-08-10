import sys
import tkinter

from src.webby.browser import Browser
from src.webby.url import URL


def main():
    print("Entry point for Webby")
    Browser().new_tab(URL(sys.argv[1]))
    tkinter.mainloop()
