# 资讯视频 Codex 工作流

把中文文稿和真实素材，制作成有视觉差异的9:16资讯视频。内含可安装Skill、三套可编辑Remotion版式、独立工程初始化、音画准备、保持音高的原声变速、配乐避让人声、全帧核验及项目内过程清理。

## 安装到自己的Codex

任何使用者都可以在Codex中发送：

> 使用 Skill Installer 安装这个技能：https://github.com/Predirector/news-video-workflow/tree/main/skills/news-video-workflow

安装整个`skills/news-video-workflow`目录，不能只复制SKILL.md。Skill内已包含运行工程和参考规范，不依赖仓库根目录或原作者的其他项目。安装后在下一轮聊天用`$news-video-workflow`调用；若当前Codex未刷新，重新打开聊天或重启应用。

本仓库公开，无需邀请或仓库访问授权即可下载。这个地址不会替别人授权飞书或视频平台。若没有Skill Installer，也可将整个技能目录复制到Codex支持的用户技能目录`~/.agents/skills/news-video-workflow`。

可复制的首次请求：

> 使用 $news-video-workflow，在我指定的工作目录创建独立工程，检查运行环境。补齐工具后引导我完成自己的飞书应用配置和登录，读取我指定的条目并下载附件，再搜索和补充缺失素材。先运行内置功能演示，再制作正式资讯视频。同批视频在字体、标题格局、色调、背景和资讯板上有实质差异。

已安装旧版的使用者，可让Codex从同一地址更新技能；更新前核对已有技能目录和个人改动，不覆盖本期工程、素材或账号配置。

## 首次配置

- 本地Node.js 20.19（20系列）或22.12以上、Python3.12以上；首次需联网安装锁定的Node依赖、隔离的Python依赖、官方字体和必要浏览器。字体不默默替换，下载失败/缺字会指出问题。现有工具先检查、可用则复用。
- 媒体路径由使用者自己的配置决定，没有原作者电脑用户名、盘符或其他工程依赖。
- 已集成官方飞书CLI的本地安装、应用配置引导、设备登录与状态检查；令牌管理和刷新由官方CLI负责。使用者在自己的账号完成一次授权，企业可能需要管理员批准。
- 提供按编号读取Docx/Wiki/Sheets、选中条目附件下载，以及网页图片、原版网页截图、yt-dlp视频下载和本地素材导入。搜索优先用Codex网页搜索，另有Commons、视频搜索及可选Brave后端。
- 真实视频、文章截图和配乐由Codex按当期采集/导入；默认字体从官方源获取，特殊授权字体由使用者提供。仓库不含客户原稿、真实视频、音乐库、Cookie、令牌或私钥。


## v1.2：把细则与实际视觉一起交接

此前v1.1的简化starter没有等价迁移原工程字体与全部细节，能运行不代表能复现原视觉。v1.2补上：

- [13组完整制作细则](skills/news-video-workflow/references/editorial-rules.md)，覆盖本项目连续对话中的标题/字体、封面、原版报道、单高亮、素材对应/重复/闪帧、两类字幕、背景、音乐卡点、文件归拢和条件性交付。
- [逐项实现与验收矩阵](skills/news-video-workflow/references/implementation-matrix.md)，明确自动检查、实际审看和未实现的条件分支，不能把规则当作工具已具备。
- 官方实际字体文件/字重与哈希、缺字检查、独立主副标题字体、真实花字厚度与底托；详见[字体与复现](skills/news-video-workflow/references/visual-reproduction.md)。
- 新工程生成AGENTS和完整规则；正式制作逐镜填写production-plan，渲染输出字体/规则/音乐节点分析及360px实际手机帧。清理前需要逐项、真实文件支持的审核记录。
- [样式学习工具与样式卡](skills/news-video-workflow/references/reference-library.md)，提取真实参考片，不猜字体/曲名，不把尚未实现的样式称作可用模板。

