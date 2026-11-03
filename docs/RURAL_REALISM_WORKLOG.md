# 第一幕「田埂晨」写实改造记录

更新时间：2026-11-02。**当前仍是未完成的在制版本，不是高精度写实场景验收交付。** 已经重建一部分资产、接入实时工程并进行观察和功能测试；下列未解决问题仍影响样板及全岛质量。

## 原工程与设定

- 工程是 Three.js r169 的五岛连续长卷。原文档明确第一幕为 1980 年代，但没有确定具体省份或季节；本轮暂按江南丘陵稻作区、晚稻收获期、手工农耕与人力货运作假设，不能当作某一村落的考据复原。
- 原 `rural.glb` 是 320×300 米岛体，原车的 Three.js 坐标为 `(2.2, 0.06, 52)`，对应 Blender 平面约 `(2.2, -52)`；运行时还覆盖了拾光点位置。本轮车体移到 `(2.2, 0.11, 52)`，车辕沿路朝村口，拾光仍跟随原位置。
- 工程目录没有 Git 历史。开始前的第一幕 `.blend`、`.glb`、相关源代码及在线构建文件在 `qa/rural_realism/prework_backup/`。原始实时截图在 `qa/rural_realism/baseline/`。

## 参考和授权

- [UNESCO：皖南古村落](https://whc.unesco.org/en/list/1002/)：借鉴村落、道路与水系的空间关联；并未将本场景声称为宏村或徽派建筑的准确复原。
- [Historical Photographs of China：木车轮](https://www.hpcbristol.sjtu.edu.cn/visual/Hv25-086)：观察轮毂、辐条、轮圈构造。该照片是 1933–1946 年北京的记录，仅作为构造参考，不证明 1980 年代江南车辆形制；未将照片用于运行资产。
- [The Handcart Handbook](https://www.chinastrategies.com/wp-content/uploads/2022/04/The_Handcart_Handbook_1985.pdf)：参考双轮手拉车的货运、车辕及受力关系，未复制插图。
- [FAO 中国农业水污染控制指南](https://www.fao.org/docrep/019/i3536e/i3536e.pdf)：参考田埂与排水的作用，未复制图像。
- [Poly Haven 许可](https://polyhaven.com/license)：`dirt`、`fine_grained_wood`、`white_plaster_rough_01`、`rough_linen`、`clay_roof_tiles` 材质及 `grass_bermuda_01`、`weed_plant_02` 植物采用 CC0。各下载文件的 URL 和 MD5 记录在 `assets/materials/polyhaven/manifest.json` 和 `assets/vegetation/source/manifest.json`。织物、墙、瓦颜色经过调整，原始贴图仍保留。
- 村口一株阔叶树来自 [Polyy.AI 3D Deciduous Trees Pack](https://polyyai.itch.io/3d-deciduous-trees-pack)，原作者标注 AI 辅助生成和 CC0。原始 GLB、作者许可和说明保留在 `assets/vegetation/source/ai_tree/`；运行版本由 98,917 三角面简化到 70,462，按 5 米高度安放，关闭金属性并调整粗糙度。该树仅作为通用阔叶树，不宣称物种精确。

## 可见问题、修改和复查

复查图均来自同一真实 WebGL 应用，机位和参数记录在 `qa/rural_realism/capture.mjs`；不是 Blender 离线渲染或概念图。

| 可见问题 | 具体修改 | 复查结果 |
| --- | --- | --- |
| 原车为棚式简化轮廓，原车辕横跨道路，木材和轮轴难以阅读。 | 改为独立双轮货运手拉车：木车辕、纵梁、横梁、车板、贯穿轴、轮毂、木辐条、轮圈铁箍、支腿、货袋、系绳和未点亮马灯。 | [原车](../qa/rural_realism/baseline/03_cart_front.png) / [当前车](../qa/rural_realism/final/03_cart_front.png) / [轮轴细节](../qa/rural_realism/final/07_wheel_detail.png)。轮轴与木材可辨；货袋依然偏光滑，绳结、金属磨损和木构连接仍需精修。 |
| 原路面是平整色带与两条画线。 | 路面改为带浅车辙起伏的网格，加入 2 米尺度泥土 PBR 贴图与半透明压实痕；沿路增加实例化地被。 | [原道路](../qa/rural_realism/baseline/02_road.png) / [当前道路](../qa/rural_realism/final/02_road.png)。土粒近看可见，但道路边缘仍突兀、车辙和踩踏不够自然，田埂过渡仍需制作。 |
| 房屋墙面为整块方盒、窗户在晨光中过亮。 | 建立有厚度的门窗开口和窗后进深；墙面、木门、灰瓦增加贴图，屋顶网格加入瓦波和搭接轮廓；关闭第一幕门窗及灯笼自发光。 | [原院落](../qa/rural_realism/baseline/05_courtyard.png) / [当前院落](../qa/rural_realism/final/05_courtyard.png)。墙材与开口有所改善，但檐口、门轴、台阶和屋顶材质仍不够真实，屋檐下与背面还需逐栋检查。 |
| 样板民居上层窗为空洞，门槛与单级台阶高度不连贯；新增院门柱一度与墙脱开。 | 增加上层窗框窗棂、门板与铰链、三级台阶、院墙石基，并把门柱移到墙端。 | [修改前近景](../qa/rural_realism/iteration_08_plus/09_house_detail.png) / [当前近景](../qa/rural_realism/final/09_house_detail.png)。接触关系更清楚，但构造和磨损仍需继续精修。 |
| 水塘中间被地形穿透，水岸为简单几何。 | 下挖池底、重建岸线及部分芦苇，并减弱第一幕水面镜面强度。 | [原水塘](../qa/rural_realism/baseline/06_water.png) / [当前水塘](../qa/rural_realism/final/06_water.png)。穿透已经消失，但水面仍过于平滑，岸线和水深表现未达目标。 |
| 路旁球形树、草叶过于简化；第一次植物接入有黑色贴图边缘。 | 替换村口一株树，实例化扫描地被；将原资源分离的 Alpha 合并到颜色图。 | [Alpha 修复前](../qa/rural_realism/iteration_03/02_road.png) / [当前](../qa/rural_realism/final/02_road.png)。黑色碎片基本消失，一株树改善；村口大树的候选树冠因与原树干、气根不匹配而回退（见 iteration_11），其他树冠、草地和远山仍有明显低模感。 |
| 原阴影偏移导致接触弱，第一次缩小阴影范围后出现地面条纹。 | 第一幕单独调节阴影范围、法线偏移并给车轮/支腿增加局部接触阴影。 | `qa/rural_realism/shadows/` 保留对比；大面积条纹减轻，但近物接触和软阴影质量仍需改善。 |

最终运行截图还包括 [全岛斜俯](../qa/rural_realism/final/01_overview.png)、[车侧面](../qa/rural_realism/final/04_cart_side.png)、[车后方](../qa/rural_realism/final/08_cart_rear.png)。[17.84 秒实时漫游录屏](../qa/rural_realism/recording/rural_walk.webm)由浏览器实际进入第一幕、步行、转身和打开拾光录制；无后期补画。

## 资产、材质和运行

- `assets/zones/rural.blend`：53,364,732 字节，保存于按材质合批前；3,828 个对象，文件图像已打包。
- `assets/vehicles/rickshaw.blend`：4,994,532 字节，含 125 个独立网格和根节点，文件图像已打包。
- 运行 `rural.glb`：28,996,288 字节，305,244 个存储三角面，17 种材质、15 张内嵌图像；`rickshaw.glb`：4,390,456 字节，12,388 个存储三角面，6 种材质、6 张内嵌图像。上述统计不包括运行时植物实例，详见 `qa/rural_realism/asset_stats.json`。
- 土、木、墙、瓦和布料使用约 1K 的颜色、法线和粗糙度源贴图；招牌沿用原 4096×2048 图集。木纹按构件长轴投影；粗糙度和法线作为 glTF PBR 通道导出。未进行高模烘焙。
- 路旁草和小型地被按变体实例化；树独立加载，随第一幕显隐。第一幕降低纸艺描边和泛光，其他四幕保留原管线；第一幕水塘单独使用较克制的水材质。
- 在线与离线构建均已更新，离线单文件 75,338,499 字节。重建方法、依赖与 AI 树简化命令见项目 README。源脚本先保存未合批的 Blender 文件，再为实时 GLB 按材质合批；手工修改后的源文件也可用 `tools/export_rural_assets.py` 重新导出，第一幕和车分别验证过该流程。

## 实测和验证范围

- Windows 11，Intel Core i9-13900HX，16,886,550,528 字节内存；机器同时有 Intel UHD 和 NVIDIA RTX 5070 Ti Laptop GPU，但本次 Chromium WebGL 实际使用的是 **Intel UHD / ANGLE Direct3D 11**，未测 RTX。
- Headless Chrome 151、WebGL 2、1600×900、DPR 1、桌面默认画质；第一幕固定视图下，6.00 秒采样 184 帧，平均 **30.64 FPS**，帧间隔中位数 31.7 ms、95 百分位 41.4 ms。见 `qa/rural_realism/performance_iteration_10.json`。这不是全程最低帧率，也不是所有设备的性能保证。
- `npm run build` 成功；`npm test` 通过 57 项，覆盖章节、拾光、自动漫游、手机与横屏布局、总览、离线、子目录、加载失败与 WebGL 失败恢复；日志 `qa/rural_realism/full_test_final.log`。
- `qa/rural_realism/walk_check.mjs` 在真实浏览器验证 W 键移动、C 键低身、拖动转身、步行中拾光、退出自由步行及切换第二幕；结果在 `walk_check.json`。手动录屏展示的是实际程序操作。

## 未完成和限制

1. 样板和全岛仍未达到本任务要求的高精度写实标准。大片农田、土路肩、树木、山体、水塘和可到达远处仍保留粗糙或示意几何，空间过渡与近看质量不足。
2. 人力车的货袋仍近似圆垫；布料重力褶皱、绳结、铁件磨损、轮圈与木构的真实加工细节不足。民居门轴、细瓦、檐底、后墙及排水也需逐处补做。
3. 自由步行使用简化地形函数和部分手工碰撞范围；并非完整物理导航。院墙、田埂、其他道具和山体碰撞尚不完整，所有可达区域尚未逐一验证。
4. 晚稻成熟度、晒谷、绿田和植物季相尚未全岛统一。第一幕与原纸艺风格的第二幕之间仍有视觉差异。
5. 集显测得约 30 FPS，低于原项目提出的桌面 60 FPS 目标；还需要分块剔除、远景 LOD、资源加载和不同设备上的实际测量。没有物理手机或 RTX 性能数据。
