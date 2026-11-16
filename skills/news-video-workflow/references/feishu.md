# 飞书连接与条目读取（v1.1）

统一入口是技能目录中的 `scripts/news.py`，不是工程内同名脚本。以下 `SKILL`、`PROJECT` 由Codex解析为实际路径，不照抄占位符。

## 首次连接

```sh
python3 "$SKILL/scripts/news.py" --project "$PROJECT" setup --runtime
python3 "$SKILL/scripts/news.py" --project "$PROJECT" connect --configure
```

`setup`在新目录创建工程，优先检查已有工具；缺少时在工程的`.news-tools`安装官方`@larksuite/cli`、yt-dlp与截图工具；`--runtime`同时安装视频运行依赖。没有Node/Python时报告缺项，由使用者安装系统运行时，不修改全局PATH或覆盖已有CLI。

`connect --configure`只用于首次创建自己的飞书应用：官方`config init --new`会给出链接，Codex后台保持进程运行，把原始授权链接交给使用者。使用者完成应用配置后进入登录。已有应用/CLI配置时用`connect`，不要重复创建应用。企业不允许自建应用时，由管理员配置自己的应用后再登录，不复用仓库作者的服务器。

登录使用官方设备授权，申请文档、表格、Wiki和附件下载的只读权限，不申请消息发送或文档写入。输出URL时把原始链接发给使用者；需要二维码时用实际CLI的`auth qrcode --help`生成。用户必须亲自完成登录/管理员审批；Skill不能代替这一步。

`--no-wait --json`返回验证链接及device code。用户完成授权后，用返回的device code恢复轮询：

```sh
python3 "$SKILL/scripts/news.py" --project "$PROJECT" connect --resume '<device-code>'
python3 "$SKILL/scripts/news.py" --project "$PROJECT" status
```

令牌及刷新交给官方CLI管理，申请`offline_access`，不导出令牌、不抄入聊天/源码。服务端必须实际签发refresh token；若租户未签发、已撤销或刷新失败，明确要求重新登录，不保证永久免登录。状态失败或刷新被撤销时重新`connect`；缺少scope时只补缺少的只读scope。飞书/Lark品牌和身份须与文档一致，所有读取以使用者身份执行。管理员尚未批准、文档未共享给当前身份、下载受限时明确指出阻塞，不擅自改权限。

## 读取指定条目及其附件

```sh
python3 "$SKILL/scripts/news.py" --project "$PROJECT" intake \
  --url '<Wiki/Docx/Sheets链接>' --item '2.1' --download
```

- Wiki先解析对象；Docx按块分页读取，识别表格行和数字标题分节；表格保留表头。只选明确匹配的条目，不把2.1与2.10混淆。
- 编号重复时不静默取第一条；Docx可加`--section '<准确的父级标题>'`，表格可加`--sheet '<sheetId>' --range A1:Z200`缩小范围。默认范围有上限，不把未读到的范围说成不存在。
- 正文找不到条目时尝试读取嵌入表格；不递归读取所有链接，不支持的对象（如bitable）明确报告，不能声称所有文档类型均支持。
- `--download`只下载选中条目的已识别附件/图片，复制到工程媒体库并校验SHA-256，再移除本次临时附件副本。不会删除使用者Downloads里的文件。
- 原文JSON和选择结果在工程`reports/intake-*/`，默认不入Git；结果包括选中原文、外链、附件和每项成功/失败状态。Codex应实际读这个结果，依据原文核对标题、脚本和视觉要求。
- 外链素材随后交给[素材采集](acquisition.md)，不是把正文里的所有链接都认作可直接下载的视频。

仍保留`feishu_read.py --url ... --output ...`低层接口：可加`--project "$PROJECT"`复用官方CLI；高级使用者也可使用自己`FEISHU_USER_ACCESS_TOKEN`或`FEISHU_TOKEN_FILE`，此手动令牌路径不会自动刷新。

## 官方来源

- CLI与登录/凭据管理：https://github.com/larksuite/cli
- CLI原始接口与下载输出：https://github.com/larksuite/cli/blob/main/cmd/api/api.go
- Wiki：https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview
- Docx：https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list
- 附件：https://open.feishu.cn/document/server-docs/docs/drive-v1/media/download

真实账号OAuth及管理员审批需要在接收者自己的租户完成。单元测试或CLI安装成功不等于接收者已获得文档权限。
