#!/usr/bin/env python
# encoding: utf-8

from common import version
import string
import random
import re
import os
from file_helpers import read_contents

def main(mcd, common):
    params = common.params
    style = common.load_style()
    for (k, v) in style.iteritems():
        if k.endswith("_color") and v is None:
            style[k] = "none"
    mcd.calculate_size(style)
    result = []
    result.append("#!/usr/bin/env python")
    result.append("# encoding: utf-8")
    result.append("# %s\n" % common.timestamp())
    result.append("import time, codecs\n")
    result.append("""from math import hypot""")
    result.extend(common.process_geometry(mcd, style))
    result.append("card_max_width = %(card_max_width)s\ncard_max_height = %(card_max_height)s\ncard_margin = %(card_margin)s\narrow_width = %(arrow_width)s\narrow_half_height = %(arrow_half_height)s\narrow_axis = %(arrow_axis)s\n" % style)
    result.append(read_contents(os.path.join(params["script_directory"], "goodies.py")))
    result.append(read_contents(os.path.join(params["script_directory"], "svg_goodies.py")))
    result.append("""\nlines = '<?xml version="1.0" standalone="no"?>\\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\\n"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'""")
    result.append("""lines += '\\n\\n<svg width="%s" height="%s" view_box="0 0 %s %s"\\nxmlns="http://www.w3.org/2000/svg"\\nxmlns:link="http://www.w3.org/1999/xlink">' % (width,height,width,height)""")
    result.append(_("""lines += u'\\n\\n<desc>Generated by Mocodo {version} on {date}</desc>'""").format(version=version, date="%s") + """ % time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())""")
    result.append("""lines += '\\n\\n<rect id="frame" x="0" y="0" width="%s" height="%s" fill="%s" stroke="none" stroke-width="0"/>' % (width,height,colors['background_color'] if colors['background_color'] else "none")""")
    commands = {
        "round_rect":       """<rect x="%(x)s" y="%(y)s" width="%(w)s" height="%(h)s" fill="%(color)s" rx="%(radius)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "lower_round_rect": """<path d="%(path)s" fill="%(color)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "upper_round_rect": """<path d="%(path)s" fill="%(color)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "arrow":            """<path d="%(path)s" fill="%(stroke_color)s" stroke-width="0"/>""",
        "line_arrow":       """<path d="%(path)s" fill="%(stroke_color)s" stroke-width="0"/>""",
        "curve_arrow":      """<path d="%(path)s" fill="%(stroke_color)s" stroke-width="0"/>""",
        "line":             """<line x1="%(x0)s" y1="%(y0)s" x2="%(x1)s" y2="%(y1)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "dash_line":        """<line x1="%(x0)s" y1="%(y)s" x2="%(x1)s" y2="%(y)s" style="fill:none;stroke:%(stroke_color)s;stroke-width:%(stroke_depth)s;stroke-dasharray:%(dash_width)s;"/>""",
        "rect":             """<rect x="%(x)s" y="%(y)s" width="%(w)s" height="%(h)s" fill="%(color)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "circle":           """<circle cx="%(cx)s" cy="%(cy)s" r="%(r)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s" fill="%(color)s"/>""",
        "text":             """<text x="%(x)s" y="%(y)s" fill="%(text_color)s" font-family="%(family)s" font-size="%(size)s">%(text)s</text>""",
        "card":             """<text x="%(tx)s" y="%(ty)s" fill="%(text_color)s" font-family="%(family)s" font-size="%(size)s">%(text)s</text>""",
        "annotated_card":   """<text x="%(tx)s" y="%(ty)s" fill="%(text_color)s" font-family="%(family)s" font-size="%(size)s" onmouseover="show(evt,'%(annotation)s')" onmouseout="hide(evt)" style="cursor: pointer;">%(text)s</text>""",
        "card_underline":   """<line x1="%(x1)s" y1="%(y1)s" x2="%(x2)s" y2="%(y1)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "circle":           """<circle cx="%(cx)s" cy="%(cy)s" r="%(r)s" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s" fill="%(color)s"/>""",
        "curve":            """<path d="M%(x0)s %(y0)s C %(x1)s %(y1)s %(x2)s %(y2)s %(x3)s %(y3)s" fill="none" stroke="%(stroke_color)s" stroke-width="%(stroke_depth)s"/>""",
        "begin":            """<g id="%(id)s">""",
        "end":              """</g>""",
    }
    legs = dict((leg.identifier(), leg.value()) for row in mcd.rows for box in row for leg in box.legs)
    others = {}
    tabs = 0
    rex = re.compile(r"(?<=%\().+?(?=\)s)")
    has_annotated_card = False
    for d in mcd.description():
        if type(d) is dict:
            if d["key"] == "env":
                result.append("(%s) = (%s)" % (",".join(zip(*d["env"])[0]), ",".join(zip(*d["env"])[1])))
            else:
                if d["key"] == "card":
                    result.append('(tx,ty) = card_pos(%(ex)s,%(ey)s,%(ew)s,%(eh)s,%(ax)s,%(ay)s,k[u"%(leg_identifier)s"])' % d)
                elif d["key"] == "annotated_card":
                    result.append('(tx,ty) = card_pos(%(ex)s,%(ey)s,%(ew)s,%(eh)s,%(ax)s,%(ay)s,k[u"%(leg_identifier)s"])' % d)
                    has_annotated_card = True
                elif d["key"] == "upper_round_rect":
                    result.append('path = upper_round_rect(%(x)s,%(y)s,%(w)s,%(h)s,%(radius)s)' % d)
                elif d["key"] == "lower_round_rect":
                    result.append('path = lower_round_rect(%(x)s,%(y)s,%(w)s,%(h)s,%(radius)s)' % d)
                elif d["key"] == "arrow":
                    result.append('path = arrow(%(x)s,%(y)s,%(a)s,%(b)s)' % d)
                elif d["key"] == "line_arrow":
                    result.append('path = line_arrow(%(x0)s,%(y0)s,%(w0)s,%(h0)s,%(x1)s,%(y1)s,%(w1)s,%(h1)s,t[u"%(leg_identifier)s"])' % d)
                elif d["key"] == "curve_arrow":
                    result.append('path = curve_arrow(%(x0)s,%(y0)s,%(x1)s,%(y1)s,%(x2)s,%(y2)s,%(x3)s,%(y3)s,t[u"%(leg_identifier)s"])' % d)
                elif d["key"] in ("color", "stroke_color"):
                    others[d["key"]] = "colors['%s']" % d[d["key"]]
                elif d["key"] == "stroke_depth":
                    others["stroke_depth"] = d["stroke_depth"]
                tabs = tabs - (1 if d["key"] == "end" else 0)
                if d["key"] in commands:
                    d.update(others)
                    for k in d:
                        if type(d[k]) is str and d[k].endswith("_color"):
                            d[k] = "colors['%s']" % d[k]
                    line = commands[d["key"]]
                    sub_dict = dict((key, "%(" + key + ")s") for key in rex.findall(line))
                    for k in sub_dict:
                        if k in d and type(d[k]) is not str:
                            sub_dict[k] = d[k]
                    line = line % sub_dict
                    sub_dict = "{%s}" % ", ".join("'%s': %s" % (k, (d[k] if k in d else k)) for k in rex.findall(line))
                    result.append("lines += u\"\"\"\\n%s\"\"\"" % ("\t" * tabs + line) + " % " + str(sub_dict))
                tabs = tabs + (1 if d["key"] == "begin" else 0)
        else:
            result.append("\nlines += u\"\"\"\\n\\n<!-- %s -->\"\"\"" % d)
    if has_annotated_card and not params["hide_annotations"]:
        salt = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8)) # prevent the same identifiers to appear in several figures of the same notebook
        result.append("""annotation_overlay_height = %(annotation_overlay_height)s\nannotation_baseline = %(annotation_baseline)s\nannotation_font = %(annotation_font)s\nannotation_text_color = "%(annotation_text_color)s"\nannotation_color = "%(annotation_color)s"\nannotation_opacity = %(annotation_opacity)s\n""" % style)
        result.append("""lines += '\\n\\n<!-- Annotations -->'""")
        result.append("""lines += '\\n<script type="text/ecmascript">'""")
        result.append("""lines += '\\n<![CDATA['""")
        result.append("""lines += '\\n	function show(evt, text) {'""")
        result.append("""lines += '\\n		var pos = (evt.target.getAttribute("y") < %s) ? "bottom" : "top"' % (height - annotation_overlay_height - card_margin)""")
        result.append("""lines += '\\n		var annotation = document.getElementById(pos + "_annotation_%s")'""" % salt)
        result.append("""lines += '\\n		annotation.textContent = text'""")
        result.append("""lines += '\\n		annotation.setAttributeNS(null, "visibility", "visible");'""")
        result.append("""lines += '\\n		document.getElementById(pos + "_overlay_%s").setAttributeNS(null, "visibility", "visible");'""" % salt)
        result.append("""lines += '\\n	}'""")
        result.append("""lines += '\\n	function hide(evt) {'""")
        result.append("""lines += '\\n		document.getElementById("top_annotation_%s").setAttributeNS(null, "visibility", "hidden");'""" % salt)
        result.append("""lines += '\\n		document.getElementById("top_overlay_%s").setAttributeNS(null, "visibility", "hidden");'""" % salt)
        result.append("""lines += '\\n		document.getElementById("bottom_annotation_%s").setAttributeNS(null, "visibility", "hidden");'""" % salt)
        result.append("""lines += '\\n		document.getElementById("bottom_overlay_%s").setAttributeNS(null, "visibility", "hidden");'""" % salt)
        result.append("""lines += '\\n	}'""")
        result.append("""lines += '\\n]]>'""")
        result.append("""lines += '\\n</script>'""")
        result.append("""lines += '\\n<rect id="top_overlay_%s" x="0" y="0" width="%%s" height="%%s" fill="%%s" stroke-width="0" opacity="%%s" visibility="hidden"/>' %% (width, annotation_overlay_height, annotation_color, annotation_opacity)""" % salt)
        result.append("""lines += '\\n<text id="top_annotation_%s" text-anchor="middle" x="%%s" y="%%s" fill="%%s" font-family="%%s" font-size="%%s" visibility="hidden"></text>' %% (width/2, annotation_baseline, annotation_text_color, annotation_font['family'], annotation_font['size'])""" % salt)
        result.append("""lines += '\\n<rect id="bottom_overlay_%s" x="0" y="%%s" width="%%s" height="%%s" fill="%%s" stroke-width="0" opacity="%%s" visibility="hidden"/>' %% (height-annotation_overlay_height, width, annotation_overlay_height, annotation_color, annotation_opacity)""" % salt)
        result.append("""lines += '\\n<text id="bottom_annotation_%s" text-anchor="middle" x="%%s" y="%%s" fill="%%s" font-family="%%s" font-size="%%s" visibility="hidden"></text>' %% (width/2, height-annotation_overlay_height+annotation_baseline, annotation_text_color, annotation_font['family'], annotation_font['size'])""" % salt)
    result.append("""lines += u'\\n</svg>'""")
    result.append("""\nwith codecs.open("%(output_name)s.svg", "w", "utf8") as f:\n    f.write(lines)""" % params)
    result.append((_("""safe_print_for_PHP(u'Output file "{output_name}.svg" successfully generated.')""").format(output_name=params["output_name"])))
    common.dump_output_file("\n".join(result))


if __name__ == "__main__":
    from argument_parser import parsed_arguments
    from mcd import Mcd
    from common import Common
    clauses = u"""
        CLIENT: Réf. client, Nom, Prénom, Adresse
        PASSER, 0N CLIENT, 11 COMMANDE
        COMMANDE: Num commande, Date, Montant
        INCLURE, 1N COMMANDE, 0N PRODUIT: Quantité
        PRODUIT: Réf. produit, Libellé, Prix unitaire
    """.replace("  ", "").split("\n")
    params = parsed_arguments()
    params["image_format"] = "svg"
    common = Common(params)
    mcd = Mcd(clauses, params)
    main(mcd, common)