from src.webby.constants import WIDTH, HSTEP, VSTEP
from src.webby.layout import BlockLayout


class DocumentLayout:
    def __init__(self, node):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height
        self.display_list = child.display_list

    def paint(self):
        return []
