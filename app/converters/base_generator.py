from bs4 import BeautifulSoup
import hashlib
import re

CSS_RELEVANT_PROPS = {
    # Cores e fundos
    "background-color", "color", "opacity",

    # Espaçamento
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",

    # Bordas
    "border", "border-radius", "border-style", "border-width",
    "border-color", "box-shadow",

    # Layout
    "display", "cursor", "position", "top", "right", "bottom", "left",

    # Tipografia básica
    "font-size", "line-height", "font-family", "font-weight", "text-align",

    # Outras propriedades úteis
    "width", "height", "max-width", "max-height", "min-width", "min-height"
}

def normalize_color(value: str) -> str:
    if value.startswith("rgb"):
        parts = re.findall(r"\d+", value)
        if len(parts) >= 3:
            r, g, b = map(int, parts[:3])
            return f"#{r:02x}{g:02x}{b:02x}".upper()
    return value


def parse_inline_style(style_str: str) -> dict:
    styles = {}
    for part in style_str.split(";"):
        if ":" not in part:
            continue

        k, v = part.split(":", 1)
        prop = k.strip().lower()
        val = v.strip()

        if not prop or not val:
            continue

        if prop in CSS_RELEVANT_PROPS:
            if "color" in prop:
                val = normalize_color(val)

            if "px" in val:
                val = val.replace("px", "")

            styles[prop] = val

    paddings = {k: v for k, v in styles.items() if k.startswith("padding-")}
    if len(paddings) == 4 and len(set(paddings.values())) <= 2:
        vertical = paddings["padding-top"]
        horizontal = paddings["padding-right"]
        styles["padding"] = f"{vertical}px {horizontal}px"
        for k in paddings:
            styles.pop(k)

    return styles


def style_dict_to_css(d: dict) -> str:
    return ";\n  ".join(f"{k}: {v}" for k, v in sorted(d.items()))


class BaseGenerator:
    def generate(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find()
        if not tag:
            return html

        inline = tag.get("style")
        if not inline:
            return str(tag)

        styles = parse_inline_style(inline)

        # Adiciona valores default importantes
        if tag.name == "button":
            if "border" not in styles:
                styles["border"] = "none"
            if "border-radius" not in styles:
                styles["border-radius"] = "4px"

        if not styles:
            tag.attrs.pop("style", None)
            return str(tag)

        signature = style_dict_to_css(styles)

        existing = tag.get("class", [])
        if not existing:
            tag["class"] = []

        tag.attrs.pop("style", None)

        class_name = ''.join(filter(str.isalpha, hashlib.md5(signature.encode('utf-8')).hexdigest()))[:8]
        tag["class"].append(class_name)

        css = f".{class_name} {{\n  {signature}\n}}"

        return f"{str(tag)}\n\n<style>\n{css}\n</style>"