from bs4 import BeautifulSoup
import re

# ------------------------------
# Helpers para parsing
# ------------------------------

class ParsedElement:
    def __init__(self, tag, style_dict, existing_classes, hash_, original_soup, node):
        self.tag = tag
        self.style_dict = style_dict
        self.existing_classes = existing_classes
        self.hash = hash_
        self._soup = original_soup
        self._node = node

    def replace_classes(self, new_classes):
        """Substitui classes no HTML e retorna HTML atualizado."""
        self._node['class'] = new_classes
        return str(self._node)


CSS_RELEVANT_PROPS = {
    "background-color", "background", "color", "cursor",
    "font-size", "line-height", "font-family", "display"
}

def _parse_decl_block(block: str) -> dict:
    out = {}
    for line in block.split(";"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        prop = k.strip().lower()
        val = v.strip()
        if prop in CSS_RELEVANT_PROPS and val:
            out[prop] = val
    return out

def parse_element(html_raw: str):
    soup = BeautifulSoup(html_raw, "html.parser")
    node = soup.find()
    if not node:
        raise ValueError("HTML vazio ou inválido")

    tag = node.name
    classes = node.get("class", []) or []
    existing_classes, hash_class = [], ""
    for c in classes:
        if re.fullmatch(r"[0-9a-f]{8}", c):
            hash_class = c
        else:
            existing_classes.append(c)

    # 1) Primeiro tenta inline
    style_dict = {}
    inline = node.get("style")
    if inline:
        style_dict.update(_parse_decl_block(inline))

    # 2) Se não houver inline suficiente, busca no <style> pela .<hash>
    if not style_dict and hash_class:
        # pega TODO o CSS concatenado de todos <style>
        css_text = "\n".join(s.get_text() for s in soup.find_all("style"))
        # regex tolerante a espaços e quebras de linha
        # captura o bloco entre { ... } da classe .<hash>
        m = re.search(
            r"\." + re.escape(hash_class) + r"\s*\{\s*([^}]*)\s*\}",
            css_text, flags=re.I | re.M | re.S
        )
        if m:
            style_dict.update(_parse_decl_block(m.group(1)))

    # Normaliza background → p['bg']
    if "background" in style_dict and "background-color" not in style_dict:
        style_dict["background-color"] = style_dict["background"]

    return ParsedElement(
        tag=tag,
        style_dict=style_dict,
        existing_classes=existing_classes,
        hash_=hash_class,
        original_soup=soup,
        node=node
    )

# ------------------------------
# Normalizadores e helpers
# ------------------------------

def normalize_style(style_dict):
    """
    Normaliza propriedades: converte px → número, rgb → string simples etc.
    """
    props = {}
    for k, v in style_dict.items():
        if k in ["font-size", "line-height"]:
            # extrair número
            m = re.match(r"([\d.]+)", v)
            props[k] = float(m.group(1)) if m else None
        elif k in ["color", "background", "background-color"]:
            props["color" if "color" in k and "background" not in k else "bg"] = v
        elif k == "font-family":
            if "mono" in v: props[k] = "monospace"
            elif "serif" in v: props[k] = "serif"
            else: props[k] = "sans-serif"
        elif k == "font-weight":
            if "bold" in v: props[k] = "bold"
            else: props[k] = "normal"
        elif k == "display":
            props[k] = v
        else:
            props[k] = v
    return props


def approx(value, target, tol=1.5):
    try:
        return abs(float(value) - target) <= tol
    except:
        return False


def is_gray(color: str) -> bool:
    if not color: return False
    m = re.findall(r"(\d+)", color)
    if len(m) >= 3:
        r, g, b = map(int, m[:3])
        return abs(r - g) < 10 and abs(g - b) < 10
    return False


def is_color(color: str, kind: str) -> bool:
    if not color: return False
    color = color.lower()
    if kind == "primary":
        return "0, 123, 255" in color or "#007bff" in color
    if kind == "secondary":
        return "108, 117, 125" in color or "#6c757d" in color
    return False


def sanitize_bootstrap(classes):
    tw_prefixes = (
        "text-[", "bg-[",  # Permite valores arbitrários
        "text-gray-", "bg-gray-",
        "hover:", "focus:",
        "leading-", "font-"
    )
    return [c for c in classes if not any(c.startswith(p) for p in tw_prefixes)]


def sanitize_tailwind(classes):
    forbidden = ["btn", "form-control", "form-select", "display-", "fs-", "fw-", "lh-"]
    return [c for c in classes if not any(c.startswith(f) for f in forbidden)]


def dedupe_ordered(seq):
    seen = set()
    out = []
    for c in seq:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out
