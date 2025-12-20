import sys
from src.webby.url import load, URL

def main():
    print("Entry point for Webby")
    load(URL(sys.argv[1]))