# 工程图学研习

《画法几何与机械制图》的交互式习题讲解，以及一套可交给 Agent 复用的制作方法。每个讲解从已知图开始，逐步展示纸面作图过程，最后提供完成图供核对。

## 在线查看

[2024 秋期中作图题汇总](https://annouimo.github.io/engineering-graphics/)

- [第 2 题（1） · 求点 K 的三面投影](https://annouimo.github.io/engineering-graphics/examples/three-view-projection.html)
- [第 2 题（2） · 求 AB 与 X 轴的夹角](https://annouimo.github.io/engineering-graphics/examples/line-axis-angle.html)
- [第 2 题（3） · 求 AB 与 X 轴的最短距离](https://annouimo.github.io/engineering-graphics/examples/line-axis-distance.html)
- [第 3 题 · 在线上找距平面 20 mm 的点](https://annouimo.github.io/engineering-graphics/examples/point-plane-distance.html)
- [第 4 题 · 作等腰三角形并求平面倾角](https://annouimo.github.io/engineering-graphics/examples/isosceles-triangle.html)
- [第 5 题 · 补画主视图](https://annouimo.github.io/engineering-graphics/examples/missing-front-view.html)
- [第 5 题 · 画正等轴测图](https://annouimo.github.io/engineering-graphics/examples/isometric-view.html)

## 制作自己的讲解

把题目和已知图交给 Agent，请它阅读 [AGENTS.md](AGENTS.md)、[知识点索引](topics.md) 、[配置指南](tools/README.md)和[示例配置](lessons/three-view-projection.json)。可以这样说：

> 请按 AGENTS.md 制作这道题的离线作图讲解。先从 topics.md 选择适用的课内知识点，再按配置模板写出图层和步骤，运行 `python3 tools/build_lessons.py` 生成 HTML。图上要看得出从哪里量、沿哪个方向画、取哪个交点。

知识点按作图任务组织，使用时可以对照不同教材。SolidWorks 建模与出图实验见 [ai-solidworks](https://github.com/Annouimo/ai-solidworks)。
