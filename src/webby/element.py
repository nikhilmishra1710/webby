class Element:
    def __init__(self, tag, attributes={}, parent=None):
        self.tag = tag
        self.attributes = attributes
        self.parent = parent
        self.children = []
        self.is_focused = False

    def __repr__(self):
        return f"<{self.tag} {self.attributes}>"
