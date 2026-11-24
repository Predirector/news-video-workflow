# 依赖复用 v1.3

新工程的 bootstrap.py 默认把 Node、Python 安装到本机共享运行目录，通过 node_modules、.venv 引用；news.py setup 同样复用 .news-tools。原有制作命令不变。源码、素材、字体角色配置、package.json、package-lock.json、requirements.txt 仍各期独立。

默认目录为 macOS/Linux 的 ~/.local/share/news-video-workflow/runtimes，Windows 的 %LOCALAPPDATA%/news-video-workflow/runtimes。可用 NEWS_RUNTIME_ROOT 选择另一个本机内盘目录；不要选择 exFAT、云盘或将可执行环境随媒体打包。所有后续安装使用同一配置。runtime-links.local.json 记录本机指向，不提交仓库。

Node 按 package.json、完整 npm 锁文件、系统架构与 Node ABI 分组；Python 按 requirements、解释器版本/路径、系统架构分组。采集工具按固定版本分组。不同组合独立安装；没有修改既有锁文件，也不强行合并不兼容依赖。npm ci 继续使用原锁文件和本机 npm 缓存，Python 有 uv 时复用 uv 下载缓存。

共享安装带互斥锁；失败后可重新运行，不通过伪造完成标记跳过依赖检查。遇到等待中的安装不要删除活动锁。

已有真实目录不自动移动或删除，继续按原入口运行。bootstrap.py --local 可显式创建隔离环境；它也不会覆盖其他来源的链接。安装包不批量回收历史项目。

迁移已有工程时：先检查锁文件和个人改动，在新的独立工程验证相同依赖的共享环境和实际渲染，再核对旧环境是否还有其他消费者。Python venv 不直接搬移复制。保存精确清单、旧占用、共享目标及渲染证据后，显式迁移对应引用，再从原入口复验；不能验证的旧环境保留。删除一个工程不能递归删除它链接到的共享环境。

共享环境禁止在单期工程内随意 npm install / pip install。需要新依赖时，先更新该项目清单及锁文件，再创建对应版本的新环境，不能修改其他项目在用的共享目录。转交工程时不打包 node_modules/.venv/.news-tools 或本机链接；接收者保留清单，在自己的机器运行 bootstrap/setup 重建引用。

Windows 使用目录 junction；若权限或文件系统不支持，明确报错，可显式选 --local 隔离，不静默复制。Windows/Linux 分支尚需目标机器实测，macOS 验证不能视为跨系统已验收。
