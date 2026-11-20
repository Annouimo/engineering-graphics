# 用配置生成作图讲解

复制 [配置模板](lesson.example.json) 到 `lessons/<题目名>.json`。题目名使用小写字母、数字和短横线，与生成的 HTML 同名。

```sh
python3 tools/build_lessons.py <题目名>
python3 tools/build_lessons.py --check
```

第一条命令生成 `examples/<题目名>.html`，省略题目名则重新生成全部。第二条检查提交的 HTML 能否从同一份配置重新生成。两条命令都只使用 Python 3.8 及以上版本的标准库。HTML 可单文件离线打开，GitHub Pages 直接发布提交的产物。新增页面时，在站点目录和根 README 加上入口。

## 配置结构

| 字段 | 用途 |
| --- | --- |
| `source`、`title`、`problem`、`caption` | 题号或出处、标题、题干、图注 |
| `size` | SVG 画布的 `[宽, 高]`。原点在左上，向右和向下为正 |
| `layers` | 以名称组织几何图元。每层放一组应一起出现或高亮的元素 |
| `given` | 从题图到完成图始终显示的图层 |
| `steps` | 每步写 `title`、`action`，可加一句 `reason`。用 `add` 和 `show` 引用图层 |
| `answer` | 用 `action` 写结论，用 `show` 指定完成图的图层。可加 `reason` |
| `intro`、`details` | 可选的读题提示和折叠补充说明。模板可省略这两项 |

`add` 里的图层从当前步出现，后续步骤降为浅色。用 `show` 可以临时显示量距标记，也可以重新高亮已知图或之前出现的图层。完成图显示 `given` 和 `answer.show`。图层按配置中的声明顺序叠放。

## 图元

| `type` | 几何字段 |
| --- | --- |
| `line` | `from`、`to` |
| `polyline` | `points`，依次连接各点 |
| `arc` | `from`、`to`、`radius`、`clockwise`。超过半圆时设 `large: true` |
| `circle` | `at`、`radius` |
| `dot` | `at` |
| `label` | `at`、`text`，可加 `subscript` |

每个点用 `[x, y]`。线类图元的 `role` 可选 `outline`（轮廓）、`construction`（作图线）、`hidden`（不可见轮廓）、`center`（中心线）。标签的 `role` 可选 `normal`、`view`（视图名）、`dimension`（尺寸）、`result`（结果点）。颜色、字号、文字描边和步骤控件都由共享模板管理。

先用计算或作图确立几何关系，再把纸面坐标写入配置。坐标如何求可由各题自行决定。编译器负责检查字段、图层引用和弧的基本约束，并输出页面。如果遇到需要新图元的题，在共享编译器中加入相应图元。

## 空间示意

[第 2 题（3）的配置](../lessons/line-axis-distance.json)含可选的 `space`。空间点以 `[x, y, z]` 定义，`views` 为三面投影指定共同的 `scale` 和 `V`、`H`、`W` 三个图面原点。图面坐标依次采用 `[-x, -z]`、`[-x, y]`、`[y, -z]`，乘以比例后加到原点。

纸面图元可以用 `{"point":"M","view":"W"}` 代替二维坐标。标签可用 `offset` 设图面偏移。水平图的点引用加 `"on":"miter"`，可定位从该点向右引深度线与 45° 转向线的交点。普通二维坐标仍可用于轴线、图注和辅助构造。

`segments` 用 `from` 和 `to` 引用空间点，可用 `role` 标为 `axis` 或 `result`。在 `markers` 中用 `point` 标出可对照的点，在 `right_angles` 中用 `vertex` 和两个 `arms` 端点标示直角。三类对象都可用 `step` 指定首次出现的步骤，省略则随题图显示。空间图和点选联动由模板生成。

空间图在题目下方默认显示。标准投影面由 `space.views` 中配置的 H、V、W 决定。辅助面和换面产生的新平面可以通过 `auxiliary_planes` 声明名称、顶点及出现步骤，顶点引用 `space.points`。二维换面作图仍用原有图层编排。

`projections` 按步骤指定标准投影面（`view`）、投影点（`points`）及可选的投影线段（`segments`）。用 `step` 指定开始步骤，需要在某一步后收起时填写 `until`。空间坐标同时用于生成面上的投影与投射线。

默认从第一分角上方斜看。可以用鼠标或触摸拖动，切换作图步骤会保留视角。「恢复默认视角」将空间图转回开场方向。
