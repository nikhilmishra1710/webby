import tkinter

from src.webby.constants import HEIGHT, WIDTH, VSTEP, SCROLL_STEP
from src.webby.document_layout import DocumentLayout
from src.webby.html_parser import HTMLParser


class Browser:
    def __init__(self):
        self.scroll = 0
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scrollDown)
        self.window.bind("<Up>", self.scrollUp)
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.parser = HTMLParser()
        self.canvas.pack()

    def load(self, url):
        body = url.request()
        print(body)
        self.nodes = self.parser.parse(body)
        self.parser.print_tree(self.nodes)
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = self.document.display_list
        self.draw()

    def scrollDown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollUp(self, e):
        self.scroll -= SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=word, font=font, anchor="nw"
            )
