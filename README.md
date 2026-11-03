# 山河织路

一部可以走进去的实时三维长卷。以一条红线连接田埂、街市、城市、山河与星河，把五段中国时间中的日常缝合在一起。第一幕现使用本项目建模与 CC0 材质、植被；来源和修改记录见 [第一幕制作记录](docs/RURAL_REALISM_WORKLOG.md)。

> 第一幕写实改造仍在制作中，当前画面和资产尚未达到高精度写实验收标准；已完成与待处理内容见制作记录。其余四幕仍沿用原有视觉风格。

## 本地运行

需要 Node.js 20+、Python 3 和支持 WebGL 2 的现代浏览器。

```sh
npm install
npm run build
npm run serve
```

打开 http://127.0.0.1:8137/。`npm run build` 同时生成在线版和单文件离线版；日常只调试网页可运行 `npm run build:web`，然后刷新浏览器。

无需服务器的交付物是 `dist/山河织路-离线单文件.html`，可直接双击打开。它内嵌模型、贴图、脚本和样式；声音由 WebAudio 实时合成，不依赖在线服务。

## 体验

- 封面下方可直接进入五幕中的任意一幕；点击“走进长卷”从头出发。
- 滚轮、上滑或方向键向前，下滑或向上方向键回望。左右拖动调整视线。
- 第一幕可点击“自由漫步”：W/A/S/D 行走，按住 C 低身，拖动画面转身，Esc 或“返回路线”回到长卷。触屏使用方向按钮、蹲下按钮和拖动视角。
- “自动漫游”约三分钟走完整条路，手动操作、查看卡片和切到后台会暂停。
- 点击场景中的拾光点或“拾起这一幕”收集记忆。收集进度和声音偏好保存在本机；浏览器禁用存储时仍可体验。
- “展卷”可总览五座时代之岛，点击岛屿标签进入该时代。
- 终点可选择或填写一句愿望，点亮火箭，再回看整轴长卷。
- M 切换声音，Esc 关闭卡片或返回。对话框支持键盘焦点循环。系统开启“减少动态”时停用视差、漂移及发射镜头。

声音默认关闭，由观众手动开启。移动端降低像素比、阴影分辨率并关闭泛光。

## 源码与交付

| 路径 | 内容 |
| --- | --- |
| `src/index.html`、`src/style.css` | 纸本展览界面、响应式布局与可访问性结构 |
| `src/bootstrap.js` | 启动与 WebGL / 必需资源失败恢复 |
| `src/main.js` | 五幕场景、相机曲线、漫游状态与交互 |
| `src/paper.js`、`src/water.js` | 纸纹、墨线、泛光与程序水面 |
| `src/audio.js` | 程序音乐、时代环境音、发射音效 |
| `assets/zones/`、`assets/vehicles/` | 原创 glTF 模型与 Blender 源文件 |
| `tools/build_*.py`、`tools/blib.py` | 原创建模脚本与构件库 |
| `tools/build_rural_realism.py`、`tools/build_rickshaw_realism.py` | 第一幕重建入口；先保存可编辑 Blender 场景，再按材质合批导出 |
| `assets/materials/polyhaven/`、`assets/vegetation/` | CC0 材质、植物、树木的源文件、许可与实时资产 |
| `tools/build.mjs` | 在线、离线统一构建入口 |
| `tools/verify.mjs` | 真实 Chromium 交互与交付回归检查 |
| `qa/optimized/` | 回归检查生成的桌面、手机截图 |
| `docs/00-concept.md` | 作品概念与原始设计方案 |
| `production/`、`docs/boards/` | 已有演示影片与设计展板 |

构建只覆盖网页自身的输出，不清空 `dist`，以保留目录中已有的视频交付物。影片、PDF 和展板是独立制作的静态交付物，不会随网页构建自动重新生成。

## 验证

```sh
npm run build
npm test
```

验证使用 Playwright 自带 Chromium；若本机没有浏览器，可运行 `npx playwright install chromium`，或通过 `CHROME` 环境变量指定 Chromium 可执行文件。测试自行启动随机端口的静态服务器，结束后关闭浏览器和服务器。

检查涵盖桌面、竖屏、横屏、小屏布局，章节跳转、自动漫游、拾光保存、声音、键盘与弹层、愿望与发射、重播资源释放、子目录部署、离线打开，以及模型缺失和 WebGL 不可用的恢复界面。

## 本轮优化

封面重构为双栏展览版式：宋体标题、朱红印记、独立实时场景画框与五幕目录。漫游工具栏、进度、拾光反馈和尾声使用统一视觉语言；重新调整纸纹、景深边缘阈值、列车自发光及昼夜界面配色。补全自动漫游、本机记忆、声音偏好、返回封面与愿望短句。

工程层修复缺失的构建入口、离线版相对资源引用和子目录部署，补充启动异常处理、后台暂停、对话框焦点管理及发射效果释放。除第一幕的在制改造外，三维几何沿用已有资产。

### 重建第一幕资产

已交付的贴图和植物源文件在项目相对目录中；使用 Blender 4.2、Python 3（含 Pillow）和 Node.js：

```powershell
python tools/prepare_rural_materials.py
& 'D:/Blender/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python tools/build_rickshaw_realism.py
& 'D:/Blender/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python tools/build_rural_realism.py
npm run build
```

第一幕 Blender 源文件将贴图打包到 `.blend` 中；运行资产使用导出的 `.glb`。植物原始 glTF 与纹理可由 `tools/fetch_rural_plants.ps1` 重新打包；树木的原始模型及许可保留在 `assets/vegetation/source/ai_tree/`，其运行版本通过下列命令从原模型简化：

```powershell
npx gltf-transform simplify assets/vegetation/source/ai_tree/tree_12_oak_green.glb assets/vegetation/rural_broadleaf.glb --ratio 0.3 --error 0.02
```

如已在 Blender 中手工修改并保存源件，可从该源件重新合批并导出，不必重新生成场景；导出器不会把合批结果写回源 `.blend`：

```powershell
& 'D:/Blender/blender-4.2.9-windows-x64/blender.exe' -b assets/zones/rural.blend --python tools/export_rural_assets.py
& 'D:/Blender/blender-4.2.9-windows-x64/blender.exe' -b assets/vehicles/rickshaw.blend --python tools/export_rural_assets.py
npm run build
```
