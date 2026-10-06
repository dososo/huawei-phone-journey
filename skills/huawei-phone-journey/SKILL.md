---
name: huawei-phone-journey
description: 制作和修改华为手机设计史的九章网页游历动画，使用真实图片画板、共享人体姿态与空间材质过界，支持资料检查、素材导入、配乐重演奏和可选视频导出。
---

# 华为手机九章游历

把技能目录作为工作目录。运行代码、数据与工具全部在此目录中，不依赖仓库外的文件。

## 先明确交付

区分缺图技术预览、用户素材版网页、视频导出和完整有声作品。当前目录含 1106 条资料记录，`data/catalog.json` 的 `journeyIds` 选择 451 项进入九章时间轴；不要将记录数称为独立型号全部收齐。

真实手机图片和商业采样没有随技能提供。缺图必须明确显示，不生成假手机补空；缺音源时如实报告，不冒称已复现原片。

## 运行入口

```bash
python3 scripts/journey.py check
python3 scripts/journey.py serve
```

需要导入或获取图片时，先查看 `fetch`、`import-images` 的帮助。获取操作应遵守来源的访问规则；遇到限制停止该来源，不猜路径或绕过登录、验证码与频率限制。

```bash
python3 scripts/journey.py fetch --help
python3 scripts/journey.py import-images --help
python3 scripts/journey.py build --help
```

普通网页无需 npm，`serve` 默认只绑定本机的 8780 端口。下载和导入图片另需 Pillow；`fetch` 使用 `--ids` 或 `--all` 选择记录，并以 `--yes` 显式开始获取。`import-images --from` 读取用户目录，`--map` 可提供 ID 到输入目录内相对路径的 JSON。

只有需要 HyperFrames 检查或导出时，先执行 `npm install`，再执行 `python3 scripts/journey.py build` 生成 `output/project`，然后执行 `npm run check`、`npm run render`。默认影片输出到 `output/journey.mp4`。短段可用 `build --seconds 12`；带音轨用 `--audio`，目前只支持从零开始的有声构建。

## 修改位置

- `data/catalog.json`：名称、来源、图片线索、显示上限、风格与日期状态。
- `data/timeline.json`：九章、节点、序幕、片尾、到达和过界时点。
- `data/score.json`：乐谱事件、重点提示与轻空气编排。
- `src/hero.js`：独立人物姿态与媒介表面。
- `src/journey.js`：真实图画板、世界运动与空间裁切。
- `src/compact.js`、`src/app.js`、`index.html`：九章节奏与播放页面。
- `src/player.js`：普通网页播放时钟；构建导出工程时排除，由 GSAP 接管确定性的逐帧定位与渲染。

只修改请求涉及的内容。保留精确变体、来源语义、推断与冲突标记；图片公开可访问不等于已获授权。用户必须有权使用导入的图片和音源，商业采样不得随项目再次分发。

## 画面与声音约束

不同材质绘制使用同一时间、姿态与尺度；世界画板负责裁切，保持过界时不同身体部位连续换肤。不要靠瞬时换色替代空间变换。

图片保持完整原幅比例与显示上限，不去水印，不把局部图或身份不明的变体当成完整本型号。媒介映射是创意表达，不是手机材料或屏幕技术事实。

音频脚本另需 NumPy、SciPy 与 SoundFile。用 `--bank` 显式指定用户有权使用的样本库 JSON，并用 `--out` 指定输出。完整重演需要钢琴、电钢琴、暖垫、晶体、弦乐五类各至少一份样本和三个鼓片段；样本文件必须位于配置文件目录内。

```bash
python3 -m pip install numpy scipy soundfile
python3 scripts/audio.py --help
```

配置字段见 [examples/audio-bank.json](examples/audio-bank.json)。模板不含音频，根音与力度必须对应用户自己的样本。

使用时间轴中的精确到达与过界锚点。章节导航的整秒显示不可用于精确音效定位。音频脚本输出 48 kHz 双声道 24 位 WAV，尚未做最终响度与真峰母带；不要继承其他作品的母带指标作为当前输出结果。

## 完成前检查

执行数据检查并实际预览画面。检查型号与年月可读、手机身份与完整性、人体轮廓、材质过界和首尾构图。需要视频时，对真正导出的文件做媒体探测、完整解码与抽帧；需要声音时，实际监听章节变化、音画时点和结尾。

交付说明列出修改、运行命令与实际结果，并区分已验证、缺失素材和待人工审美判断。不要将 JSON 检查、导出退出码或旧作品截图写成当前画面与听感验收。
