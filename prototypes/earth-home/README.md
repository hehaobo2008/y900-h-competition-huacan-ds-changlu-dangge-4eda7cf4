# 回望地球 · 独立结尾小样（三稿）

打开 [独立离线小样](../../dist/回望地球-独立小样.html)，或看 [26 秒预览短片](../../dist/回望地球-小样预览.mp4)。支持播放、暂停、拖动时间轴、选择阶段和重新播放。这是接入前的历史小样，保留当时的结语。该镜头现已接入[正式作品](../../dist/山河织路-离线单文件.html)，正式结语为“这次，家是地球”，实现见 `src/earth/`。

## 本次调整

云层改为 8192 × 4096 的全球云图，保留云带、涡旋和细碎的薄云。上层云与较暗的底层分开渲染，并在地表投下偏移的云影。云层经度略作构图调整，使回望时露出山河与海岸；这不是实时天气展示。

大气改为沿视线累积、随高度衰减的散射，消除原先蓝色球壳的硬边。升空途中，头顶绘画纹理逐渐退入平静的高空蓝，避免放大的笔触挤满画面。

节奏从 36 秒缩至 26 秒。先缓缓转身，让地表进入视野；随后相机平滑加速，约 7 秒完成主要拉远，最后收稳停留。地球尺寸始终固定，没有通过缩小地球模型制造拉远。

## 镜头关系

火箭比观察者上升得快，依靠距离变化缩成光点。光点消失后，镜头才开始回望。

旧岛屿、建筑、列车、树木和道具在镜头仍朝向天空时全部退出渲染。此时切入独立的地球世界，保留相机朝向、视野和天空。回望看到的第一片地面就属于完整地球。

相机边回望、边沿轻微弧线升高，先看到地表和云带，再看到海岸与大陆，最后看见完整地球。没有白屏、云洞或道具舞台遮挡切换。

| 时间 | 画面 |
| --- | --- |
| 0—3 秒 | 点火，保留地面参照 |
| 3—8 秒 | 火箭加速甩开镜头，缩成远处光点 |
| 8—9.2 秒 | 光点逐渐消失 |
| 9.4 秒 | 视野朝上，在画面之外切换到地球世界 |
| 9.6—14.6 秒 | 连续转身，地表与薄云缓缓进入视野 |
| 14.6—21.8 秒 | 拉远逐步加快，大陆与地球全貌显现，再平滑收稳 |
| 21.9—26 秒 | 停留回望，字幕渐显“这里，是家。” |

此样采用电影式时间与尺度压缩，用于验证视觉衔接，并非真实航天飞行模拟。本文件记录接入前的验证阶段；后续正式版本已接上原有声音控制、返回展卷与重新启程。

## 构建与验证

- `main.js`：播放、发射镜头、视野外的场景切换。
- `choreography.js`：火箭与观察者的速度曲线、回望角度与高度。
- `planet.js`：独立的完整地球、云层、云影、大气和星空。
- 构建：`node tools/build_earth_preview.mjs`。
- 检查：`node tools/verify_earth_preview.mjs`。
- 预览短片：`node tools/render_earth_preview.mjs`。
- 本稿画面与记录在 `qa/earth-preview-v3/`，[检查结果](../../qa/earth-preview-v3/results.json)涵盖离线加载、火箭先消失、镜头连续、拉远加速与收稳、场景切换、固定地球尺寸、旧岛屿退出、手机构图、字幕和重播。
- 正式离线作品为 `dist/山河织路-离线单文件.html`，已在后续接入轮更新。

## 素材来源

地球表面：NASA Earth Observatory 的 **Blue Marble: Next Generation**，2004 年 7 月地形与海底地形版本，5400 × 2700。

- [NASA 官方纹理列表](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-topography-bathymetry/)
- [本样使用的官方 JPEG](https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/bmng-topography-bathymetry/july/world.topo.bathy.200407.3x5400x2700.jpg)
- [NASA Earth Observatory 使用说明](https://science.nasa.gov/earth/faq/)
- [NASA 图像和媒体使用规范](https://www.nasa.gov/nasa-brand-center/images-and-media/)

云层：**Solar System Scope / INOVE — Earth Clouds**，8192 × 4096，按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 使用。

- [作者的纹理页面](https://www.solarsystemscope.com/textures/)
- [原始 8K 云图](https://www.solarsystemscope.com/textures/download/8k_earth_clouds.jpg)
- [本地署名与使用说明](assets/CLOUDS-CREDIT.txt)
- 原图保留原分辨率，未编辑图像。渲染时调整经度、云层高度、光照、透明度与大气颜色，并将同一密度图用于云影。
- 署名和许可链接已放入离线小样右上方“素材来源”，详细说明也内嵌于 HTML。

星点、大气与镜头路径由本项目绘制。未使用 NASA 标识，不表示 NASA 参与或背书。上述素材现也用于正式作品的地球尾声。
