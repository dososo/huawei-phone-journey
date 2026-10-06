# 华为手机九章游历

让同一个飞行角色穿过手机图片画板，随设计风格在玻璃、金属、贝母与纹理之间变换。

这是一套可本地运行的网页动画与创作技能。当前资料目录包含 **1106 条记录**，九章时间轴选择 **451 份机型影像节点**，时长 **12 分 52.7 秒**。记录可能包含版本、别名、日期推断与待核项；这些数字不代表独立型号全部收齐，也不代表所有图片均为高清或已获再分发授权。

仓库提供源码、来源索引、时间轴和乐谱事件。真实手机图片、商业采样和已制作影片不随源码提供。未导入图片时，页面会明确标注缺图；它仍可用于检查角色、布局和时间轴。

## 快速开始

需要 Python 3.9 或更新版本和现代桌面浏览器。先进入技能目录，再检查数据并启动本地页面：

```bash
git clone https://github.com/dososo/huawei-phone-journey.git
cd huawei-phone-journey
cd skills/huawei-phone-journey
python3 scripts/journey.py check
python3 scripts/journey.py serve
```

打开终端显示的本地网址。普通网页由 `src/player.js` 驱动播放时钟，无需安装 npm 依赖。构建导出工程时会排除该时钟，由 GSAP 驱动确定性的逐帧渲染。

在支持本地技能的 AI 工具中，也可将 `skills/huawei-phone-journey` 完整目录复制到其技能目录，再请求“用 huawei-phone-journey 检查资料并打开游历预览”。技能运行不依赖仓库根目录文档。

支持 Skills CLI 的工具可用：`npx skills add dososo/huawei-phone-journey --skill huawei-phone-journey`。

使用你有权使用的图片恢复手机画板。下载和导入另需 Pillow；操作是显式的，可先查看参数：

```bash
python3 -m pip install pillow
python3 scripts/journey.py fetch --help
python3 scripts/journey.py import-images --help
python3 scripts/audio.py --help
```

下载成功不等于取得版权许可；来源不可访问或身份不明时保留缺图状态。详见[使用与复现](docs/使用与复现.md)和[素材许可范围](ASSET-LICENSE.md)。

需要通过 HyperFrames 检查或导出时，可在技能目录安装可选依赖：

```bash
npm install
python3 scripts/journey.py build
npm run check
npm run render
```

项目使用 HyperFrames **0.8.135** 与 GSAP **3.14.2**。导出前先实际预览所选素材；检查命令通过不能替代画面和听感验收。

## 能做什么

| 能力 | 实际范围 |
| --- | --- |
| 连续游历 | 九章、451 节点；按排序年月推进，保留推断与冲突标记。 |
| 角色变材质 | 共享人体姿态，在画板空间边界内分别绘制媒介表面。 |
| 真实图画板 | 使用用户导入的图片，按完整原幅比例和显示上限绘制；实际构图仍需看图确认。 |
| 资料检索 | 1106 条资料记录及来源线索，入片节点由独立名单确定。 |
| 配乐重演奏 | 从 2446 条乐谱事件与用户自己的音源配置生成音频。 |
| 本地制作 | 网页预览、数据检查、图片导入、静态构建与可选视频导出。 |

人物材质是视觉创作，不是对手机内部材料、屏幕技术或性能的测量。历史来源中的宣布、上市和开售日期语义不同，推断值也不是精确官方发布日期。

## 目录

```text
.
├── README.md
├── LICENSE
├── NOTICE
├── ASSET-LICENSE.md
├── docs/
│   ├── 设计与原理.md
│   └── 使用与复现.md
├── scripts/
│   └── release_check.py          公开文件与敏感信息检查
├── tests/
│   ├── test_journey.py
│   ├── test_audio.py
│   └── test_release_check.py
├── .github/workflows/           持续集成
└── skills/huawei-phone-journey/
    ├── SKILL.md
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── hyperframes.json
    ├── src/
    │   ├── hero.js
    │   ├── journey.js
    │   ├── compact.js
    │   ├── app.js
    │   └── player.js             普通网页播放时钟，导出时排除
    ├── data/
    │   ├── catalog.json
    │   ├── timeline.json
    │   └── score.json
    ├── scripts/
    │   ├── journey.py
    │   └── audio.py
    └── examples/
        ├── catalog.json         小型数据示例
        └── audio-bank.json      用户音源配置模板，不含音频
```

技能所需的运行代码和数据都位于技能目录内，可完整复制该目录使用。运行产生的图片、音频、构建目录与影片属于本地输出，不应连同私人路径、密钥或未获许可的素材提交到源码仓库。

## 常见问题

**为什么手机画板是缺图提示？** 真实手机图片没有随仓库分发。导入可用原图后，网页才会显示相应手机；缺图状态用于说明事实，不能作为真实外观交付。

**能否还原已经发布的影片？** 可以重建结构和动画逻辑，但这里不承诺原片字节复现。图片、音源、字体、浏览器和导出环境不同都会改变最终结果。

**这是视频模型一键生成的吗？** 主要画面由代码绘制，手机画板来自真实图片；音乐通过乐谱与采样重演奏。AI 可辅助研究和实现，但不能据此称为完全自动生成。

**能否商用或重新发布？** 作者原创代码与文档按木兰宽松许可证第2版使用。手机图片、字体、音源和商标另受其权利条件约束，见[素材许可范围](ASSET-LICENSE.md)。

**能否扩充资料或改成其他产品史？** 可以调整目录、入片名单、时间轴和风格映射。保留精确身份、来源、日期语义和不确定标记，再检查数据与实际渲染。

## 作者

**爆裂队长 NEXT（BLCaptain）**

- GitHub：[dososo](https://github.com/dososo)
- X：[@thinkszyg](https://x.com/thinkszyg)
- 邮箱：[blteam2026@outlook.com](mailto:blteam2026@outlook.com)

代码与文档采用[木兰宽松许可证第2版](LICENSE)。第三方内容范围见 [NOTICE](NOTICE) 与 [ASSET-LICENSE.md](ASSET-LICENSE.md)。
