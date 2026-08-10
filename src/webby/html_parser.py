from src.webby.constants import HEAD_TAGS, SELF_CLOSING_TAGS
from src.webby.element import Element
from src.webby.text import Text


class HTMLParser:
    def __init__(self, body):
        self.unfinished_tag = []
        self.body = body

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished_tag]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def get_attributes(self, tag_str):
        parts = tag_str.split()
        tag = parts[0].casefold()
        attrs = {}
        for attrpairs in parts[1:]:
            if "=" in attrpairs:
                key, value = attrpairs.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attrs[key.casefold()] = value.strip('"').strip("'")
            else:
                attrs[attrpairs.casefold()] = ""
        return tag, attrs

    def add_text(self, text):
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished_tag[-1] if self.unfinished_tag else None
        node = Text(text, parent)
        if parent:
            parent.children.append(node)

    def add_tag(self, tag_str):
        tag, attributes = self.get_attributes(tag_str)
        if tag_str.startswith("!"):
            return
        self.implicit_tags(tag)
        if tag_str.startswith("/"):
            if len(self.unfinished_tag) == 1:
                return
            tag_name = tag[1:]
            if self.unfinished_tag and self.unfinished_tag[-1].tag == tag_name:
                node = self.unfinished_tag.pop()
                parent = self.unfinished_tag[-1] if self.unfinished_tag else None
                if parent:
                    parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished_tag[-1] if self.unfinished_tag else None
            node = Element(tag, attributes, parent)
            if parent:
                parent.children.append(node)
        else:
            parent = self.unfinished_tag[-1] if self.unfinished_tag else None
            node = Element(tag, attributes, parent)
            self.unfinished_tag.append(node)

    def finish(self):
        if not self.unfinished_tag:
            self.implicit_tags(None)
        while len(self.unfinished_tag) > 1:
            node = self.unfinished_tag.pop()
            parent = self.unfinished_tag[-1] if self.unfinished_tag else None
            if parent:
                parent.children.append(node)
        return self.unfinished_tag[0] if self.unfinished_tag else None

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text.strip())
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def print_tree(self, node=None, level=0):
        if node is None:
            node = self.finish()
        indent = "  " * level
        print(f"{indent}{node}")
        for child in node.children:
            self.print_tree(child, level + 1)
