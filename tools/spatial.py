"""Orthographic projections and SVG presets for lessons with shared space points."""
from html import escape
from math import hypot, sqrt


def spatial_panel(model, points, steps, draw, fields, number, words, reference):
    fields(model, ("points", "views", "segments", "markers", "right_angles"), (), "space")

    def coordinate(point):
        if not isinstance(point, str) or point not in points:
            raise ValueError(f"未知空间点：{point}")
        return points[point]

    def stage(item):
        value = item.get("step", 0)
        if type(value) is not int or not 0 <= value <= steps:
            raise ValueError("空间图的 step 必须是有效的作图步骤")
        return value

    def wrap(stage_index, content):
        hidden = ' class="is-hidden"' if stage_index else ""
        return f'<g data-space-step="{stage_index}"{hidden}>{content}</g>'

    for key in ("segments", "markers", "right_angles"):
        if not isinstance(model[key], list):
            raise ValueError(f"space.{key} 需要列表")

    # Unit screen bases. W shows +y to the right and +z upwards, like the paper drawing.
    presets = (
        ("oblique", "空间关系", (-.8, .6, 0), (.3, .4, .8660254),
         "蓝色为侧投影面 W，暖灰色为水平投影面 H。沿虚线追踪空间点在 W 面上的落点。"),
        ("side", "看向侧面 W", (0, 1, 0), (0, 0, 1),
         "沿 X 轴看过去，X 轴积聚为 O。MN 平行于 W 面，在这个方向显示实长。"),
    )
    dot = lambda a, b: sum(x*y for x, y in zip(a, b))
    sub = lambda a, b: tuple(x-y for x, y in zip(a, b))
    unit = lambda a: tuple(x / sqrt(dot(a, a)) for x in a)

    bases = [(key, title, unit(right), unit(up), note) for key, title, right, up, note in presets]
    x_end = max(p[0] for p in points.values())
    y_min = min(0, min(p[1] for p in points.values())) - 18
    y_max = max(0, max(p[1] for p in points.values())) + 24
    z_top = max(0, max(p[2] for p in points.values())) + 24
    horizontal = [(0,y_min,0), (x_end,y_min,0), (x_end,y_max,0), (0,y_max,0)]
    wall = [(0,y_min,0), (0,y_max,0), (0,y_max,z_top), (0,y_min,z_top)]
    bounds = []
    for _, _, right, up, _ in bases:
        xs = [dot(point, right) for point in [*points.values(), *wall, *horizontal]]
        ys = [-dot(point, up) for point in [*points.values(), *wall, *horizontal]]
        bounds.append((min(xs), max(xs), min(ys), max(ys)))
    scale = min(445 / max(max(r-l for l,r,_,_ in bounds), 1),
                230 / max(max(b-t for _,_,t,b in bounds), 1))
    panels = []
    for (key, title, right, up, note), (left, right_edge, top, bottom) in zip(bases, bounds):
        def project(point):
            return [270 + scale*(dot(point, right) - (left+right_edge)/2),
                    142 + scale*(-dot(point, up) - (top+bottom)/2)]

        def face(corners, cls):
            vertices = " ".join(",".join(number(v, "投影面") for v in project(p)) for p in corners)
            return f'<polygon points="{vertices}" class="{cls}"/>'

        def segment(a, b, role="outline"):
            return draw({"type": "line", "from": project(a), "to": project(b), "role": role}, "空间投影")

        def caption(p, title, dx=0, dy=0):
            x, y = project(p)
            return draw({"type": "label", "at": [x+dx, y+dy], "text": title, "role": "view"}, "投影面名称")

        content = []
        if key == "oblique":
            content.extend([face(horizontal, "h-plane"), caption((x_end,y_max,0), "水平面 H", -45, 54)])
        content.append(face(wall, "w-plane"))
        if key == "side":
            content.append(caption((0,y_max,0), "侧投影面 W", -104, -9))
        else:
            content.append(caption((0,y_max,z_top), "侧投影面 W", -100, 18))
            content.append(caption((0,0,0), "O", 7, 15))

        for item in model["segments"]:
            a, b = coordinate(item["from"]), coordinate(item["to"])
            if item.get("role") == "axis":
                continue
            projected = [(0,p[1],p[2]) for p in (a,b)]
            guides = ""
            if key == "oblique":
                guides = "".join(segment(p,q,"construction") for p,q in zip((a,b), projected) if p != q)
                guides += segment(*projected)
            content.append(wrap(stage(item), f'<g class="space-projection">{guides}</g>'))

        for item in model["segments"]:
            fields(item, ("from", "to"), ("label", "role", "step"), "space.segments")
            a, b = coordinate(item["from"]), coordinate(item["to"])
            p, q = project(a), project(b)
            role = item.get("role", "outline")
            if role not in ("axis", "outline", "result"):
                raise ValueError("空间线段的 role 应为 axis、outline 或 result")
            collapsed = hypot(*sub(p, q)) < .001
            if collapsed:
                geometry = draw({"type": "dot", "at": p}, "空间点")
            else:
                geometry = draw({"type": "line", "from": p, "to": q}, "空间线段")
            if "label" in item:
                label = words(item["label"], "space.segments.label")
                at = [p[0]-23, p[1]+22] if collapsed else [q[0]-27, q[1]+20]
                geometry += draw({"type": "label", "at": at, "text": "O" if collapsed and role=="axis" else label}, "空间线段标签")
            content.append(wrap(stage(item), f'<g class="space-{role}">{geometry}</g>'))
        for item in model["right_angles"]:
            fields(item, ("vertex", "arms"), ("step",), "space.right_angles")
            p = coordinate(item["vertex"])
            if not isinstance(item["arms"], list) or len(item["arms"]) != 2:
                raise ValueError("直角标记需要两个臂端点")
            arms = [sub(coordinate(arm), p) for arm in item["arms"]]
            if any(dot(arm, arm) == 0 for arm in arms):
                raise ValueError("直角臂不能为零")
            # Suppress a marker when one of its arms projects to a point.
            if any(hypot(dot(arm,right), dot(arm,up)) < .001 for arm in arms):
                continue
            u, v = [tuple(x*12/scale for x in unit(arm)) for arm in arms]
            corners = [project(tuple(x+a+b for x,a,b in zip(p, du, dv)))
                       for du,dv in ((u,(0,0,0)),(u,v),((0,0,0),v))]
            mark = draw({"type":"polyline","points":corners}, "空间直角")
            content.append(wrap(stage(item), f'<g class="space-result">{mark}</g>'))
        for item in model["markers"]:
            fields(item, ("point",), ("step", "project"), "space.markers")
            name = item["point"]
            at = project(coordinate(name))
            x,y = (number(n,"空间标记") for n in at)
            if key == "oblique" and item.get("project", False):
                projected = (0, *coordinate(name)[1:])
                px, py = project(projected)
                content.append(wrap(stage(item),
                    f'<g class="space-projection"><circle cx="{number(px,"投影")}" cy="{number(py,"投影")}" r="3"/>'
                    + caption(projected, name.lower()+"″", 7, -7) + "</g>"))

            label = escape(name)
            display = label if key == "oblique" else label.lower() + "″"
            label_y = at[1] + 22 if key == "oblique" and name == "B" else at[1] - 9
            if key == "oblique" and at[0] > 450:
                x_label = at[0]-22
            else:
                x_label = at[0]+9
            content.append(wrap(stage(item),
                f'<g class="space-point" data-point="{reference(name)}" role="button" tabindex="0" aria-label="对照点 {label}" aria-pressed="false">'
                f'<circle class="point-hit" cx="{x}" cy="{y}" r="16"/>'
                f'<circle cx="{x}" cy="{y}" r="4"/>'
                f'<text x="{number(x_label,"点名")}" y="{number(label_y,"点名")}">{display}</text></g>'))
        hidden = ' hidden' if key != "oblique" else ''
        panels.append(f'<div data-space-view="{key}"{hidden}><svg viewBox="0 0 540 284" role="group" aria-label="{title}">'
                      + "".join(content) + f'</svg><p class="space-note">{note}</p></div>')

    return ('<section class="space-panel" id="space-panel" aria-labelledby="space-title"><h2 id="space-title">空间图</h2>'
            '<div class="space-controls" aria-label="视角">'
            '<button type="button" data-camera="oblique" aria-pressed="true">空间关系</button>'
            '<button type="button" data-camera="side" aria-pressed="false">看向侧面 W</button></div>'
            + "".join(panels) + '<p class="space-status" aria-live="polite">点选字母，对照纸面图中已画出的投影。</p></section>')
