<div align="center">

# 🎯 分流管家 · proxy-router

**给 Clash Verge Rev 加一个「哪个软件走哪个节点」的可视化管理页面**

Chrome 走日本、Claude 锁定美国住宅 IP、Git 走香港、微信直连——点几下就配好，保存立即生效。

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)
![Clash Verge Rev](https://img.shields.io/badge/Clash%20Verge%20Rev-mihomo-6f42c1)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/RickLisfdsdf/proxy-router?style=social)

### [👉 在线试玩（演示模式，不用安装）](https://ricklisfdsdf.github.io/proxy-router/)

</div>

![分流规则](docs/rules.png)

## 为什么做这个

Clash 本身支持按进程分流（`PROCESS-NAME`），但要用起来得：

- 手写 YAML 规则，还得记住规则顺序、代理组语法
- 订阅一更新，手改的规则就没了，要学「扩展脚本 / Merge」
- 改完不知道到底生效没，要去连接列表里一条条翻
- 想「只能走这个节点，挂了就断网，别漏到别的节点」，还得自己建代理组

**分流管家把这些全包了**：网页上选软件、选节点、点保存，剩下的它来做。

## 功能

| | |
|---|---|
| 🖥️ **按软件分流** | 进程名 / 进程路径正则。比如同样叫 `claude.exe` 的 Claude 桌面版和 Claude Code 也能分开 |
| 🌐 **按服务分流** | 域名、域名关键字、geosite 分类、IP 段、端口 |
| 🔒 **锁定节点** | 只能走指定节点，节点挂了就断网，**绝不会漏到别的节点**（适合对 IP 敏感的 AI、支付、账号类服务） |
| 🔁 **优先 + 备用** | 主节点不通时自动切到你勾选的备用节点 |
| 🇨🇳 **国内网站直连** | 软件走代理时，国内网站仍然直连，不绕路 |
| 👀 **实时验证** | 看每个软件**实际**走的是哪条链路、命中了哪条规则；一键给正在联网的软件指定节点 |
| ⚡ **立即生效** | 先用 mihomo 校验配置，再热加载，不用重启 Clash Verge |
| 🛡️ **订阅更新也不丢** | 规则写进 Clash Verge 的全局扩展脚本；换订阅后找不到的节点会自动跳过，不会让配置报错 |
| 📋 **常用模板** | Chrome / Edge / Claude / ChatGPT / Gemini / Telegram / VS Code / Cursor / Git / npm / pip / Steam / Discord… |

<table>
<tr>
<td><img src="docs/editor.png" alt="编辑规则"></td>
<td><img src="docs/apps.png" alt="正在联网的软件"></td>
</tr>
<tr>
<td align="center">编辑规则：锁定 / 优先 + 备用节点</td>
<td align="center">实时查看每个软件实际走的节点</td>
</tr>
</table>

## 快速开始

**前提**：Windows + [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev)（mihomo 内核）+ Python 3.10+

```bash
git clone https://github.com/RickLisfdsdf/proxy-router.git
cd proxy-router
pip install -r requirements.txt
python app.py
```

浏览器打开 <http://127.0.0.1:9123> 就能用。以后也可以双击 `启动分流管家.vbs` 在后台启动。

**建议设置**：Clash Verge 里打开 **TUN 模式**，并使用**规则模式**。不开 TUN 的话，不读系统代理的命令行程序（git、npm、Claude Code 等）不会被接管。

## 工作原理

```
网页编辑规则 ─▶ rules.json
                  │
                  ├─▶ 生成 Clash Verge 全局扩展脚本 Script.js（订阅更新、重启后规则依然在）
                  │
                  └─▶ 插入当前运行配置 ─▶ verge-mihomo -t 校验 ─▶ 命名管道热加载（立即生效）
```

- 每条规则会生成一个以 `🎯 ` 开头的代理组，在 Clash Verge 的代理页面也能看到
- 锁定 = 只有一个节点的 `select` 组；优先 = `fallback` 组
- 「国内网站直连」用 `AND,((PROCESS-NAME,xxx),(GEOSITE,cn))` 这类组合规则实现
- 首次保存会把原来的全局扩展脚本备份为 `Script.js.before-proxy-router`
- 全程只和本机的 mihomo 通信，不联网上传任何东西

## 常见问题

<details>
<summary><b>规则顺序有什么讲究？</b></summary>

从上往下匹配，先命中的生效。如果你想让 claude.ai 不管在哪个浏览器里都走同一个节点，就把「Claude 网页」这条**域名**规则放到「Chrome」这条**软件**规则上面。
</details>

<details>
<summary><b>保存后原来的订阅分流还在吗？</b></summary>

在。你的规则只是插在最前面，没被命中的流量照常按订阅原有规则走。
</details>

<details>
<summary><b>Claude 桌面版和 Claude Code 都叫 claude.exe，怎么分开？</b></summary>

用模板里的「Claude 桌面版」「Claude Code」，它们按进程路径（`PROCESS-PATH-REGEX`）区分。
</details>

<details>
<summary><b>能在 Clash Verge 里继续手动改全局扩展脚本吗？</b></summary>

不建议，下次在网页里保存时会被覆盖。需要自定义的话请提 Issue。
</details>

<details>
<summary><b>支持 macOS / Linux 吗？</b></summary>

目前只支持 Windows（依赖 Clash Verge Rev 在 Windows 上的命名管道控制接口和配置目录）。欢迎 PR。
</details>

## 路线图

- [ ] 从「正在运行的程序」列表里直接挑选软件
- [ ] 规则导入 / 导出，分享给朋友
- [ ] 开机自启选项
- [ ] macOS / Linux 支持
- [ ] 支持 Clash Party、FlClash 等其他 mihomo 客户端

## 支持一下

如果这个项目帮你省了时间，**点个 ⭐ Star** 吧，这能让更多有同样需求的人找到它。

遇到问题或有想法，欢迎提 [Issue](https://github.com/RickLisfdsdf/proxy-router/issues)。

[![Star History Chart](https://api.star-history.com/svg?repos=RickLisfdsdf/proxy-router&type=Date)](https://star-history.com/#RickLisfdsdf/proxy-router&Date)

## License

[MIT](LICENSE)
