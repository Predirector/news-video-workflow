# 字体、实际视觉基准与旧工程迁移

## 为什么v1.1在其他Mac上能出片却不像原工程

此前将本机工程改写成三个简化starter时，使用Noto宋/黑体代替了原有普惠体Black/Heavy/Bold和用户自有方正；规则被压缩成摘要，默认文字效果/字号层级并未等价迁移。安装与技术导出测试不能证明审美复现。缺少实际字体审计、手机视觉基准和旧工程更新路径，让偏差容易继续传播。

## 现在的确定字体方案

| 默认样式 | 标题实际字体 | 副标题实际字体 | 正文实际字体 |
|---|---|---|---|
| paper-red | 普惠体2.0 115 Black | 105 Heavy | 85 Bold |
| speed-yellow | Noto Sans SC变量字体选wght900 | 普惠体105 Heavy | 85 Bold |
| berry-progress | 普惠体105 Heavy | 85 Bold | 85 Bold |

`fontPreset=style-default`在准备时按样式绑定，不要求更换style后再手动猜字体。阿里字体从官网脚本公开引用的官方字体服务器获取，并使用正常官网Referer；仅下载到使用者本地，不把字体软件放入GitHub。对应SHA-256、来源在`font-catalog.json`。Noto字体同样固定文件哈希并保留OFL。

官方Black/Heavy与本机旧文件的整体哈希不同；逐表实测字形轮廓glyf、宽度hmtx以及字符→glyph索引相同，差异在name/cmap等表的组织。因此不冒称文件逐字节相同。公共安装以后以catalog固定的官方文件为准，`reports/font-audit.json`记录实得身份、字重、缺字与哈希。

字体下载失败、文件变化、字形缺失或真实字重不合要求时明确停止，不能偷偷加载系统字体；默认渲染`fontSynthesis:none`，并等待FontFace加载完成。检查字重不意味着仅靠数值判断美感，仍要看真实字面。

方正汉真广标、苹方等原样复刻需要使用者自己的合法字体文件。导入不会安装系统字体或删除原件：

```sh
python3 "$SKILL/scripts/news.py" --project "$PROJECT" fonts \
  --title '<标题字体.ttf>' --subtitle '<副标题字体.ttf>' --body '<正文字体.ttf>'
```

它使用工程隔离Python，需先bootstrap，保存为`fontPreset=custom`。若某真实粗字文件元数据是Regular（如部分标题字库），不能用CSS伪加粗蒙混；实际审看后填写`fontExceptions:{titleStrokeReviewed:true,titleReason:"具体字体及真实字面粗度判断依据"}`，在人工审核中记录。这个例外不自动发放给所有Regular字体。

## 标准如何进入工程

初始化除了源码，还会复制完整制作规则和落实表，生成AGENTS入口。正式制作按`production-plan.example.json`填写本期计划（Codex填，不让用户填技术表），并配置准确的expectedTitles、原图来源和字幕。

`prepare.py`输出：

- `font-audit.json`：实际文件、字体名/子族、字重、缺字检查与哈希。
- `production-audit.json`：安全区、标题与图槽关系、文本适配、单一标记等可测结果；人工审看清单独立列出，不自动全打通过。
- `music-analysis.json`：真实连续配乐片段的谱通量起音候选和切点距离。它不判定抖音热度、新闻听感或所有候选都是重拍，仍要试听及做语义/阅读取舍。

`verify.py`检查真实编码，增加360px封面及每段打字早/中/全文后的手机帧。按`review.example.json`记录实际看的文件及封面、字体、手机字面、证据、字幕/停留、转场/闪帧和音乐结论。清理不接受一个孤立的passed=true。记录存在并不证明人已审看，不得替没有做过的检查填“通过”。

## 视觉基准

技能内`assets/visual-baselines/`包括三套默认样式的实际封面、照片/正片手机图及字体/布局记录。对照时检查：实际文件哈希、主副标题字形/字重、颜色/厚度/底托、中央安全区、中部画幅、下方板型、正文居中/关键词与纹理。

这些是本包自制的演示基准，不是对历史每一期视频的完整复制，也不是新闻事实/音乐已验收的成片。需要精确复刻指定历史模板时必须拿到该模板的实际源码、字体和必要参考；不能仅凭“paper-red”这个名称宣称相同。

## 已创建工程不会随Skill自动升级

先预检，不写入；已改过的源码会列为blocked：

```sh
python3 "$SKILL/scripts/upgrade_project.py" "$PROJECT"
# 仅当列出的都是可以迁移的未改starter文件时：
python3 "$SKILL/scripts/upgrade_project.py" "$PROJECT" --apply
```

迁移器识别v1.1原始文件哈希，只更新未被改过的工具/模板；保留原稿文字、片段时码、媒体、成片和runtime.local配置。不擅自覆盖其他Codex已开发的布局和AGENTS；这些需要对照新规则有选择地移植。

迁移后重新bootstrap、prepare、实际渲染和手机检查；不是装新版Skill就认为旧工程字体已经改好。原稿只有默认Noto示例配置的旧工程会明确切到style-default；自定义字体保留为custom，并补独立副标题绑定，仍需核对授权和实际效果。

官方字体入口：https://fonts.alibabagroup.com/ 。Remotion字体加载依据：https://www.remotion.dev/docs/fonts 。字体许可与本仓库MIT代码许可分别适用。
