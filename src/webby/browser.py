import ctypes
import urllib.parse
import math
import sdl2
import skia

from src.webby.constants import HEIGHT, SCROLL_STEP, VSTEP, WIDTH
from src.webby.css_parser import CSSParser, cascade_priority, style, tree_to_list
from src.webby.document_layout import DocumentLayout
from src.webby.draw import DrawLine, DrawOutline, DrawRect, DrawText, Rect
from src.webby.element import Element
from src.webby.html_parser import HTMLParser
from src.webby.js_context import JSContext
from src.webby.layout import get_font
from src.webby.text import Text
from src.webby.url import URL


def paint_tree(layout_object, display_list):
    cmds = []
    if layout_object.should_paint():
        cmds = layout_object.paint()
    for child in layout_object.children:
        paint_tree(child, cmds)

    if layout_object.should_paint():
        cmds = layout_object.paint_effects(cmds)
    display_list.extend(cmds)


with open("sample_files/browser.css") as css_file:
    DEFAULT_STYLE_SHEET = CSSParser(css_file.read()).parse()


def linespace(font):
    metrics = font.getMetrics()
    return metrics.fDescent - metrics.fAscent


class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.focus = None
        self.address_bar = ""

        self.font = get_font(20, "normal", "roman")
        self.font_height = linespace(self.font)

        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding

        plus_width = self.font.measureText("+") + 2 * self.padding
        self.newtab_rect = skia.Rect.MakeLTRB(
            self.padding,
            self.padding,
            self.padding + plus_width,
            self.padding + self.font_height,
        )

        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + self.font_height + 2 * self.padding

        back_width = self.font.measureText("<") + 2 * self.padding
        self.back_rect = skia.Rect.MakeLTRB(
            self.padding,
            self.urlbar_top + self.padding,
            self.padding + back_width,
            self.urlbar_bottom - self.padding,
        )

        self.address_rect = skia.Rect.MakeLTRB(
            self.back_rect.right() + self.padding,
            self.urlbar_top + self.padding,
            WIDTH - self.padding,
            self.urlbar_bottom - self.padding,
        )

        self.bottom = self.urlbar_bottom

    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right() + self.padding
        tab_width = self.font.measureText("Tab X") + 2 * self.padding
        return skia.Rect.MakeLTRB(
            tabs_start + tab_width * i,
            self.tabbar_top,
            tabs_start + tab_width * (i + 1),
            self.tabbar_bottom,
        )

    def paint(self):
        cmds = []
        cmds.append(DrawLine(0, self.bottom, WIDTH, self.bottom, "black", 1))

        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(
            DrawText(
                self.newtab_rect.left() + self.padding,
                self.newtab_rect.top(),
                "+",
                self.font,
                "black",
            )
        )

        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(
                DrawLine(bounds.left(), 0, bounds.left(), bounds.bottom(), "black", 1)
            )
            cmds.append(
                DrawLine(bounds.right(), 0, bounds.right(), bounds.bottom(), "black", 1)
            )
            cmds.append(
                DrawText(
                    bounds.left() + self.padding,
                    bounds.top() + self.padding,
                    "Tab {}".format(i),
                    self.font,
                    "black",
                )
            )

            if tab == self.browser.active_tab:
                cmds.append(
                    DrawLine(
                        0, bounds.bottom(), bounds.left(), bounds.bottom(), "black", 1
                    )
                )
                cmds.append(
                    DrawLine(
                        bounds.right(),
                        bounds.bottom(),
                        WIDTH,
                        bounds.bottom(),
                        "black",
                        1,
                    )
                )

        cmds.append(DrawOutline(self.back_rect, "black", 1))
        cmds.append(
            DrawText(
                self.back_rect.left() + self.padding,
                self.back_rect.top(),
                "<",
                self.font,
                "black",
            )
        )

        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            cmds.append(
                DrawText(
                    self.address_rect.left() + self.padding,
                    self.address_rect.top(),
                    self.address_bar,
                    self.font,
                    "black",
                )
            )
            w = self.font.measureText(self.address_bar)
            cmds.append(
                DrawLine(
                    self.address_rect.left() + self.padding + w,
                    self.address_rect.top(),
                    self.address_rect.left() + self.padding + w,
                    self.address_rect.bottom(),
                    "red",
                    1,
                )
            )
        else:
            url = str(self.browser.active_tab.url)
            cmds.append(
                DrawText(
                    self.address_rect.left() + self.padding,
                    self.address_rect.top(),
                    url,
                    self.font,
                    "black",
                )
            )

        return cmds

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains(x, y):
            self.browser.new_tab(URL("https://browser.engineering/"))
        elif self.back_rect.contains(x, y):
            self.browser.active_tab.go_back()
            self.browser.raster_chrome()
            self.browser.raster_tab()
            self.browser.draw()
        elif self.address_rect.contains(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains(x, y):
                    self.browser.active_tab = tab
                    break
            self.browser.raster_tab()

    def enter(self):
        if self.focus == "address bar":
            self.browser.active_tab.load(URL(self.address_bar))
            self.focus = None
            self.browser.focus = None

    def blur(self):
        self.focus = None

    def keypress(self, char):
        if self.focus == "address bar":
            self.address_bar += char
            return True
        return False


class Browser:
    def __init__(self):
        self.chrome = Chrome(self)

        self.sdl_window = sdl2.SDL_CreateWindow(
            b"Browser",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            WIDTH,
            HEIGHT,
            sdl2.SDL_WINDOW_SHOWN,
        )
        self.root_surface = skia.Surface.MakeRaster(
            skia.ImageInfo.Make(
                WIDTH, HEIGHT, ct=skia.kRGBA_8888_ColorType, at=skia.kUnpremul_AlphaType
            )
        )
        self.chrome_surface = skia.Surface(WIDTH, math.ceil(self.chrome.bottom))
        self.tab_surface = None

        self.tabs = []
        self.active_tab = None
        self.focus = None

        if sdl2.SDL_BYTEORDER == sdl2.SDL_BIG_ENDIAN:
            self.RED_MASK = 0xFF000000
            self.GREEN_MASK = 0x00FF0000
            self.BLUE_MASK = 0x0000FF00
            self.ALPHA_MASK = 0x000000FF
        else:
            self.RED_MASK = 0x000000FF
            self.GREEN_MASK = 0x0000FF00
            self.BLUE_MASK = 0x00FF0000
            self.ALPHA_MASK = 0xFF000000

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.focus = None
            self.chrome.click(e.x, e.y)
            self.raster_chrome()
        else:
            if self.focus != "content":
                self.focus = "content"
                self.chrome.blur()
                self.raster_chrome()
            url = self.active_tab.url
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
            if self.active_tab.url != url:
                self.raster_chrome()
            self.raster_tab()
        self.draw()

    def handle_key(self, char):
        if not (0x20 <= ord(char) < 0x7F):
            return
        if self.chrome.focus:
            self.chrome.keypress(char)
            self.raster_chrome()
            self.draw()
        elif self.focus == "content":
            self.active_tab.keypress(char)
            self.raster_tab()
            self.draw()

    def handle_enter(self):
        if self.chrome.focus:
            self.chrome.enter()
            self.raster_tab()
            self.raster_chrome()
            self.draw()

    def handle_down(self):
        self.active_tab.scrolldown()
        self.draw()

    def new_tab(self, url):
        new_tab = Tab(HEIGHT - self.chrome.bottom)
        new_tab.load(url)
        self.tabs.append(new_tab)
        self.active_tab = new_tab
        self.raster_chrome()
        self.raster_tab()
        self.draw()

    def raster_tab(self):
        tab_height = math.ceil(self.active_tab.document.height + 2 * VSTEP)

        if not self.tab_surface or tab_height != self.tab_surface.height():
            self.tab_surface = skia.Surface(WIDTH, tab_height)

        canvas = self.tab_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)
        self.active_tab.raster(canvas)

    def raster_chrome(self):
        canvas = self.chrome_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        for cmd in self.chrome.paint():
            cmd.execute(canvas)

    def draw(self):
        canvas = self.root_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        tab_rect = skia.Rect.MakeLTRB(0, self.chrome.bottom, WIDTH, HEIGHT)
        tab_offset = self.chrome.bottom - self.active_tab.scroll
        canvas.save()
        canvas.clipRect(tab_rect)
        canvas.translate(0, tab_offset)
        self.tab_surface.draw(canvas, 0, 0)
        canvas.restore()

        chrome_rect = skia.Rect.MakeLTRB(0, 0, WIDTH, self.chrome.bottom)
        canvas.save()
        canvas.clipRect(chrome_rect)
        self.chrome_surface.draw(canvas, 0, 0)
        canvas.restore()

        # This makes an image interface to the Skia surface, but
        # doesn't actually copy anything yet.
        skia_image = self.root_surface.makeImageSnapshot()
        skia_bytes = skia_image.tobytes()

        depth = 32  # Bits per pixel
        pitch = 4 * WIDTH  # Bytes per row
        sdl_surface = sdl2.SDL_CreateRGBSurfaceFrom(
            skia_bytes,
            WIDTH,
            HEIGHT,
            depth,
            pitch,
            self.RED_MASK,
            self.GREEN_MASK,
            self.BLUE_MASK,
            self.ALPHA_MASK,
        )

        rect = sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT)
        window_surface = sdl2.SDL_GetWindowSurface(self.sdl_window)
        # SDL_BlitSurface is what actually does the copy.
        sdl2.SDL_BlitSurface(sdl_surface, rect, window_surface, rect)
        sdl2.SDL_UpdateWindowSurface(self.sdl_window)

    def handle_quit(self):
        sdl2.SDL_DestroyWindow(self.sdl_window)


