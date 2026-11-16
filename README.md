# 山河织路

《山河织路》的这一稿题为《回家吃饭》。外婆的灶边字条、妈妈的电影票、宁宁的绿皮车票与高铁票，连起一家三代的归途。最后是一张通向星河的登船牌。故事以第三人称讲述：时代改变了远行与团圆的条件，纸上的牵挂一直留着。

## 打开剧情体验版

- 正式网页入口：[harmonyconnectwindows.com/#HCHHB](https://harmonyconnectwindows.com/#HCHHB)。沿用 HCW 官网的 Cloudflare Pages `web` 项目；后续发布见 [网页部署记录](docs/网页部署记录.md)。
- [剧情与互动稿](docs/回家吃饭-剧情与互动稿.md) 收录开场、五幕票面与票背正文，以及回望地球的统一尾声。
- [离线体验](dist/山河织路-离线单文件.html) 可直接在支持 WebGL 2 的桌面浏览器打开。模型、贴图、声音程序和脚本均已内嵌。

## 已接入正式作品的地球尾声

“点亮归途”现在直接进入约 26 秒的实时三维尾声：火箭先远去消失，镜头缓缓回望，地表显露后平滑加速拉远，最后停在完整地球与“这次，家是地球”。原始 5400 × 2700 地表、8192 × 4096 云图保留分辨率，尾声采用 1.5—2 倍渲染与多重采样抗锯齿；不是内嵌预览录像。轨道相机按距离调整深度精度，消除拉远后云层被地表错误遮挡产生的碎黑点。云带、云影和柔和大气沿用已认可的小样，桌面、竖屏和横屏分别调整取景。

结束后地球继续留在画面中，“再走一程”“展开长卷”和可展开的“沿途票根”承接后续操作。票根中保留原句与留言；返回展卷再回尾声，会恢复地球画面。减少动态或“直接看尾声”直接进入静态地球。

历史 [回望地球小样](dist/回望地球-独立小样.html) 与 [26 秒预览短片](dist/回望地球-小样预览.mp4) 保留作对照，其中旧结语未改。正式版本见上方离线体验。源实现位于 `src/earth/`；纹理来源与许可见 `assets/earth/` 和作品说明。开发时可用 `node tools/build_earth_preview.mjs` 单独重建历史小样。

本轮还将山河大桥的桥牌移至桥跨中心，并用新的五节环线列车替换未来城的静态列车；车厢各自沿弯道转向。隧道没有改动。

## 上一版参赛存档与美术资料
- [四段跨岛短片](qa/crossings/四段跨岛预览.mp4) 和[跨岛实景](qa/crossings/四段跨岛实景.jpg) 取自正式漫游的离岸、越界与着陆位置。
- [102 秒演示片](dist/山河织路-演示片.mp4) 记录上一版“到了，给家里捎个信”的叙事。
- [上一版参赛材料包](dist/山河织路-参赛材料.zip) 包含当时的交互作品、桌面与移动界面 PNG、影片、五张展板、设计说明及流程图。
- [四幕树木同机位对照](qa/scenery/四幕树木前后对照.jpg) 可查看东街、都市、桥岛和星港本轮替换前后的实景。
- [沿途细节改造对照](qa/refinement/漫游细节对照.jpg) 在同一漫游进度比较前后画面。
- [五幕动画实景](qa/animation/五幕实景.jpg) 取自正式漫游入口。
- [美术规范与验收](docs/美术规范与验收.md) 记录逐幕的材质、镜头、修改依据、素材授权与实测范围。[五幕同机位对照](qa/edition/五幕同机位对照.jpg)

## 操作

从封面“展开长卷”进入约 9.6 秒的短开场：一家三代的介绍、五岛灯火，随后镜头接入村庄。可跳过引入；展卷后选择任一岛，镜头直接切入并缓缓靠近。

滚轮、上滑、向下方向键或空格前进，向上方向键回望。岛内同样的滚动量对应相同的前进路程，跨岛逐步加速和减速。也可开启自动漫游。

每幕设置一个票页节点：提前留出减速距离，用约四秒的连续收速抵达；在最后约 1.5 秒，票面与镜头减速同步渐显，票面展开完成时镜头基本停稳。整张票可点击，一次翻面直接读到文案；按 R 也可翻阅。再次向前滚动、向上滑出票面或点“继续游览”都能接着走。出票时尚未结束的那次滚动不会直接带走票页，也不会积存为后续的突然前冲。票背内容超出屏幕时，先在票内滚动阅读；输入框保留正常编辑。

五种物件各自设计：折角手写字条、带撕验副券的电影票、粉红软纸普速客票、蓝色磁介质高铁票、带航次/舱门/座位/条码的星河港登船牌。票面采用剧情中的虚构资料，铁路票按官方票样重绘，登船牌采用独立的航天视觉。票背也延续各自材质与排版。“票夹”可回看已到达的票页，每幕只主动出现一次。绿皮车与双向高铁在前一段跨岛时便启动，入岛后已在行驶，读票期间继续运行；票页和故事短句完全不等待列车通过。

前四张票背可以“留住这句话”。未来城游览后出现登船牌，背面直接填写最多 24 字的旅途留言，或选一句，也可留白。正面和背面都能“点亮归途”，另有“直接看尾声”。留言只是观众的落款，不触发人物回复。草稿保留在本次行程，重新启程会清空。

火箭比镜头升得更快，远去消失后开始回望。旧岛屿在视野之外退出，地表与云带显露，再加速带出地球全貌。“这次，家是地球”在镜头收稳后渐显。结尾不根据留言分支，选留原句与旅途留言保存在“沿途票根”。

首次进入时静音，M 或声音按钮可切换。声音偏好与收集的章节保存在本机。阅读支持键盘焦点循环；系统的减少动态设置保留静态开场、直接翻面和完整尾声。

## 运行、拍摄与导出

使用 Node.js 20+、Python 3、支持 WebGL 2 的 Chromium。安装依赖后运行以下命令。开发服务器地址为 `http://127.0.0.1:8137/`。

```sh
npm install
npm run build
npm test
npm run serve
```

构建同时生成网页与离线单文件，保留目录中的影片。浏览器驱动使用 Playwright，可用 `npx playwright install chromium` 安装，或设置 `CHROME` 指向现有可执行文件。相机脚本与影片脚本默认连接上面的本机服务器，`CAPTURE_URL` 可改地址。

保持服务器运行后，可执行以下拍摄与验收命令。展板、PDF 和参赛打包仍采用上一版参赛编排。剧情体验版的交付文件为离线网页与《回家吃饭》互动稿。同机位对照的上版底图存放在 `qa/refinement/previous`。出图脚本使用 Pillow 及 Windows 宋体、微软雅黑。影片使用随项目保存的合成配乐。

```sh
node tools/verify_arrivals.mjs
node tools/verify_homecoming.mjs
node tools/profile_departures.mjs
node tools/check_crossings.mjs
node tools/check_route.mjs qa/refinement/after
python tools/refinement_proof.py
node tools/capture_edition.mjs qa/edition/final --details
python tools/edition_proofs.py
node tools/render_video.mjs
node tools/render_boards.mjs
node tools/render_pdfs.mjs
python tools/package_submission.py
```

实名提交时，打包脚本另支持 `--author 姓名 --pledge 已签承诺书.pdf`，团队分工可用 `--team 分工说明.pdf` 附入。依据见[数字媒体作品公开提交说明](https://xsszjyxy.ccut.edu.cn/info/1012/1753.htm)。

## 可编辑资产

| 路径 | 用途 |
| --- | --- |
| `assets/zones/`、`assets/vehicles/` | 五座岛与七种载具的 Blender 源件及实时 GLB |
| `assets/sources/painted/`、`assets/painted/` | 十二张原始画稿、三十张实际运行的绘景纹理 |
| `assets/sources/lettering/`、`assets/sources/scene-print/` | 招牌字体原件与许可、影院海报与夜窗画稿 |
| `assets/sources/guishangqingfeng/` | 《轨上清风》的三种列车原模型及校验清单 |
| `src/painted_scenes.js`、`src/illustration.js` | 分层搭景、人物、温室、植物与分阶着色 |
| `assets/raw/` | 十二件主模型未经网页压缩的 GLB |
| `assets/materials/polyhaven/`、`assets/vegetation/` | 第一幕材质、早期地被源件、许可与清单 |
| `tools/model_craft.py`、`tools/rural_craft.py`、`tools/era_fixtures.py`、`tools/rolling_stock.py` | 稻穗和篾编、钢木构件、报亭、列车及发射场细部 |
| `src/main.js`、`src/surface.js`、`src/water.js`、`src/paper.js` | 章节路线、票页与发射、材质细节、雨夜反射、水和纸感后期 |
| `production/`、`docs/boards/` | 配乐、影片母版与提交版、五张 2400 × 1500 展板 |

重建使用 Blender 4.2、Python（含 Pillow）与 Node.js。先运行 `python tools/make_craft_atlas.py` 生成稻穗、树叶和四种场内标牌。下表为 Blender 的 Python 脚本及其参数。

| 源件 | Blender 脚本及参数 |
| --- | --- |
| 田埂晨、人力车 | `tools/build_rural_realism.py`、`tools/build_rickshaw_realism.py` |
| 街市暮、轿车 | `tools/build_town.py`、`tools/build_town.py -- car` |
| 城夜雨 | `tools/build_city.py` |
| 山河速 | `tools/build_rail.py -- rail` |
| 绿皮车、和谐号、复兴号 | `tools/adapt_train_collection.py` |
| 星河远、火箭 | `tools/build_future.py -- --only zone`、`tools/build_future.py -- --only rocket` |
| 星港环线列车 | `tools/build_future_metro.py`；独立五节车厢，由 `src/future_metro.js` 沿环线运行 |

例如，使用本机 Blender 从已保存的原始绘景和列车源件重建网页。

```powershell
& 'D:/Blender/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python tools/adapt_train_collection.py
python tools/prepare_painted_plates.py
node tools/pack_models.mjs green_train hsr harmony
npm run build
```

网页压缩脚本可接收一个或多个资产名，省略参数会处理全套十二个模型。在 Blender 中手工修改第一幕或人力车后，可用 `tools/export_rural_assets.py` 从对应的已保存源件合批导出，再运行压缩和网页构建。

## 验收记录

[桌面、部署与离线回归](qa/tickets/results.json) · [手机与横竖屏检查](qa/tickets/layout-results.json) · [桥牌与环线列车检查](qa/transit/results.json) · [前版交付回归](qa/optimized/results.json) · [招牌视线、排字与转场](qa/refinement/visibility.json) · [单车停位测量](qa/refinement/cinema.json) · [五幕真实机位与错误记录](qa/edition/final/views.json) · [集显帧时间](qa/edition/performance.json) · [源件与图像引用检查](qa/edition/native-audit.json) · [运行资产明细](qa/edition/asset-audit.json)
