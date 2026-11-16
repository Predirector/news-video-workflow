# 配置与制作命令

`assets/starter` 被初始化到独立工程后，所有命令在该工程目录运行。首次：

```sh
python3 scripts/bootstrap.py
node scripts/python.mjs prepare.py
node scripts/render.mjs --cover
node scripts/render.mjs --frame 60
node scripts/render.mjs
node scripts/python.mjs verify.py
```

`bootstrap.py` 检查依赖；Node依赖固定版本并带lockfile，Python隔离在工程`.venv`。字体首次从Google Fonts下载Noto Sans SC、Noto Serif SC及OFL声明，不带作者电脑的字体。浏览器先复用 `REMOTION_BROWSER_EXECUTABLE` 或 `runtime.local.json` 的 `browserExecutable`，否则按Remotion安装。FFmpeg依次从 `FFMPEG_PATH`、本机PATH、Remotion平台组件查找。不要写死作者环境。

媒体可通过 `runtime.local.json` 的 `mediaRoot` 或 `NEWS_MEDIA_ROOT` 指向自己的媒体目录；该目录必须先存在。大素材、处理件与输出在其中的public/output；代码、依赖、配置和JSON核验留工程目录。没设置时使用工程自己的public/output。运行时配置不入Git。

## episode.json

- `name`：最终文件名，不含扩展名，使用原稿完整编号与条目标题。
- `mode`：`news`（纯字幕）或`speech`（原声切片）。
- `style`：`paper-red`（纸感对照）、`speed-yellow`（亮黄深墨）、`berry-progress`（暖白莓红）。允许在`src/Root.tsx`中发展新模板。
- `mainTitle`、`subtitle`：逐行数组；合并后应逐字等于原稿给定文案。行太长时重新断行，不能直接改写。
- `expectedTitles`：可选原稿校验对象，包含`main`和`subtitle`原文字符串；与上面逐行合并不符时停止，防止封面副标题被意外改写。
- `message`：核心命题；`durationReason`：超过20秒时说明保留必要信息/原声的理由。
- `speechRate`：原声可选倍速，默认1；用户要求时可1.1。`news`忽略此参数。音乐保持原速。
- `fonts`：`title`、`body`均为public内相对路径。可用自己合法可用的字体；同批片子协调变化字形，不牺牲正文易读性。
- `cover`：`asset`为原始静态图片，`focus`可选例如`50% 40%`，`keywords`最多两条简短关键词。自行从真实原片选帧时把原帧导入，不生成虚构事件照片。
- `background.asset`：可选真实模糊背景；无此项时使用固定种子纸纹与柔和色区。
- `bgm`：`asset`、`start`、`sourceUrl`、`channelUrl`、`credit`。音源应是连续可用段；`channelUrl`是抖音/汽水发现页，未核验填null并说明，不填假链接。当前episode明确不加音乐时设置`allowSilent: true`。
- `sources`：每项`asset`、`sourceUrl`、`purpose`（fact/context/demo）及必要身份/年份/署名。
- `demo`：仅功能演示时为true；真实制作设false，不能用内置demo图冒充新闻素材。

## segments

每个片段包含：

```json
{
  "asset": "media/original-video.mp4",
  "kind": "video",
  "sourceStart": 715.3,
  "duration": 7.766,
  "voice": true,
  "caption": "完整同期字幕短句",
  "focus": "50% 50%",
  "keywords": ["关键字"],
  "info": {
    "type": "comparison",
    "items": [
      {"label":"原预计约","value":"30%"},
      {"label":"实际","value":"＞70%","active":true}
    ]
  }
}
```

`duration`和`sourceStart`以原素材秒计，工具按所选倍速编译输出帧数。图片使用`kind:image`，原声片中的静音插图不设voice。素材先用`node scripts/python.mjs import_media.py '<文件>' --source-url '<来源>'`复制并校验到public/media，不依赖Downloads原路径。

需要精确裁切时设置 `crop:[x,y,width,height]`（原视频像素）；不设置则等比cover和focus。要保全横版文章原文，先从原版面裁出所需原文区域，或调整`layout.picture:[left,top,width,height]`，不能重排文章。图片支持`mark:[x,y,width,height]`，这是裁切后显示框内的归一化高亮矩形；标记截图不做前景推拉，避免标记漂移；不支持给移动视频随意加静态框。

`info`支持：

- `text`：`heading`可选，`lines`正文数组，`keywords`可选。
- `comparison`或`metrics`：`items:[{label,value,active}]`，通常2或3列。
- `progression`：`steps`、`active`、`headline`、`condition`。例如三部曲后All in，目标/预计等范围与指标一起写清楚。

纯字幕模式在下方资讯板显示`caption`，逐字显现且保留读完停留；原声模式在画内整句显示，下方显示`info`。原声可另外设置全局 `subtitles:[{start,end,text,keywords}]`，时间是剪辑后原速语音时间线、从0秒起、不含前三帧封面；工具同步除以语速。也可提供`speechAsset`替代逐视频取声，此时不要给片段再设voice=true；独立音轨应已按原速剪成与整条视觉时间线对应的版本。

## 审核和清理

自动核验生成实际编码联系表、SRT、发布文案和来源JSON。检查后写`reports/review.json`：

```json
{"passed":true,"checked":["实际封面","实际编码联系表","切镜边界","音画与字幕"],"notes":"写清实际核验结论；有问题时passed=false"}
```

再运行 `node scripts/python.mjs cleanup.py --apply`，只清理登记的过程音轨/检查帧，执行真实渲染并复核成片哈希。输出主文件使用固定正式名称，渲染通过后替换旧成片；独有原件与当前工程保留。脚本不会自动删除用户Downloads。

PDF附件先按原页渲染为图片再裁取需要的原文区域；视频渲染器不直接把PDF当图片，也不重排PDF文字冒充报道。
