"""Render a rotatable teaching diagram from shared spatial coordinates."""
from html import escape
from math import cos, radians, sin, sqrt


def spatial_panel(model, points, steps, draw, fields, number, words):
    def coordinate(point):
        if not isinstance(point, str) or point not in points:
            raise ValueError(f"未知空间点：{point}")
        return points[point]

    def stage(item, key="step", default=0):
        value = item.get(key, default)
        if type(value) is not int or not 0 <= value <= steps:
            raise ValueError(f"空间图的 {key} 必须是有效的作图步骤")
        return value

    def wrap(start, content, end=None, focus=None):
        hidden = ' class="is-hidden"' if start else ""
        until = f' data-space-until="{end}"' if end is not None else ""
        plane = f' data-space-focus="{focus}"' if focus else ""
        return f'<g data-space-step="{start}"{until}{plane}{hidden}>{content}</g>'

    for key in ("segments", "markers", "right_angles", "auxiliary_planes", "projections"):
        if not isinstance(model.get(key, []), list):
            raise ValueError(f"space.{key} 需要列表")

    default_angles = (62, 28)
    azimuth, elevation = map(radians, default_angles)
    right = (-sin(azimuth), cos(azimuth), 0)
    up = (-sin(elevation)*cos(azimuth), -sin(elevation)*sin(azimuth), cos(elevation))

    def dot(a, b):
        return sum(x*y for x, y in zip(a, b))

    def sub(a, b):
        return tuple(x-y for x, y in zip(a, b))

    x0, y0, z0 = (min(0, *axis) for axis in zip(*points.values()))
    x1, y1, z1 = (max(0, *axis) for axis in zip(*points.values()))
    y1 += 24
    z1 += 26
    x1 = max(x1, 20)
    plane_specs = {
        "H": (2, [(x0,y0,0), (x1,y0,0), (x1,y1,0), (x0,y1,0)],
              "水平面 H", (x1*.87,y1*.62,0), (-28,19)),
        "V": (1, [(x0,0,z0), (x1,0,z0), (x1,0,z1), (x0,0,z1)],
              "正投影面 V", (x1,0,z1), (-8,-10)),
        "W": (0, [(0,y0,z0), (0,y1,z0), (0,y1,z1), (0,y0,z1)],
              "侧投影面 W", (0,y1,z1*.62), (15,3)),
    }

    enabled = {key: spec for key, spec in plane_specs.items() if key in model["views"]}
    auxiliary = []
    for item in model.get("auxiliary_planes", []):
        fields(item, ("label", "corners", "step"), (), "space.auxiliary_planes")
        corners = item["corners"]
        if not isinstance(corners, list) or len(corners) < 3:
            raise ValueError("辅助面需要至少三个顶点")
        auxiliary.append((stage(item), [coordinate(point) for point in corners], words(item["label"], "辅助面名称")))

    fit_points = [*points.values(), *(p for _, corners, *_ in enabled.values() for p in corners),
                  *(p for _, corners, _ in auxiliary for p in corners)]
    xs, ys = [dot(p, right) for p in fit_points], [-dot(p, up) for p in fit_points]
    left, right_edge, top, bottom = min(xs), max(xs), min(ys), max(ys)
    scale = min(430 / max(right_edge-left, 1), 214 / max(bottom-top, 1))

    def project(point):
        return [270 + scale*(dot(point, right) - (left+right_edge)/2),
                142 + scale*(-dot(point, up) - (top+bottom)/2)]

    def encoded(vertices):
        return " ".join(",".join(number(v, "空间坐标") for v in p) for p in vertices)

    def bind(markup, vertices, offset=None):
        attrs = f' data-world="{encoded(vertices)}"'
        if offset is not None:
            attrs += f' data-offset="{offset[0]},{offset[1]}"'
        tag_end = markup.index(" ")
        return markup[:tag_end] + attrs + markup[tag_end:]

    def face(corners):
        vertices = " ".join(",".join(number(v, "投影面") for v in project(p)) for p in corners)
        return bind(f'<polygon points="{vertices}"/>', corners)

    def segment(a, b, role="outline"):
        return bind(draw({"type": "line", "from": project(a), "to": project(b), "role": role}, "空间投影"), [a, b])

    def caption(point, title, offset, role="normal"):
        x, y = project(point)
        dx, dy = offset
        return bind(draw({"type": "label", "at": [x+dx, y+dy], "text": title, "role": role}, "空间标注"), [point], offset)

    def circle(point, radius, cls=""):
        x, y = (number(n, "空间标记") for n in project(point))
        return bind(f'<circle class="{cls}" cx="{x}" cy="{y}" r="{radius}"/>', [point])

    content = []
    for view, (_, corners, label, anchor, offset) in enabled.items():
        content.append(f'<g class="space-plane plane-{view.lower()}" data-plane="{view}">'
                       + face(corners) + caption(anchor, label, offset, "view") + '</g>')
    for start, corners, label in auxiliary:
        center = tuple(sum(axis)/len(corners) for axis in zip(*corners))
        content.append(wrap(start, '<g class="space-plane plane-extra">'
                            + face(corners) + caption(center, label, (6,-6), "view") + '</g>'))
    content.append(caption((0,0,0), "O", (7,15), "view"))

    for item in model.get("projections", []):
        fields(item, ("view", "step", "points"), ("until", "segments"), "space.projections")
        view = item["view"]
        if not isinstance(view, str) or view not in enabled:
            raise ValueError("空间投影需要已启用的投影面")
        start = stage(item)
        end = stage(item, "until") if "until" in item else None
        if end is not None and end < start:
            raise ValueError("空间投影的 until 不能早于 step")
        if not isinstance(item["points"], list) or not isinstance(item.get("segments", []), list):
            raise ValueError("空间投影的 points、segments 需要列表")
        axis = enabled[view][0]

        def projected(name):
            return tuple(0 if i == axis else value for i, value in enumerate(coordinate(name)))

        guides = []
        for names in item.get("segments", []):
            if not isinstance(names, list) or len(names) != 2:
                raise ValueError("投影线段需要两个端点")
            guides.append(segment(*(projected(name) for name in names)))
        for name in item["points"]:
            p, q = coordinate(name), projected(name)
            if p == q:
                continue
            guides.append(segment(p, q, "construction"))
            suffix = {"V": "′", "H": "", "W": "″"}[view]
            guides.append(circle(q, 3) + caption(q, name.lower()+suffix, (8,-9)))
        content.append(wrap(start, '<g class="space-projection">' + "".join(guides) + '</g>', end, view))

    for item in model["segments"]:
        fields(item, ("from", "to"), ("label", "role", "step"), "space.segments")
        a, b = coordinate(item["from"]), coordinate(item["to"])
        role = item.get("role", "outline")
        if role not in ("axis", "outline", "result"):
            raise ValueError("空间线段的 role 应为 axis、outline 或 result")
        geometry = segment(a, b)
        if "label" in item:
            geometry += caption(b, words(item["label"], "空间线段标签"), (-27,22))
        content.append(wrap(stage(item), f'<g class="space-{role}">{geometry}</g>'))

    for item in model["right_angles"]:
        fields(item, ("vertex", "arms"), ("step",), "space.right_angles")
        p = coordinate(item["vertex"])
        if not isinstance(item["arms"], list) or len(item["arms"]) != 2:
            raise ValueError("直角标记需要两个臂端点")
        arms = [sub(coordinate(arm), p) for arm in item["arms"]]
        lengths = [sqrt(dot(arm, arm)) for arm in arms]
        if not all(lengths):
            raise ValueError("直角臂不能为零")
        u, v = [tuple(x*12/(scale*length) for x in arm) for arm, length in zip(arms, lengths)]
        corners = [tuple(x+a+b for x,a,b in zip(p, du, dv))
                   for du,dv in ((u,(0,0,0)),(u,v),((0,0,0),v))]
        mark = segment(corners[0], corners[1]) + segment(corners[1], corners[2])
        content.append(wrap(stage(item), f'<g class="space-result">{mark}</g>'))

    for item in model["markers"]:
        fields(item, ("point",), ("step",), "space.markers")
        name = item["point"]
        p = coordinate(name)
        label = escape(name)
        offset = {"A": (-19,-12), "B": (10,17), "M": (-9,-16), "N": (-26,-10)}.get(name, (9,-9))
        content.append(wrap(stage(item),
            f'<g class="space-point" data-point="{label}" role="button" tabindex="0" aria-label="对照点 {label}" aria-pressed="false">'
            + circle(p, 15, "point-hit") + circle(p, 4) + caption(p, name, offset) + '</g>'))

    camera = ",".join(map(str, default_angles))
    return ('<section class="space-panel" id="space-panel" aria-labelledby="space-title"><h2 id="space-title">空间图</h2>'
            '<div class="space-controls"><button id="reset-space" type="button">恢复默认视角</button></div>'
            f'<svg viewBox="0 0 540 284" role="group" aria-label="空间图，拖动可旋转" data-orbit="{camera}" data-fit="{encoded(fit_points)}">'
            + "".join(content) + '</svg><p class="space-note">拖动旋转，点选字母可对照纸面投影。</p>'
            '<p class="space-status" aria-live="polite"></p></section>')
