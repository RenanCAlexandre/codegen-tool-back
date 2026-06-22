# generators/tailwind_generator.py
import re
from .utils import normalize_style, parse_element, dedupe_ordered

class TailwindGenerator:
    def __init__(self, allow_arbitrary: bool = True):
        self.allow_arbitrary = allow_arbitrary
        self._size_tol = 1.5

        self._SPACING = {0:"0",2:"0.5",4:"1",6:"1.5",8:"2",10:"2.5",12:"3",14:"3.5",16:"4",20:"5",24:"6",28:"7",32:"8",36:"9",40:"10",48:"12"}
        self._FS = {12:"text-xs",14:"text-sm",16:"text-base",20:"text-xl",24:"text-2xl",32:"text-3xl"}
        self._LEADING = {1.0:"leading-none",1.25:"leading-tight",1.375:"leading-snug",1.5:"leading-normal",1.625:"leading-relaxed",2.0:"leading-loose"}

        self._BG = {"#000000":"bg-black","#ffffff":"bg-white","#007bff":"bg-blue-600"}
        self._TEXT = {"#000000":"text-black","#ffffff":"text-white","#333333":"text-neutral-700"}
        self._BORDER_COLOR = {"#000000":"border-black","#ffffff":"border-white","#007bff":"border-blue-600","#333333":"border-neutral-700"}

        # remover Bootstrap já presente
        self._BS_PATTERNS = [r"^btn", r"^d-", r"^fs-", r"^lh-", r"^text-(primary|secondary|success|danger|warning|info|light|dark|black|white)$",
                             r"^bg-(primary|secondary|success|danger|warning|info|light|dark|black|white)$",
                             r"^(p|px|py|pt|pr|pb|pl|m|mx|my|mt|mr|mb|ml)-", r"^rounded(-\d)?$", r"^border(-\d)?$", r"^position-", r"^(top|bottom|start|end)-",
                             r"^opacity-\d+$", r"^shadow"]

    # ---- helpers
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
    def _arb(self, prefix, raw): return f"{prefix}-[{raw}]" if self.allow_arbitrary else None

    # ---- mapeamentos
    def _bg(self, v):
        key = str(v).lower()
        return self._BG.get(key, self._arb("bg", key))

    def _text(self, v):
        key = str(v).lower()
        return self._TEXT.get(key, self._arb("text", key))

    def _opacity(self, v):
        n = self._num(v)
        if n is None: return None
        pct = round(max(0, min(1, n)) * 100) if n <= 1 else round(max(0, min(100, n)))
        step = round(pct / 5) * 5
        if abs(step - pct) <= 3:
            return f"opacity-{int(step)}"
        return self._arb("opacity", str(pct/100))

    def _font_size(self, v):
        n = self._num(v)
        if n is None: return None
        nearest = self._nearest(n, self._FS.keys())
        return self._FS[nearest] if abs(n - nearest) <= self._size_tol else self._arb("text", f"{n}px")

    def _line_height(self, v):
        s = str(v).strip().lower()
        if s in ("normal", "", "none"): return "leading-normal"
        n = self._num(s)
        if n is None:
            try: n = float(s)
            except: return None
        nearest = self._nearest(n, self._LEADING.keys())
        return self._LEADING[nearest] if abs(n - nearest) <= 0.15 else self._arb("leading", str(n))

    def _font_weight(self, v):
        n = self._num(v)
        if n is None:
            if str(v).strip().lower() == "bold": return "font-bold"
            return None
        if n >= 800: return "font-extrabold"
        if 700 <= n < 800: return "font-bold"
        if 600 <= n < 700: return "font-semibold"
        if 500 <= n < 600: return "font-medium"
        if 400 <= n < 500: return "font-normal"
        if 300 <= n < 400: return "font-light"
        return "font-normal"

    def _text_align(self, v):
        s = str(v).strip().lower()
        return {"start":"text-left","left":"text-left","center":"text-center","end":"text-right","right":"text-right","justify":"text-justify"}.get(s)

    def _display(self, v):
        s = str(v).strip().lower()
        return s if s in ("block","inline","inline-block","flex","grid") else None

    def _cursor(self, v):
        s = str(v).strip().lower()
        return f"cursor-{s}" if s in ("auto","pointer","text","not-allowed","default") else None

    def _spacing_tok(self, v):
        n = self._num(v)
        if n is None: return None
        nearest = self._nearest(n, self._SPACING.keys())
        if abs(n - nearest) <= 1.0:
            return self._SPACING[nearest]
        return self._arb("", f"{n}px")

    def _pad_sh(self, v):
        raw = str(v).replace("px"," ").replace(",", " ")
        pr = [p for p in raw.split() if p]
        out = []
        if len(pr) == 1:
            t = self._spacing_tok(pr[0]);
            if t: out.append(f"p-{t}" if not t.startswith("[") else f"p-{t}")
        elif len(pr) == 2:
            tv = self._spacing_tok(pr[0]); th = self._spacing_tok(pr[1])
            if tv: out.append(f"py-{tv}")
            if th: out.append(f"px-{th}")
        elif len(pr) == 3:
            tt = self._spacing_tok(pr[0]); th = self._spacing_tok(pr[1]); tb = self._spacing_tok(pr[2])
            if tt: out.append(f"pt-{tt}")
            if th: out.append(f"px-{th}")
            if tb: out.append(f"pb-{tb}")
        elif len(pr) == 4:
            tt = self._spacing_tok(pr[0]); tr = self._spacing_tok(pr[1]); tb = self._spacing_tok(pr[2]); tl = self._spacing_tok(pr[3])
            if tt: out.append(f"pt-{tt}")
            if tr: out.append(f"pr-{tr}")
            if tb: out.append(f"pb-{tb}")
            if tl: out.append(f"pl-{tl}")
        return out

    def _border_width(self, v):
        n = self._num(v)
        if n is None: return None
        if n == 0: return "border-0"
        nearest = self._nearest(n, (1,2,4,8))
        if abs(n - nearest) <= 0.75:
            return {1:"border",2:"border-2",4:"border-4",8:"border-8"}[nearest]
        return self._arb("border", f"{n}px")

    def _border_style(self, v):
        s = str(v).strip().lower()
        return {"none":"border-none","solid":"border-solid","dashed":"border-dashed","dotted":"border-dotted","double":"border-double"}.get(s)

    def _border_color(self, v):
        key = str(v).lower()
        return self._BORDER_COLOR.get(key, self._arb("border", key))

    def _radius(self, v):
        n = self._num(v)
        if n is None: return None
        if n <= 0: return "rounded-none"
        if n <= 2: return "rounded-sm"
        if n <= 4: return "rounded"
        if n <= 6: return "rounded-md"
        if n <= 8: return "rounded-lg"
        if n <=12: return "rounded-xl"
        if n <=16: return "rounded-2xl"
        return self._arb("rounded", f"{n}px")

    def _shadow(self, v):
        s = str(v).strip().lower()
        if s == "none": return "shadow-none"
        nums = re.findall(r"[-+]?\d*\.?\d+", s)
        try: blur = float(nums[2]) if len(nums) >= 3 else 4.0
        except: blur = 4.0
        if blur <= 3: return "shadow-sm"
        if blur <= 8: return "shadow"
        if blur <= 14: return "shadow-md"
        if blur <= 20: return "shadow-lg"
        return "shadow-xl"

    def _position(self, v):
        s = str(v).strip().lower()
        return s if s in ("static","relative","absolute","fixed","sticky") else None

    def _offset(self, prop, val):
        s = str(val).strip()
        if s in ("auto",""): return None
        p = self._pct(s)
        if p is not None:
            if abs(p - 0) <= 1: tok = "0"
            elif abs(p - 50) <= 1: tok = "1/2"
            elif abs(p - 100) <= 1: tok = "full"
            else: tok = None
            return f"{prop}-{tok}" if tok else self._arb(prop, s)
        n = self._num(s)
        return self._arb(prop, f"{n}px") if n is not None else self._arb(prop, s)

    def _width_like(self, prefix, v):
        s = str(v).strip().lower()
        if s == "auto": return f"{prefix}-auto"
        p = self._pct(s)
        if p is not None:
            if abs(p - 25) <= 1:  return f"{prefix}-1/4"
            if abs(p - 33.333) <= 1.5: return f"{prefix}-1/3"
            if abs(p - 50) <= 1:  return f"{prefix}-1/2"
            if abs(p - 66.667) <= 1.5: return f"{prefix}-2/3"
            if abs(p - 75) <= 1:  return f"{prefix}-3/4"
            if abs(p - 100) <= 1: return f"{prefix}-full"
            return self._arb(prefix, s)
        n = self._num(s)
        return self._arb(prefix, f"{n}px") if n is not None else None

    def _filter_bootstrap(self, classes):
        return [c for c in classes if not any(re.search(p, c) for p in self._BS_PATTERNS)]

    # ---- principal
    def generate(self, html_raw: str) -> str:
        el = parse_element(html_raw)
        props = normalize_style(el.style_dict)
        out = []

        # cores / opacidade
        bgv = self._first(props, "background-color", "background")
        if bgv: out.append(self._bg(bgv))
        if "color" in props: out.append(self._text(props["color"]))
        if "opacity" in props:
            cls = self._opacity(props["opacity"]);  out += [cls] if cls else []

        # tipografia
        if "font-size" in props:
            cls = self._font_size(props["font-size"]); out += [cls] if cls else []
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
                cls = self._offset(prop, props[prop]); out += [cls] if cls else []

        # padding
        padv = self._first(props, "padding")
        if padv: out += self._pad_sh(padv)
        for side, pre in (("padding-top","pt"),("padding-right","pr"),("padding-bottom","pb"),("padding-left","pl")):
            if side in props:
                tok = self._spacing_tok(props[side])
                if tok: out.append(f"{pre}-{tok}" if not tok.startswith("[") else f"{pre}-{tok}")

        # borda
        if "border" in props:
            b = str(props["border"]).strip().lower()
            out.append("border-none" if b == "none" else "border")
        if "border-width" in props:
            cls = self._border_width(props["border-width"]); out += [cls] if cls else []
        if "border-style" in props:
            cls = self._border_style(props["border-style"]); out += [cls] if cls else []
        if "border-color" in props:
            out.append(self._border_color(props["border-color"]))
        if "border-radius" in props:
            cls = self._radius(props["border-radius"]); out += [cls] if cls else []

        # sombra
        if "box-shadow" in props:
            cls = self._shadow(props["box-shadow"]); out += [cls] if cls else []

        # dimensões
        for prop, pre in (("width","w"),("height","h"),("max-width","max-w"),("max-height","max-h"),("min-width","min-w"),("min-height","min-h")):
            if prop in props:
                cls = self._width_like(pre, props[prop]); out += [cls] if cls else []

        keep = self._filter_bootstrap(el.existing_classes)
        classes = dedupe_ordered([c for c in out if c] + keep)
        classes.append(el.hash)
        return el.replace_classes(classes)
