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
        ("oblique", "空间关系", (.8660254, -.5, 0), (.25, .4330127, .8660254),
         "观察 AB 和 X 轴如何错开。MN 出现后，可以看到两端的直角。"),
        ("side", "看向侧面 W", (0, 1, 0), (0, 0, 1),
         "沿 X 轴看过去，X 轴积聚为 O。MN 平行于 W 面，在这个方向显示实长。"),
    )
    dot = lambda a, b: sum(x*y for x, y in zip(a, b))
    sub = lambda a, b: tuple(x-y for x, y in zip(a, b))
    unit = lambda a: tuple(x / sqrt(dot(a, a)) for x in a)

    bases = [(key, title, unit(right), unit(up), note) for key, title, right, up, note in presets]
    bounds = []
    for _, _, right, up, _ in bases:
        xs = [dot(point, right) for point in points.values()]
        ys = [-dot(point, up) for point in points.values()]
        bounds.append((min(xs), max(xs), min(ys), max(ys)))
    scale = min(390 / max(max(r-l for l,r,_,_ in bounds), 1),
                206 / max(max(b-t for _,_,t,b in bounds), 1))
    panels = []
    for (key, title, right, up, note), (left, right_edge, top, bottom) in zip(bases, bounds):
        def project(point):
            return [270 + scale*(dot(point, right) - (left+right_edge)/2),
                    142 + scale*(-dot(point, up) - (top+bottom)/2)]

        content = []
        if key == "side":
            content.append('<rect x="45" y="20" width="450" height="244" rx="3" class="w-plane"/>')
            content.append('<text x="479" y="250" text-anchor="end" class="plane">W 面</text>')
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
                at = [p[0]-42, p[1]+21] if collapsed else [q[0]+10, q[1]+4]
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
            fields(item, ("point",), ("step",), "space.markers")
            name = item["point"]
            at = project(coordinate(name))
            x,y = (number(n,"空间标记") for n in at)
            label = escape(name)
            content.append(wrap(stage(item),
                f'<g class="space-point" data-point="{reference(name)}" role="button" tabindex="0" aria-label="对照点 {label}" aria-pressed="false">'
                f'<circle class="point-hit" cx="{x}" cy="{y}" r="16"/>'
                f'<circle cx="{x}" cy="{y}" r="4"/>'
                f'<text x="{number(at[0]+9,"点名")}" y="{number(at[1]-9,"点名")}">{label}</text></g>'))
        hidden = ' hidden' if key != "oblique" else ''
        panels.append(f'<div data-space-view="{key}"{hidden}><svg viewBox="0 0 540 284" role="group" aria-label="{title}">'
                      + "".join(content) + f'</svg><p class="space-note">{note}</p></div>')

    return ('<details class="space-panel" id="space-panel"><summary>空间示意</summary>'
            '<div class="space-controls" aria-label="视角">'
            '<button type="button" data-camera="oblique" aria-pressed="true">空间关系</button>'
            '<button type="button" data-camera="side" aria-pressed="false">看向侧面 W</button></div>'
            + "".join(panels) + '<p class="space-status" aria-live="polite">点选字母，对照纸面图中已画出的投影。</p></details>')