实际效果可查看[三套手机视觉基准](skills/news-video-workflow/assets/visual-baselines/README.md)，不是只看代码与字体名。

已有工程**不会**因Skill更新自动改变。先运行`upgrade_project.py`查看迁移计划；它保护当期脚本、素材和自定义源码，不能覆盖另一个Codex已经做过的独立布局。

## 连接与采集入口

安装后的技能目录记为`SKILL`，自己的新工程目录记为`PROJECT`：

```sh
python3 "$SKILL/scripts/news.py" --project "$PROJECT" setup --runtime
# 仅首次没有自己的飞书应用配置时：
python3 "$SKILL/scripts/news.py" --project "$PROJECT" connect --configure
# 按输出链接完成自己的授权，随后用返回的device code恢复：
python3 "$SKILL/scripts/news.py" --project "$PROJECT" connect --resume '<device-code>'
python3 "$SKILL/scripts/news.py" --project "$PROJECT" intake --url '<飞书链接>' --item '2.1' --download
python3 "$SKILL/scripts/news.py" --project "$PROJECT" collect --input '<上一步生成的result.json>'
```

已有飞书配置时直接`connect`，已有有效登录可直接`intake`。Codex负责发送授权链接、读取选题结果、核对素材并继续制作。系统Node/Python仍需先安装；平台登录、付费内容、验证码和DRM不由Skill绕过。视频按实际下载尺寸记账，不保证每个源都有1080P。

详细说明：[飞书连接](skills/news-video-workflow/references/feishu.md)、[素材采集](skills/news-video-workflow/references/acquisition.md)。

## 包含的制作标准

封面突出稿件核心，核心元素在中央3:4；主副标题按原稿、居中且横平竖直；真实图片与人物保留自然颜色。原声字幕整句切换，纯字幕资讯逐字/意群渐显；资讯板手机易读；报道只能用原版面、单一高亮；素材按语义匹配且避免近邻重复。音乐选连续段、以实际听感判断，讲话时压低；默认资讯尽量20秒以内，语速和超时原因按单期配置。

三套起始样式：

| 样式 | 主要变化 |
|---|---|
| paper-red | 明亮纸纹、普惠体Black标题、红白底托与对照板 |
| speed-yellow | 亮黄深墨、Noto Sans SC 900标题、速度/指标分组 |
| berry-progress | 暖白莓红、普惠体Heavy标题、阶段递进板 |

这些是可运行起点。Codex仍需从稿件核心出发选图、调整字体与结构、看实际编码结果，不能仅靠安装保证审美与选曲合格。

## 交付与边界

交付MP4、静态封面、SRT、来源JSON和可编辑Remotion工程。附带的SVG和合成节奏只为安装/功能演示，明确不是新闻证据或抖音音乐。

当前包不包含剪映自动转换、代替使用者完成登录/管理员审批、私有服务器或生成式图像/音乐服务。可通过官方CLI引导创建使用者自己的应用，但不是安装Skill就自动得到文档权限。可按实际需要另外接入。默认不把本机某一期1.1倍速、固定音乐或外接盘名称推广给所有新视频。

`.codex-plugin/plugin.json`另提供插件格式清单；本版主要验收安装路径为GitHub目录→Skill Installer→独立工程。这里不是公开插件商店上架声明。

安装与运行核验见[VALIDATION.md](VALIDATION.md)。第三方字体保留下载时的OFL声明，运行依赖按其各自许可使用。

本仓库原创代码与规范采用 [MIT License](LICENSE)。第三方依赖、字体和使用者自行提供的媒体继续遵守各自许可。

## v1.3：同一台电脑复用依赖

新工程默认共享相同锁定版本的 Node、Python 与采集工具环境，不再每期各装一份。项目仍保留自己的源码、清单和锁文件，依赖不同自动分组。原来的制作命令保持不变；已有独立环境保留，不自动清理。配置、隔离选项与旧工程迁移注意事项见[依赖复用](skills/news-video-workflow/references/shared-runtime.md)。
