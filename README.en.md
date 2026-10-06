[中文](README.md) · **English**

# Huawei Phone Journey in Nine Chapters

One flying character travels through panels of phone images, changing between glass, metal, pearl and textured surfaces as the design styles change.

[![22 Years of Huawei Phone Design: click to watch the nine-chapter film](site/assets/cover-16x9.png)](https://dososo.github.io/huawei-phone-journey/watch.html)

[Watch the Film](https://dososo.github.io/huawei-phone-journey/watch.html) · [Covers and Platform Copy](https://dososo.github.io/huawei-phone-journey/promotion.html) · [1106-Record Catalog](https://dososo.github.io/huawei-phone-journey/catalog.html) · [Creation Skill Source (Chinese)](skills/huawei-phone-journey/SKILL.md)

This project provides a local web animation and a creation skill. The current catalog contains **1106 records**. The nine-chapter timeline selects **451 phone-image nodes** and runs for **12 minutes 52.7 seconds**. Records may include variants, aliases, inferred dates and items awaiting verification. These counts do not mean that every distinct model has been collected, or that every image is high resolution or licensed for redistribution.

The film, final audio preview and covers in three aspect ratios are available through the project website and Release. The repository also provides source code, source references, a timeline and score events. The complete original phone-image library and commercial sample library are not distributed with the source. Without imported images, the local source preview clearly displays missing-image notices and can still be used to inspect the character, layout and timeline.

## Watch and Publishing Materials

- [Project Home](https://dososo.github.io/huawei-phone-journey/): an introduction and links to each part of the project.
- [Nine-Chapter Film](https://dososo.github.io/huawei-phone-journey/watch.html): 451 images in nine chapters, running for 12:52.7; not all other catalog records appear in the film.
- [Covers and Copy](https://dososo.github.io/huawei-phone-journey/promotion.html): 3:4, 4:3 and 16:9 covers with finished copy for six platforms. The [copy document](docs/发布文案.md) contains Chinese, English and bilingual versions as appropriate for each platform.
- [Catalog](https://dososo.github.io/huawei-phone-journey/catalog.html): 1106 records with sources, inferred dates and verification markers retained.
- [Download the Full Film](https://github.com/dososo/huawei-phone-journey/releases/download/v1.0.0/huawei-phone-journey-full.mp4) · [Final Audio Preview](https://github.com/dososo/huawei-phone-journey/releases/download/v1.0.0/huawei-phone-journey-audio-preview.mp3).

Watching and listening do not require a development environment. Making the finished work public does not grant a blanket reuse license for its phone images, samples or trademarks. See [Asset Licensing (Chinese)](ASSET-LICENSE.md).

## Quick Start

You need Python 3.9 or later and a modern desktop browser. Enter the skill directory, check the data and start the local page:

```bash
git clone https://github.com/dososo/huawei-phone-journey.git
cd huawei-phone-journey
cd skills/huawei-phone-journey
python3 scripts/journey.py check
python3 scripts/journey.py serve
```

Open the local URL printed in the terminal. The regular web preview uses `src/player.js` as its playback clock and does not require npm dependencies. Building an export project excludes that clock; GSAP drives deterministic rendering of each frame instead.

For AI tools that support local skills, you can also copy the complete `skills/huawei-phone-journey` directory into the tool's skill directory, then ask: “Use huawei-phone-journey to check the catalog and open the journey preview.” The skill does not depend on documents at the repository root to run.

Tools that support the Skills CLI can use: `npx skills add dososo/huawei-phone-journey --skill huawei-phone-journey`.

Restore the phone panels using images you have the right to use. Downloading and importing images additionally requires Pillow. These operations must be invoked explicitly; inspect their options first:

```bash
python3 -m pip install pillow
python3 scripts/journey.py fetch --help
python3 scripts/journey.py import-images --help
```

A successful download does not grant copyright permission. Keep the missing-image state when a source is inaccessible or the model identity is unclear. See [Usage and Reproduction (Chinese)](docs/使用与复现.md) and [Asset Licensing (Chinese)](ASSET-LICENSE.md).

To render the music from its score, install the audio dependencies and inspect the sample-bank options:

```bash
python3 -m pip install numpy scipy soundfile
python3 scripts/audio.py --help
```

For checking or exporting through HyperFrames, install the optional dependencies in the skill directory:

```bash
npm install
python3 scripts/journey.py build
npm run check
npm run render
```

The project uses HyperFrames **0.8.135** and GSAP **3.14.2**. Preview the selected assets before exporting. Passing a check command does not replace visual inspection or listening.

## Capabilities

| Capability | Actual Scope |
| --- | --- |
| Continuous journey | Nine chapters and 451 nodes, ordered by year and month, with inference and conflict markers retained. |
| Character material changes | A shared human pose, with different surface treatments rendered within each panel's spatial boundaries. |
| Real-image panels | User-imported images displayed at their full original aspect ratio and within display limits; the resulting composition still needs visual inspection. |
| Catalog reference | 1106 records and source leads; a separate list determines the nodes included in the journey. |
| Music rendering | Audio generated from 2446 score events and the user's own sample-bank configuration. |
| Local production | Web preview, data checks, image import, static builds and optional video export. |

The character's materials are artistic interpretations, not measurements of a phone's internal materials, display technology or performance. Historical sources distinguish announcement, market availability and sales dates. Inferred values are not exact official launch dates.

## Directory

```text
.
├── README.md
├── README.en.md
├── LICENSE
├── NOTICE
├── ASSET-LICENSE.md
├── docs/
│   ├── 设计与原理.md
│   ├── 使用与复现.md
│   └── 发布文案.md
├── site/
│   ├── index.html               Project home
│   ├── watch.html               Film and audio preview
│   ├── promotion.html           Covers and copy
│   ├── catalog.html             Catalog
│   └── assets/
│       ├── cover-3x4.png
│       ├── cover-4x3.png
│       └── cover-16x9.png
├── scripts/
│   └── release_check.py          Public-file and sensitive-information checks
├── tests/
│   ├── test_journey.py
│   ├── test_audio.py
│   ├── test_hero.py
│   └── test_release_check.py
├── .github/workflows/           Continuous integration
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
    │   └── player.js             Web playback clock, excluded from exports
    ├── data/
    │   ├── catalog.json
    │   ├── timeline.json
    │   └── score.json
    ├── scripts/
    │   ├── journey.py
    │   └── audio.py
    └── examples/
        ├── catalog.json         Small catalog example
        └── audio-bank.json      User sample-bank template, without audio
```

All runtime code and data needed by the skill live inside the skill directory, which can be copied in full. `site` contains the public project pages and covers; the film and audio preview are Release attachments. Images, sample libraries, audio and build directories generated during your own use are local files. Do not commit private paths, credentials or assets without permission to the source repository.

## Frequently Asked Questions

**Why do the phone panels in my local preview show missing-image notices?** The public film can be watched directly, but the complete original phone-image library needed to rebuild the panels is not distributed with the skill. The local page displays a phone only after a usable source image has been imported. Missing-image notices describe the actual state; they cannot serve as a delivery of the phone's real appearance.

**Can this reproduce the published film?** It can reconstruct the structure and animation logic, but does not promise a byte-for-byte reproduction of the original film. Different images, samples, fonts, browsers and export environments will change the result.

**Was this generated in one click by a video model?** The main visuals are drawn in code, the phone panels use real images, and the music is performed from a score using samples. AI can assist research and implementation, but that does not make the work fully automatic.

**Can I use it commercially or publish it again?** The author's original code and documents are available under the Mulan Permissive Software License, Version 2. Phone images, fonts, audio samples and trademarks remain subject to their own rights and conditions. See [Asset Licensing (Chinese)](ASSET-LICENSE.md).

**Can I expand the catalog or adapt it to another product history?** You can adjust the catalog, journey list, timeline and style mappings. Retain precise identities, sources, date meanings and uncertainty markers, then check both the data and the actual rendering.

## Author

**爆裂队长 NEXT（BLCaptain）**

- GitHub: [dososo](https://github.com/dososo)
- X: [@thinkszyg](https://x.com/thinkszyg)
- Email: [blteam2026@outlook.com](mailto:blteam2026@outlook.com)

Code and documents are licensed under the [Mulan Permissive Software License, Version 2 (Chinese text)](LICENSE). For the scope of third-party content, see [NOTICE](NOTICE) and [Asset Licensing (Chinese)](ASSET-LICENSE.md).
