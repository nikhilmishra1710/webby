import tkinter

from src.webby.url import lex

HEIGHT, WIDTH = 600, 800
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
cursor_x, cursor_y = HSTEP, VSTEP
class Browser:
    def __init__(self):
        self.scroll = 0
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scrollDown)
        self.window.bind("<Up>", self.scrollUp)
        self.canvas = tkinter.Canvas(
            self.window,
            width = WIDTH,
            height = HEIGHT
        )
        self.canvas.pack()
        
    def load(self, url):
        global cursor_x, cursor_y
        text = lex(url.request())
        self.display_list = layout(text)
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
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c) 
    
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        
        if cursor_x + HSTEP > WIDTH:
            cursor_x = HSTEP
            cursor_y += VSTEP
        
    return display_list