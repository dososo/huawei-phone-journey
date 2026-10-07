[中文](README.md) · **English**

# Huawei + Honor Phone Journey in Nine Chapters

One character travels through 22 years of phone design, 2004–2026. **A nine-chapter retrospective of Huawei and pre-split Honor.**

[![22 Years of Huawei Phone Design: click to watch the nine-chapter film](site/assets/film-preview.jpg)](https://dososo.github.io/huawei-phone-journey/watch.html)

[Watch the Film](https://dososo.github.io/huawei-phone-journey/watch.html) · [1106-Record Catalog](https://dososo.github.io/huawei-phone-journey/catalog.html) · [Creation Skill Source (Chinese)](skills/huawei-phone-journey/SKILL.md)

This project provides a local web animation and a creation skill. The new film keeps **451 Huawei entries** and inserts **105 pre-split Honor entries** by year and release month: **556 display entries**, nine chapters, **11 minutes 24.9 seconds**, 1920×1080, native 60 fps. The public catalog contains **1106 records**. A further 48 records from the Honor research lack a usable image or await identity checks and are not counted in the film. Records may include variants, aliases, inferred dates and items awaiting verification. These counts do not mean that every distinct model has been collected, or that every image is high resolution or licensed for redistribution.

The new full film, nine chapter files and chapter index are available through the project website and v2.0.0 Release. The repository also provides source code, source references, a timeline and score events. The complete original phone-image library and commercial sample library are not distributed with the source. Without imported images, the local source preview clearly displays missing-image notices and can still be used to inspect the character, layout and timeline.

## Watch and Project Resources

- [Project Home](https://dososo.github.io/huawei-phone-journey/): an introduction and links to each part of the project.
- [Nine-Chapter Film](https://dososo.github.io/huawei-phone-journey/watch.html): 556 display entries, nine chapters, 11:24.9, 1080p/60 fps; chapter seeking, clear paused frames and chapter downloads.
- [Catalog](https://dososo.github.io/huawei-phone-journey/catalog.html): 1106 records with sources, inferred dates and verification markers retained.
- [Download the New Film](https://github.com/dososo/huawei-phone-journey/releases/download/v2.0.0/huawei-honor-phone-journey-full.mp4) · [New Release and Nine Chapter Files](https://github.com/dososo/huawei-phone-journey/releases/tag/v2.0.0) · [Original Edition](https://github.com/dososo/huawei-phone-journey/releases/tag/v1.0.0).

Watching and listening do not require a development environment. Making the finished work public does not grant a blanket reuse license for its phone images, samples or trademarks. See [Asset Licensing (Chinese)](ASSET-LICENSE.md).

## Rebuilt Around Your Feedback

Viewers found the original roughly 21-minute white-background cut too long, busy and difficult to read. The character sometimes covered the phones, and pre-split Honor was missing. This edition uses warm graphite light, a fixed center stage with the previous and next designs at the sides, short transitions in one direction, larger model names and release months, longer holds for key images, and material changes outside the phones. The full film was rendered again at native 60 fps, with a newly arranged nine-chapter score.

It is still a long film; scrub through or choose a chapter. The purpose is to take stock of a 22-year product journey, rather than chase views. From feature phones to smartphones and foldables, technical depth and the ambition to lead grow through sustained work across successive generations.

This is a retrospective of the collected entries, not a claim that every distinct global phone model has been verified. Honor covers its pre-split era. Local technical checks and sampled visual inspection do not establish comfort on every phone, social-platform transcoding quality or full listening acceptance.

| Time | Era | Chapter | Display entries |
| --- | --- | --- | --- |
| 00:03 | 2004—2009 | First Light | 56 |
| 01:08 | 2010—2012 | Smart Beginnings | 85 |
| 02:47 | 2013—2015 | Lines and Light | 80 |
| 04:23 | 2016—2018 | Expanding the View | 101 |
| 06:26 | 2019—2020 | Gradient Glass | 106 |
| 08:33 | 2021—2022 | Metal and Twin Circles | 29 |
| 09:10 | 2023 | Mother-of-Pearl and Space | 25 |
| 09:44 | 2024—2025 | Folds and Texture | 50 |
| 10:46 | 2026 | The Present and the Horizon | 24 |

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

The project uses HyperFrames **0.8.139** and GSAP **3.14.2**. Preview the selected assets before exporting. Passing a check command does not replace visual inspection or listening.

## Capabilities

| Capability | Actual Scope |
| --- | --- |
| Continuous journey | Nine chapters, 556 entries, native 60 fps, fixed-focus handoffs and retained year/month uncertainty markers. |
| Character material changes | A shared human pose, with different surface treatments rendered within each panel's spatial boundaries. |
| Real-image panels | User-imported images displayed at their full original aspect ratio and within display limits; the resulting composition still needs visual inspection. |
| Catalog reference | 1106 records and source leads; a separate list determines the nodes included in the journey. |
| Music rendering | Audio generated from 2427 score events and the user's own sample-bank configuration. |
| Local production | Web preview, data checks, image import, static builds and optional video export. |

The character's materials are artistic interpretations, not measurements of a phone's internal materials, display technology or performance. Historical sources distinguish announcement, market availability and sales dates. Inferred values are not exact official launch dates.

## Directory

```text
.
├── README.md
├── README.en.md
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE
├── ASSET-LICENSE.md
├── docs/
│   ├── 设计与原理.md
│   ├── 使用与复现.md
│   └── 新版说明.md
├── site/
│   ├── index.html               Project home
│   ├── watch.html               Full film and chapter seeking
│   ├── edition.json             Edition and public media index
│   ├── catalog.html             Catalog
│   └── assets/
│       └── film-preview.jpg      Actual frame from the public film
├── scripts/
│   ├── build_site.py              Allowlisted project-site build
│   └── release_check.py          Public-file and sensitive-information checks
├── tests/
│   ├── test_journey.py
│   ├── test_audio.py
│   ├── test_hero.py
│   ├── test_site.py
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
    │   ├── focus.js
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

All runtime code and data needed by the skill live inside the skill directory, which can be copied in full. `site` contains the public project pages and an actual film-frame preview; the full film and nine chapter files are Release attachments. Personal publishing covers and platform copy are not distributed with the public project. Images, sample libraries, audio and build directories generated during your own use are local files. Do not commit private paths, credentials or assets without permission to the source repository.

## Frequently Asked Questions

**Why do the phone panels in my local preview show missing-image notices?** The public film can be watched directly, but the complete original phone-image library needed to rebuild the panels is not distributed with the skill. The local page displays a phone only after a usable source image has been imported. Missing-image notices describe the actual state; they cannot serve as a delivery of the phone's real appearance.

**Can this reproduce the published film?** It reconstructs the new fixed-focus layout, chapter timing and material handoffs. The public source uses an independently drawn character whose motion details differ from the film; it does not promise pixel-for-pixel or byte-for-byte reproduction. Different images, samples, fonts, browsers and export environments will change the result.

**Was this generated in one click by a video model?** The main visuals are drawn in code, the phone panels use real images, and the music is performed from a score using samples. AI can assist research and implementation, but that does not make the work fully automatic.

**Can I use it commercially or publish it again?** The author's original code and documents are available under the Mulan Permissive Software License, Version 2. Phone images, fonts, audio samples and trademarks remain subject to their own rights and conditions. See [Asset Licensing (Chinese)](ASSET-LICENSE.md).

**Can I expand the catalog or adapt it to another product history?** You can adjust the catalog, journey list, timeline and style mappings. Retain precise identities, sources, date meanings and uncertainty markers, then check both the data and the actual rendering.

For catalog corrections and code contributions, read the [contribution guide (Chinese)](CONTRIBUTING.md) and include public sources or reproduction steps.

## Author

**爆裂队长 NEXT（BLCaptain）**

- GitHub: [dososo](https://github.com/dososo)
- X: [@thinkszyg](https://x.com/thinkszyg)
- Email: [blteam2026@outlook.com](mailto:blteam2026@outlook.com)

Code and documents are licensed under the [Mulan Permissive Software License, Version 2 (Chinese text)](LICENSE). For the scope of third-party content, see [NOTICE](NOTICE) and [Asset Licensing (Chinese)](ASSET-LICENSE.md).
