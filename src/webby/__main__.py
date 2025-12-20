import sys
import tkinter

from src.webby.url import URL
from src.webby.browser import Browser

def main():
    print("Entry point for Webby")
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
    