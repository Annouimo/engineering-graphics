"""Compile the lesson JSON files into standalone HTML using the shared template."""
import argparse
from html import escape
import json
import math
from pathlib import Path
import re
from string import Template
import sys

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
LINE_ROLES = {"outline": "", "construction": "aux", "hidden": "hidden-edge", "center": "center"}
LABEL_ROLES = {"normal": "", "view": "plane", "dimension": "dim", "result": "found"}


def fields(obj, required, optional, where):
    if not isinstance(obj, dict):
        raise ValueError(f"{where}：需要对象")
    missing = set(required) - obj.keys()
    unknown = obj.keys() - set(required) - set(optional)
    if missing or unknown:
        raise ValueError(f"{where}：缺少 {sorted(missing)}，未知字段 {sorted(unknown)}")


def words(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}：需要非空文字")
    return value


def number(value, where):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{where}：需要有限数字")
    return f"{value:.4f}".rstrip("0").rstrip(".")


def pair(value, where):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{where}：需要 [x, y]")
    return [number(n, where) for n in value]


def role(item, roles, default, where):
    value = item.get("role", default)
    if not isinstance(value, str) or value not in roles:
        raise ValueError(f"{where}：role 应为 {', '.join(roles)}")
    return roles[value]


def draw(item, where):
    kind = item.get("type") if isinstance(item, dict) else None
    if kind == "line":
        fields(item, ("type", "from", "to"), ("role",), where)
        x1, y1 = pair(item["from"], where)
        x2, y2 = pair(item["to"], where)
        cls = role(item, LINE_ROLES, "outline", where)
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'
    if kind == "polyline":
        fields(item, ("type", "points"), ("role",), where)
        points = item["points"]
        if not isinstance(points, list) or len(points) < 2:
            raise ValueError(f"{where}：折线至少需要两个点")
        return "".join(draw({"type": "line", "from": a, "to": b, "role": item.get("role", "outline")}, where)
                       for a, b in zip(points, points[1:]))
    if kind == "arc":
        fields(item, ("type", "from", "to", "radius", "clockwise"), ("large", "role"), where)
        x1, y1 = pair(item["from"], where)
        x2, y2 = pair(item["to"], where)
        r = number(item["radius"], where)
        large, clockwise = item.get("large", False), item["clockwise"]
        if float(r) <= 0 or type(large) is not bool or type(clockwise) is not bool:
            raise ValueError(f"{where}：需要正半径及布尔方向")
        chord = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
        if chord <= 0 or chord > 2 * float(r) + 0.0002:
            raise ValueError(f"{where}：弧的端点与半径不相容")
        cls = role(item, LINE_ROLES, "outline", where)
        return f'<path class="{cls}" d="M{x1},{y1} A{r},{r} 0 {int(large)},{int(clockwise)} {x2},{y2}"/>'
    if kind == "circle":
        fields(item, ("type", "at", "radius"), ("role",), where)
        x, y = pair(item["at"], where)
        r = number(item["radius"], where)
        if float(r) <= 0:
            raise ValueError(f"{where}：需要正半径")
        cls = role(item, LINE_ROLES, "outline", where)
        return f'<circle cx="{x}" cy="{y}" r="{r}" class="ring {cls}"/>'
    if kind == "dot":
        fields(item, ("type", "at"), (), where)
        x, y = pair(item["at"], where)
        return f'<circle cx="{x}" cy="{y}" r="2.7"/>'
    if kind == "label":
        fields(item, ("type", "at", "text"), ("role", "subscript"), where)
        x, y = pair(item["at"], where)
        cls = role(item, LABEL_ROLES, "normal", where)
        content = escape(words(item["text"], where))
        if "subscript" in item:
            content += f'<tspan baseline-shift="sub" font-size="13">{escape(words(item["subscript"], where))}</tspan>'
        return f'<text x="{x}" y="{y}" class="{cls}">{content}</text>'
    raise ValueError(f"{where}：未知图元类型 {kind!r}")


