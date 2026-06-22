# generators/bootstrap_generator.py
import re
from .utils import normalize_style, parse_element, dedupe_ordered

class BootstrapGenerator:
    def __init__(self):
        self._size_tol = 1.5

        # Escalas Bootstrap
        self._SPACING = {0:"0", 4:"1", 8:"2", 16:"3", 24:"4", 48:"5"}
        self._FS = {12:"fs-6", 14:"fs-5", 16:"fs-4", 20:"fs-3", 24:"fs-2", 32:"fs-1"}
        self._OPACITY = {0:"opacity-0", 25:"opacity-25", 50:"opacity-50", 75:"opacity-75", 100:"opacity-100"}

        # cores (~aprox)
        self._BG = {"#000000":"bg-black", "#ffffff":"bg-white", "#007bff":"bg-primary", "#f8f9fa":"bg-light", "#343a40":"bg-dark"}
        self._TEXT = {"#000000":"text-black", "#ffffff":"text-white", "#333333":"text-dark", "#6c757d":"text-secondary", "#212529":"text-body"}
        self._BORDER_COLOR = {"#000000":"border-black", "#ffffff":"border-white", "#007bff":"border-primary", "#6c757d":"border-secondary", "#343a40":"border-dark", "#f8f9fa":"border-light"}

        # remoção de Tailwind já presente
        self._TLW_PATTERNS = [
            r"^bg-\[", r"^text-\[", r"^border-\[", r"^rounded-\[", r"^leading-",
            r"^(block|inline|inline-block|flex|grid)$", r"^(p|px|py|pt|pr|pb|pl|m|mx|my|mt|mr|mb|ml)-",
            r"^shadow", r"^cursor-", r"^w-", r"^h-", r"^min-w-", r"^min-h-", r"^max-w-", r"^max-h-",
        ]

    
    def _first(self, props, *names):
        for n in names:
            if n in props:
                return props[n]
        return None

    def _nearest(self, x, keys): return min(keys, key=lambda k: abs(float(x) - float(k)))
    def _num(self, v):
        try: return float(str(v).replace("px","").strip())
        except: return None
    def _pct(self, v):
        s = str(v).strip()
        return float(s[:-1]) if s.endswith("%") and s[:-1].replace(".", "", 1).isdigit() else None

    def _bg_color(self, v):  return self._BG.get(str(v).lower())
    def _text_color(self, v): return self._TEXT.get(str(v).lower())

    def _opacity(self, v):
        n = self._num(v)
        if n is None: return None
        pct = round(max(0, min(1, n)) * 100) if n <= 1 else round(max(0, min(100, n)))
        nearest = self._nearest(pct, self._OPACITY.keys())
        return self._OPACITY[nearest]

    def _font_size(self, v):
        n = self._num(v)
        if n is None: return None
        nearest = self._nearest(n, self._FS.keys())
        return self._FS[nearest] if abs(n - nearest) <= self._size_tol else None

    def _line_height(self, v):
        s = str(v).strip().lower()
        if s in ("normal", "", "none"): return None
        n = self._num(s)
        if n is None:
            try: n = float(s)
            except: return None
        opts = {1.0:"lh-1", 1.25:"lh-sm", 1.5:"lh-base", 2.0:"lh-lg"}
        nearest = self._nearest(n, opts.keys())
        return opts[nearest] if abs(n - nearest) <= 0.15 else None

    def _font_weight(self, v):
        n = self._num(v)
        if n is None:
            if str(v).strip().lower() == "bold": return "fw-bold"
            return None
        if n >= 700: return "fw-bold"
        if 500 <= n < 700: return "fw-semibold"
        if 300 <= n < 500: return "fw-light"
        return "fw-normal"

    def _text_align(self, v):
        s = str(v).strip().lower()
        return {"start":"text-start","left":"text-start","center":"text-center","end":"text-end","right":"text-end","justify":"text-justify"}.get(s)

    def _display(self, v):
        s = str(v).strip().lower()
        return f"d-{s}" if s in ("block","inline","inline-block","flex","grid") else None

    def _cursor(self, v):
        s = str(v).strip().lower()
        return f"cursor-{s}" if s in ("auto","pointer","text","not-allowed","default") else None

    def _spacing_token(self, v):
        n = self._num(v)
        if n is None: return None
        nearest = self._nearest(n, self._SPACING.keys())
        return self._SPACING[nearest]

    def _padding_shorthand(self, v):
        raw = str(v).replace("px"," ").replace(",", " ")
        parts = [p for p in raw.split() if p]
        out = []
        if len(parts) == 1:
            t = self._spacing_token(parts[0]);  out += [f"p-{t}"] if t else []
        elif len(parts) == 2:
            tv = self._spacing_token(parts[0]); th = self._spacing_token(parts[1])
            if tv: out.append(f"py-{tv}")
            if th: out.append(f"px-{th}")
        elif len(parts) == 3:
            tt = self._spacing_token(parts[0]); th = self._spacing_token(parts[1]); tb = self._spacing_token(parts[2])
            if tt: out.append(f"pt-{tt}")
            if th: out.append(f"px-{th}")
            if tb: out.append(f"pb-{tb}")
        elif len(parts) == 4:
            tt = self._spacing_token(parts[0]); tr = self._spacing_token(parts[1]); tb = self._spacing_token(parts[2]); tl = self._spacing_token(parts[3])
            if tt: out.append(f"pt-{tt}")
            if tr: out.append(f"pe-{tr}")
            if tb: out.append(f"pb-{tb}")
            if tl: out.append(f"ps-{tl}")
        return out

    def _border_width(self, v):
        n = self._num(v)
        if n is None: return None
        bw = min(5, max(0, round(n)))
        return f"border-{bw}" if bw > 0 else "border-0"

    def _border_radius(self, v):
        n = self._num(v)
        if n is None: return None
        if n <= 0: return "rounded-0"
        if n <= 3: return "rounded-1"
        if n <= 6: return "rounded-2"
        if n <= 12: return "rounded-3"
        return "rounded"

    def _border_style(self, _):
        return None

    def _border_color(self, v): return self._BORDER_COLOR.get(str(v).lower())

    def _box_shadow(self, v):
        s = str(v).strip().lower()
        if s == "none": return "shadow-none"
        nums = re.findall(r"[-+]?\d*\.?\d+", s)
        try: blur = float(nums[2]) if len(nums) >= 3 else 4.0
        except: blur = 4.0
        if blur <= 3: return "shadow-sm"
        if blur >= 12: return "shadow-lg"
        return "shadow"

    def _position(self, v):
        s = str(v).strip().lower()
        return f"position-{s}" if s in ("static","relative","absolute","fixed","sticky") else None

    def _offset_percent(self, prop, val):
        p = self._pct(val)
        if p is None: return None
        nearest = min((0,50,100), key=lambda k: abs(p - k))
        if abs(p - nearest) > 5: return None
        side = {"top":"top","bottom":"bottom","left":"start","right":"end"}[prop]
        return f"{side}-{nearest}"

    def _width_util(self, v):
        p = self._pct(v)
        if p is not None:
            nearest = min((25,50,75,100), key=lambda k: abs(p - k))
            if abs(p - nearest) <= 8: return f"w-{nearest}"
            return "w-100" if nearest == 100 else None
        if str(v).strip().lower() == "auto": return "w-auto"
        return None

    def _height_util(self, v):
        p = self._pct(v)
        if p is not None:
            nearest = min((25,50,75,100), key=lambda k: abs(p - k))
            if abs(p - nearest) <= 8: return f"h-{nearest}"
            return "h-100" if nearest == 100 else None
        if str(v).strip().lower() == "auto": return "h-auto"
        return None

    def _maxmin_wh(self, prop, v):
        if str(v).strip() == "100%":
            return "mw-100" if "width" in prop else "mh-100"
        return None

    def _filter_tailwind(self, classes):
        return [c for c in classes if not any(re.search(p, c) for p in self._TLW_PATTERNS)]

    # ---- principal
    def generate(self, html_raw: str) -> str:
        el = parse_element(html_raw)
        props = normalize_style(el.style_dict)
        out = []

        # cores / opacidade
        bgv = self._first(props, "background-color", "background")
        if bgv:
            cls = self._bg_color(bgv)
            if cls: out.append(cls)
        if "color" in props:
            cls = self._text_color(props["color"])
            if cls: out.append(cls)
        if "opacity" in props:
            cls = self._opacity(props["opacity"]);  out += [cls] if cls else []

        # tipografia
        if "font-size" in props:
            cls = self._font_size(props["font-size"]);  out += [cls] if cls else []
        if "line-height" in props:
            cls = self._line_height(props["line-height"]); out += [cls] if cls else []
        if "font-weight" in props:
            cls = self._font_weight(props["font-weight"]); out += [cls] if cls else []
        if "text-align" in props:
            cls = self._text_align(props["text-align"]); out += [cls] if cls else []

        # layout
        if "display" in props:
            cls = self._display(props["display"]); out += [cls] if cls else []
        if "cursor" in props:
            cls = self._cursor(props["cursor"]); out += [cls] if cls else []
        if "position" in props:
            cls = self._position(props["position"]); out += [cls] if cls else []
        for prop in ("top","right","bottom","left"):
            if prop in props:
                cls = self._offset_percent(prop, props[prop]); out += [cls] if cls else []

        # padding
        padv = self._first(props, "padding")
        if padv: out += self._padding_shorthand(padv)
        for side, pre in (("padding-top","pt"),("padding-right","pe"),("padding-bottom","pb"),("padding-left","ps")):
            if side in props:
                tok = self._spacing_token(props[side]);  out += [f"{pre}-{tok}"] if tok else []

        # borda
        if "border" in props:
            out.append("border-0" if str(props["border"]).strip().lower() == "none" else "border")
        if "border-width" in props:
            cls = self._border_width(props["border-width"]); out += [cls] if cls else []
        if "border-style" in props:
            cls = self._border_style(props["border-style"]); out += [cls] if cls else []
        if "border-color" in props:
            cls = self._border_color(props["border-color"]); out += [cls] if cls else []
        if "border-radius" in props:
            cls = self._border_radius(props["border-radius"]); out += [cls] if cls else []

        # sombra
        if "box-shadow" in props:
            cls = self._box_shadow(props["box-shadow"]); out += [cls] if cls else []

        # dimensões
        if "width" in props:
            cls = self._width_util(props["width"]); out += [cls] if cls else []
        if "height" in props:
            cls = self._height_util(props["height"]); out += [cls] if cls else []
        for prop in ("max-width","max-height","min-width","min-height"):
            if prop in props:
                cls = self._maxmin_wh(prop, props[prop]); out += [cls] if cls else []

        keep = self._filter_tailwind(el.existing_classes)
        classes = dedupe_ordered(out + keep)

        # redundâncias
        if "btn-primary" in classes and "text-white" in classes:
            classes = [c for c in classes if c != "text-white"]

        classes.append(el.hash)
        return el.replace_classes(classes)