class Tab:
    def __init__(self, tab_height):
        self.url = None
        self.history = []
        self.tab_height = tab_height
        self.focus = None

    def load(self, url, payload=None):
        headers, body = url.request(self.url, payload)

        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = []
                for origin in csp[1:]:
                    self.allowed_origins.append(URL(origin).origin())

        self.scroll = 0
        self.url = url
        self.history.append(url)
        self.nodes = HTMLParser(body).parse()

        self.rules = DEFAULT_STYLE_SHEET.copy()
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]

        for link in links:
            try:
                headers, body = url.resolve(link).request(url)
            except:
                continue
            self.rules.extend(CSSParser(body).parse())

        scripts = [
            node.attributes["src"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "script"
            and "src" in node.attributes
        ]
        self.js = JSContext(self)
        for script in scripts:
            script_url = url.resolve(script)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue
            try:
                headers, body = script_url.request(url)
            except:
                continue
            self.js.run(script, body)

        self.render()

    def allowed_request(self, url):
        return self.allowed_origins == None or url.origin() in self.allowed_origins

    def render(self):
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)

    def raster(self, canvas):
        for cmd in self.display_list:
            cmd.execute(canvas)

    def scrolldown(self):
        max_y = max(self.document.height + 2 * VSTEP - self.tab_height, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def click(self, x, y):
        y += self.scroll
        if self.focus:
            self.focus.is_focused = False
        self.focus = None
        objs = [
            obj
            for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height
        ]
        if not objs:
            return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                if self.js.dispatch_event("click", elt):
                    return
                url = self.url.resolve(elt.attributes["href"])
                return self.load(url)
            elif elt.tag == "input":
                if self.js.dispatch_event("click", elt):
                    return
                self.focus = elt
                elt.attributes["value"] = ""
                elt.is_focused = True
                return self.render()
            elif elt.tag == "button":
                if self.js.dispatch_event("click", elt):
                    return
                while elt:
                    if elt.tag == "form" and "action" in elt.attributes:
                        return self.submit_form(elt)
                    elt = elt.parent
            elt = elt.parent
        self.render()

    def submit_form(self, elt):
        if self.js.dispatch_event("submit", elt):
            return
        inputs = [
            node
            for node in tree_to_list(elt, [])
            if isinstance(node, Element)
            and node.tag == "input"
            and "name" in node.attributes
        ]
        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]
        url = self.url.resolve(elt.attributes["action"])
        self.load(url, body)

    def keypress(self, char):
        if self.focus:
            if self.js.dispatch_event("keydown", self.focus):
                return
            self.focus.attributes["value"] += char
            self.render()

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)

    def __repr__(self):
        return "Tab(history={})".format(self.history)