def compile_lesson(config, template):
    fields(config, ("source", "title", "problem", "caption", "size", "layers", "given", "steps", "answer"),
           ("intro", "details"), "题目")
    layers = config["layers"]
    if not isinstance(layers, dict) or not layers:
        raise ValueError("layers 需要至少一个命名图层")
    used = set()

    def refs(value, where):
        if not isinstance(value, list) or any(not isinstance(x, str) or x not in layers for x in value):
            raise ValueError(f"{where}：需要已定义的图层名称列表")
        if len(set(value)) != len(value):
            raise ValueError(f"{where}：图层名称重复")
        used.update(value)
        return value

    given = refs(config["given"], "given")
    steps = config["steps"]
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps 需要至少一步")
    for i, step in enumerate(steps, 1):
        where = f"步骤 {i}"
        fields(step, ("title", "action"), ("reason", "add", "show"), where)
        add = refs(step.get("add", []), f"{where}.add")
        show = refs(step.get("show", []), f"{where}.show")
        if set(add) & (set(show) | set(given)):
            raise ValueError(f"{where}：add 与 show 或 given 重叠")

    intro = config.get("intro", {"title": "读题", "action": config["problem"]})
    answer = config["answer"]
    fields(intro, ("title", "action"), ("reason",), "intro")
    fields(answer, ("action", "show"), ("title", "reason"), "answer")
    answer = {"title": "完成图", **answer}
    refs(answer["show"], "answer.show")
    for section in [intro, *steps, answer]:
        for key in ("title", "action", "reason"):
            if key in section:
                words(section[key], key)

    if unused := layers.keys() - used:
        raise ValueError(f"未使用的图层：{', '.join(sorted(unused))}")

    drawing = []
    for layer, elements in layers.items():
        if not NAME.fullmatch(layer) or not isinstance(elements, list) or not elements:
            raise ValueError(f"{layer}：需要短横线命名、非空的图元列表")
        visibility = "" if layer in given else ' class="is-hidden"'
        markup = "".join(draw(item, f"{layer}[{i}]") for i, item in enumerate(elements))
        drawing.append(f'<g data-layer="{layer}"{visibility}>{markup}</g>')

    width, height = pair(config["size"], "size")
    if min(float(width), float(height)) <= 0:
        raise ValueError("size 的宽高必须为正")
    details = ""
    if "details" in config:
        fields(config["details"], ("title", "text"), (), "details")
        title, body = (escape(words(config["details"][key], f"details.{key}")) for key in ("title", "text"))
        details = f"<details><summary>{title}</summary><p>{body}</p></details>"
    lesson = json.dumps({"given": given, "intro": intro, "steps": steps, "answer": answer}, ensure_ascii=False)
    return template.substitute(
        **{key: escape(words(config[key], key)) for key in ("title", "source", "problem", "caption")},
        width=width, height=height, drawing="".join(drawing), details=details,
        intro_title=escape(intro["title"]), intro=escape(intro["action"]), intro_reason=escape(intro.get("reason", "")),
        lesson=lesson.replace("<", r"\u003c"),
    )


def read_config(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"重复的字段：{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="题目文件名（省略 .json）；留空则编译全部")
    parser.add_argument("--check", action="store_true", help="检查已提交的 HTML 是否与配置匹配")
    args = parser.parse_args()
    if any(not NAME.fullmatch(name) for name in args.names):
        parser.error("题目文件名应由小写字母、数字和短横线组成")
    inputs = [ROOT / "lessons" / f"{name}.json" for name in args.names]
    inputs = inputs or sorted((ROOT / "lessons").glob("*.json"))
    template = Template((ROOT / "tools" / "lesson.html").read_text(encoding="utf-8"))
    outputs = {}
    for path in inputs:
        try:
            outputs[ROOT / "examples" / f"{path.stem}.html"] = compile_lesson(read_config(path), template)
        except (ValueError, OSError) as error:
            parser.exit(1, f"{path.name}：{error}\n")
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"{path.name} 需要重新编译\n")
        else:
            path.write_text(content, encoding="utf-8")
    print(f"{'核对' if args.check else '编译'} {len(outputs)} 道讲解")


if __name__ == "__main__":
    main()
