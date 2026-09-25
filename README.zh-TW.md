<div align="center">

[简体中文](README.md) | [English](README.en.md) | **繁體中文** | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# 🎯 分流管家 · proxy-router

**為 Clash Verge Rev 加上「哪個軟體走哪個節點」的視覺化管理頁面**

Chrome 走日本、Claude 鎖定美國住宅 IP、Git 走香港、微信直連——點幾下就設定好，儲存立即生效。

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)
![Clash Verge Rev](https://img.shields.io/badge/Clash%20Verge%20Rev-mihomo-6f42c1)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/RickLisfdsdf/proxy-router?style=social)

### [👉 線上試玩（示範模式，免安裝）](https://ricklisfdsdf.github.io/proxy-router/)

</div>

> **說明：** 網頁介面目前是簡體中文。

![分流規則](docs/rules.png)

## 為什麼做這個

Clash 本身支援依程序分流（`PROCESS-NAME`），但要實際用起來得：

- 手寫 YAML 規則，還要記得規則順序、代理組語法
- 訂閱一更新，手改的規則就不見了，得學「擴充腳本 / Merge」
- 改完不知道到底有沒有生效，要去連線列表一條條翻
- 想要「只能走這個節點，掛了就斷網，不能漏到別的節點」，還得自己建代理組

**分流管家把這些全包了**：網頁上選軟體、選節點、按儲存，剩下的交給它。

## 功能

| | |
|---|---|
| 🖥️ **依軟體分流** | 程序名稱 / 程序路徑正規表示式。例如同樣叫 `claude.exe` 的 Claude 桌面版和 Claude Code 也能分開 |
| 🌐 **依服務分流** | 網域、網域關鍵字、geosite 分類、IP 範圍、連接埠 |
| 🔒 **鎖定節點** | 只能走指定節點，節點掛了就斷網，**絕不會漏到別的節點**（適合對 IP 敏感的 AI、支付、帳號類服務） |
| 🔁 **優先 + 備用** | 主節點不通時自動切到你勾選的備用節點 |
| 🇨🇳 **中國大陸網站直連** | 軟體走代理時，大陸網站仍然直連，不繞路 |
| 👀 **即時驗證** | 看每個軟體**實際**走的是哪條鏈路、命中哪條規則；一鍵為正在連網的軟體指定節點 |
| ⚡ **立即生效** | 先用 mihomo 驗證設定，再熱重載，不用重啟 Clash Verge |
| 🛡️ **訂閱更新也不會掉** | 規則寫進 Clash Verge 的全域擴充腳本；換訂閱後找不到的節點會自動略過，不會讓設定出錯 |
| 📋 **常用範本** | Chrome / Edge / Claude / ChatGPT / Gemini / Telegram / VS Code / Cursor / Git / npm / pip / Steam / Discord… |

<table>
<tr>
<td><img src="docs/editor.png" alt="編輯規則"></td>
<td><img src="docs/apps.png" alt="正在連網的軟體"></td>
</tr>
<tr>
<td align="center">編輯規則：鎖定 / 優先 + 備用節點</td>
<td align="center">即時查看每個軟體實際走的節點</td>
</tr>
</table>

## 快速開始

**前提**：Windows + [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev)（mihomo 核心）+ Python 3.10+

```bash
git clone https://github.com/RickLisfdsdf/proxy-router.git
cd proxy-router
pip install -r requirements.txt
python app.py
```

瀏覽器開啟 <http://127.0.0.1:9123> 即可使用。之後也可以雙擊 `启动分流管家.vbs` 在背景啟動。

**建議設定**：在 Clash Verge 開啟 **TUN 模式**並使用**規則模式**。不開 TUN 的話，不讀系統代理的命令列程式（git、npm、Claude Code 等）不會被接管。

## 運作原理

```
網頁編輯規則 ─▶ rules.json
                  │
                  ├─▶ 產生 Clash Verge 全域擴充腳本 Script.js（訂閱更新、重啟後規則依然在）
                  │
                  └─▶ 插入目前執行中的設定 ─▶ verge-mihomo -t 驗證 ─▶ 命名管道熱重載（立即生效）
```

- 每條規則會產生一個以 `🎯 ` 開頭的代理組，在 Clash Verge 的代理頁面也看得到
- 鎖定 = 只有一個節點的 `select` 組；優先 = `fallback` 組
- 「大陸網站直連」用 `AND,((PROCESS-NAME,xxx),(GEOSITE,cn))` 這類組合規則實現
- 第一次儲存時會把原本的全域擴充腳本備份為 `Script.js.before-proxy-router`
- 全程只和本機的 mihomo 通訊，不會上傳任何東西

## 常見問題

<details>
<summary><b>規則順序有什麼講究？</b></summary>

由上往下比對，先命中的生效。如果希望 claude.ai 不論在哪個瀏覽器都走同一個節點，就把「Claude 網頁」這條**網域**規則放在「Chrome」這條**軟體**規則上面。
</details>

<details>
<summary><b>儲存後原本的訂閱分流還在嗎？</b></summary>

在。你的規則只是插在最前面，沒被命中的流量照常依訂閱原有規則走。
</details>

<details>
<summary><b>還能在 Clash Verge 裡手動改全域擴充腳本嗎？</b></summary>

不建議，下次在網頁儲存時會被覆蓋。需要自訂的話請開 Issue。
</details>

<details>
<summary><b>支援 macOS / Linux 嗎？</b></summary>

目前只支援 Windows（依賴 Clash Verge Rev 在 Windows 上的命名管道控制介面和設定目錄）。歡迎 PR。
</details>

## 支持一下

如果這個專案幫你省了時間，**按個 ⭐ Star** 吧，能讓更多有同樣需求的人找到它。

問題或想法歡迎開 [Issue](https://github.com/RickLisfdsdf/proxy-router/issues)。

## License

[MIT](LICENSE)
