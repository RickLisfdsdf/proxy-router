<div align="center">

[简体中文](README.md) | **English** | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# 🎯 proxy-router

**A visual "which app uses which proxy node" manager for Clash Verge Rev**

Chrome through Japan, Claude locked to a US residential IP, Git through Hong Kong, WeChat direct — set it up in a few clicks, live the moment you save.

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)
![Clash Verge Rev](https://img.shields.io/badge/Clash%20Verge%20Rev-mihomo-6f42c1)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/RickLisfdsdf/proxy-router?style=social)

### [👉 Try the live demo (no install needed)](https://ricklisfdsdf.github.io/proxy-router/)

</div>

> **Note:** the web UI is currently in Simplified Chinese only. Translations are welcome — see [Contributing](#support).

![Routing rules](docs/rules.png)

## Why

Clash already supports per-process routing (`PROCESS-NAME`), but to actually use it you have to:

- Hand-write YAML rules and remember rule order and proxy-group syntax
- Lose your edits every time the subscription updates, unless you learn extension scripts / Merge
- Dig through the connection list to see whether a rule actually works
- Build your own proxy groups if you want "use only this node — if it's down, cut the connection, never leak to another node"

**proxy-router does all of that for you**: pick an app, pick a node, click save.

## Features

| | |
|---|---|
| 🖥️ **Per-app routing** | By process name or process-path regex — e.g. Claude Desktop and Claude Code, both named `claude.exe`, can be routed separately |
| 🌐 **Per-service routing** | Domain, domain keyword, geosite category, IP range, port |
| 🔒 **Lock to a node** | Only the chosen node is used; if it's down the connection fails and **never leaks to another node** (ideal for IP-sensitive AI, payment and account services) |
| 🔁 **Preferred + backups** | Automatically fails over to the backup nodes you pick |
| 🇨🇳 **Mainland China sites direct** | While an app goes through a proxy, Chinese websites still connect directly |
| 👀 **Live verification** | See the chain each app is **actually** using and which rule it hit; assign a node to any app currently online in one click |
| ⚡ **Instant apply** | Validated with `mihomo -t`, then hot-reloaded — no Clash Verge restart |
| 🛡️ **Survives subscription updates** | Rules live in Clash Verge's global extension script; nodes missing from a new subscription are skipped instead of breaking the config |
| 📋 **Templates** | Chrome / Edge / Claude / ChatGPT / Gemini / Telegram / VS Code / Cursor / Git / npm / pip / Steam / Discord… |

<table>
<tr>
<td><img src="docs/editor.png" alt="Edit rule"></td>
<td><img src="docs/apps.png" alt="Apps online"></td>
</tr>
<tr>
<td align="center">Edit a rule: lock / preferred + backups</td>
<td align="center">See which node every app is really using</td>
</tr>
</table>

## Quick start

**Requirements:** Windows + [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev) (mihomo core) + Python 3.10+

```bash
git clone https://github.com/RickLisfdsdf/proxy-router.git
cd proxy-router
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:9123>. Afterwards you can double-click `启动分流管家.vbs` to start it in the background.

**Recommended:** enable **TUN mode** and use **Rule mode** in Clash Verge. Without TUN, command-line programs that ignore the system proxy (git, npm, Claude Code…) won't be captured.

## How it works

```
Edit rules in the web UI ─▶ rules.json
                               │
                               ├─▶ Generate Clash Verge global extension script Script.js (survives updates/restarts)
                               │
                               └─▶ Patch the running config ─▶ verge-mihomo -t ─▶ hot reload via named pipe (instant)
```

- Each rule creates a proxy group prefixed with `🎯 `, also visible in Clash Verge's Proxies page
- Lock = a `select` group with a single node; Preferred = a `fallback` group
- "China sites direct" uses logic rules such as `AND,((PROCESS-NAME,xxx),(GEOSITE,cn))`
- The first save backs up your original global script as `Script.js.before-proxy-router`
- Talks only to the local mihomo instance — nothing is uploaded anywhere

## FAQ

<details>
<summary><b>Does rule order matter?</b></summary>

Yes — rules are matched top to bottom and the first match wins. If you want claude.ai to use the same node in every browser, put the "Claude web" **domain** rule above the "Chrome" **app** rule.
</details>

<details>
<summary><b>Do my subscription's own rules still work?</b></summary>

Yes. Your rules are only inserted at the top; anything they don't match falls through to the subscription's rules as before.
</details>

<details>
<summary><b>Can I still edit the global extension script in Clash Verge by hand?</b></summary>

Not recommended — it is overwritten on the next save. Open an issue if you need customization.
</details>

<details>
<summary><b>macOS / Linux?</b></summary>

Windows only for now (it relies on Clash Verge Rev's Windows named-pipe controller and config paths). PRs welcome.
</details>

## Roadmap

- [ ] Pick apps straight from a list of running programs
- [ ] Import / export rules to share with friends
- [ ] English UI
- [ ] Start on boot option
- [ ] macOS / Linux support
- [ ] Support other mihomo clients (Clash Party, FlClash…)

## Support

If this saves you time, **please give it a ⭐ Star** — it helps others with the same problem find it.

Bugs and ideas: [Issues](https://github.com/RickLisfdsdf/proxy-router/issues).

[![Star History Chart](https://api.star-history.com/svg?repos=RickLisfdsdf/proxy-router&type=Date)](https://star-history.com/#RickLisfdsdf/proxy-router&Date)

## License

[MIT](LICENSE)
