import tkinter.font

from src.webby.text import Text


HEIGHT, WIDTH = 600, 800
HSTEP, VSTEP = 13, 18


class Layout:
    cursor_x = 0
    cursor_y = 0
    weight = "normal"
    style = "roman"
    size = 12

    def __init__(self, tree):
        self.display_list = []
        self.line = []
        self.recurse(tree)
        self.flush()

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
    
    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
    
    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                    self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
    
    def token(self, tok):
        print("Token:", tok)
        if isinstance(tok, Text):
            for w in tok.text.split():
                self.word(w)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style)
        w = font.measure(word)
        print("Word:", word, self.cursor_x, w, self.size)
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for _, __, font in self.line]
        print("Metrics:", metrics)
        max_ascent = max(metric["ascent"] for metric in metrics)
        baseline = self.cursor_y + max_ascent * 1.25
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            print(x, y, word)
            self.display_list.append((x, y, word, font))
        print(self.display_list)
        max_descent = max(metric["descent"] for metric in metrics)
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []
