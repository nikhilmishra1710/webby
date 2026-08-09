import tkinter

from src.webby.constants import HEIGHT, SCROLL_STEP, VSTEP, WIDTH
from src.webby.css_parser import CSSParser, cascade_priority, style, tree_to_list
from src.webby.document_layout import DocumentLayout
from src.webby.element import Element
from src.webby.html_parser import HTMLParser


def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


with open("sample_files/browser.css") as css_file:
    DEFAULT_STYLE_SHEET = CSSParser(css_file.read()).parse()


class Browser:
    def __init__(self):
        self.scroll = 0
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scrollDown)
        self.window.bind("<Up>", self.scrollUp)
        self.canvas = tkinter.Canvas(
            self.window, width=WIDTH, height=HEIGHT, bg="white"
        )
        self.parser = HTMLParser()
        self.canvas.pack()

    def load(self, url):
        body = url.request()
        self.nodes = self.parser.parse(body)
        rules = DEFAULT_STYLE_SHEET.copy()
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:
                continue
            rules.extend(CSSParser(body).parse())
        style(self.nodes, sorted(rules, key=cascade_priority))
        # self.parser.print_tree(self.nodes)
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()

    def scrollDown(self, e):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scrollUp(self, e):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, 0)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)
