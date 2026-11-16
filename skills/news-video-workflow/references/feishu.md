# 飞书只读接入

优先复用使用者已有的飞书CLI/连接器。当前包不包含原作者的服务器、SSH私钥、应用密钥、刷新令牌或浏览器Cookie。

独立接口：

```sh
python3 <本技能目录>/scripts/feishu_read.py --url '<文档或Wiki链接>' --output '<工程目录>/source/feishu.json'
```

令牌通过当前进程的 `FEISHU_USER_ACCESS_TOKEN` 提供，也可通过 `FEISHU_TOKEN_FILE` 指向自己受保护的令牌文件（文件不入库）；不要把值写进聊天或命令参数。应用和使用者必须具备目标文档的实际阅读权限；只读令牌不扩大权限。Token过期、文档未授权、附件缺权限会明确报错。

Wiki先调用 `/wiki/v2/spaces/get_node` 取得对象类型/token，Docx分页读 `/docx/v1/documents/:id/blocks`；表格读工作表和数据范围。`--download-media DIR` 仅下载返回块里可读的附件和图片，使用 `/drive/v1/medias/:token/download`，保留成功/失败清单。嵌入表格的token会列在结果中，后续单独读取；不能把Docx正文读通说成嵌入表格及附件全部读通。

首次授权请在自己的飞书开放平台应用或既有CLI中完成。包不自动创建应用、不申请写文档或发消息权限，也不会把账号授权交给仓库作者。官方接口说明：

- https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview
- https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list
- https://open.feishu.cn/document/server-docs/docs/drive-v1/media/download
