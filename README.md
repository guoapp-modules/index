# guoapp 模块索引

应用内模块商店读取本仓库的 `index.json`。

## 工作方式

- `modules.json` 列出已上架的模块仓库，由维护者手动修改。
- 定时任务每 6 小时（也可在 Actions 里手动运行）查一遍这些仓库的最新 Release，取出该标签下的 `manifest.json` 和 `main.js`，校验后把版本、标签和两个文件的 sha256 写进 `index.json`。
- 上架的模块都在 guoapp-modules 组织内，代码改动经维护者合并、由维护者打标签发版，新版本直接更新进索引。
- 应用按索引里的标签从 GitHub 或 jsDelivr 下载这两个文件，sha256 不符就拒绝安装，所以发版后再改动标签或文件不会生效。

## 上架

1. 在自己的账号下用 [template](https://github.com/guoapp-modules/template) 写好模块，发布 Release。
2. 在本仓库开 issue 申请上架，附上模块仓库地址。
3. 维护者按下面的要求审核。通过后会邀请你加入 guoapp-modules 组织，接受邀请后，在模块仓库的 Settings › General › Transfer ownership 里把仓库转到 guoapp-modules。
4. 维护者把仓库加进 `modules.json`，下次更新索引时上架。

要求：

- 仓库公开，仓库名与模块标识相同，用 template 的 CI 发版。
- 以 GPL-3.0 许可发布，根目录保留 template 自带的 `LICENSE`。
- 代码可读，不压缩、不混淆。
- 只请求清单 `hosts` 里的域名，用途与站源功能相符。
- 不收集或上传与站源功能无关的用户数据，不下载执行远程代码。
- 标识和别名不与已上架的模块重复。

转入后你仍是仓库的协作者，提交记录照旧保留，可以管理 issue 和 PR。之后的代码改动从你的 fork 提 PR，由维护者合并并发版。

## 请求新站源

想要还没有的站源，可以在本仓库用「请求新站源」模板开 issue。站源由社区自愿编写，请求不保证会有人接手。

## 撤下

违反上述要求、站点长期失效或站点权利人要求时，从 `modules.json` 删除该仓库，下次更新时从索引移除。已安装的用户不受影响，只是不再收到更新。
