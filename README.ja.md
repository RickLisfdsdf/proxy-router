<div align="center">

[简体中文](README.md) | [English](README.en.md) | [繁體中文](README.zh-TW.md) | **日本語** | [한국어](README.ko.md) | [Русский](README.ru.md)

# 🎯 proxy-router（分流管家）

**Clash Verge Rev に「どのアプリをどのノード経由にするか」を管理する Web 画面を追加**

Chrome は日本、Claude は米国の住宅 IP に固定、Git は香港、WeChat は直接接続 —— 数クリックで設定、保存した瞬間に反映。

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)
![Clash Verge Rev](https://img.shields.io/badge/Clash%20Verge%20Rev-mihomo-6f42c1)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/RickLisfdsdf/proxy-router?style=social)

### [👉 オンラインデモ（インストール不要）](https://ricklisfdsdf.github.io/proxy-router/)

</div>

> **注意：** 現在、Web UI は簡体字中国語のみです。翻訳のコントリビュートを歓迎します。

![ルーティングルール](docs/rules.png)

## なぜ作ったか

Clash はプロセス単位のルーティング（`PROCESS-NAME`）に対応していますが、実際に使うには：

- YAML ルールを手書きし、ルールの順序やプロキシグループの書き方を覚える必要がある
- サブスクリプションが更新されるたびに手動の変更が消える（拡張スクリプト / Merge を覚える必要がある）
- ルールが本当に効いているか、接続一覧を一つずつ確認しないとわからない
- 「このノードだけを使い、落ちたら通信を止め、他のノードに漏らさない」にはプロキシグループを自作する必要がある

**proxy-router がすべて引き受けます**：アプリを選び、ノードを選び、保存するだけ。

## 機能

| | |
|---|---|
| 🖥️ **アプリ単位のルーティング** | プロセス名 / プロセスパスの正規表現。同じ `claude.exe` という名前の Claude デスクトップ版と Claude Code も別々に振り分け可能 |
| 🌐 **サービス単位のルーティング** | ドメイン、ドメインキーワード、geosite カテゴリ、IP 範囲、ポート |
| 🔒 **ノード固定** | 指定ノードのみ使用。ノードが落ちたら通信は失敗し、**他のノードには絶対に漏れない**（IP に敏感な AI・決済・アカウント系サービスに最適） |
| 🔁 **優先 + 予備** | メインノードが不通のとき、選んだ予備ノードへ自動で切り替え |
| 🇨🇳 **中国国内サイトは直接接続** | アプリがプロキシ経由でも、中国国内サイトは直接接続 |
| 👀 **リアルタイム確認** | 各アプリが**実際に**使っている経路とヒットしたルールを表示。通信中のアプリにワンクリックでノードを割り当て |
| ⚡ **即時反映** | `mihomo -t` で検証後にホットリロード。Clash Verge の再起動は不要 |
| 🛡️ **サブスク更新でも消えない** | ルールは Clash Verge のグローバル拡張スクリプトに保存。新しいサブスクに存在しないノードは自動でスキップし、設定エラーにならない |
| 📋 **テンプレート** | Chrome / Edge / Claude / ChatGPT / Gemini / Telegram / VS Code / Cursor / Git / npm / pip / Steam / Discord… |

<table>
<tr>
<td><img src="docs/editor.png" alt="ルール編集"></td>
<td><img src="docs/apps.png" alt="通信中のアプリ"></td>
</tr>
<tr>
<td align="center">ルール編集：固定 / 優先 + 予備ノード</td>
<td align="center">各アプリが実際に使っているノードを確認</td>
</tr>
</table>

## クイックスタート

**必要環境：** Windows + [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev)（mihomo コア）+ Python 3.10+

```bash
git clone https://github.com/RickLisfdsdf/proxy-router.git
cd proxy-router
pip install -r requirements.txt
python app.py
```

ブラウザで <http://127.0.0.1:9123> を開きます。次回からは `启动分流管家.vbs` をダブルクリックするとバックグラウンドで起動します。

**推奨設定：** Clash Verge で **TUN モード**を有効にし、**ルールモード**を使用してください。TUN なしでは、システムプロキシを読まないコマンドラインプログラム（git、npm、Claude Code など）は捕捉されません。

## 仕組み

```
Web でルール編集 ─▶ rules.json
                      │
                      ├─▶ Clash Verge のグローバル拡張スクリプト Script.js を生成（更新・再起動後も有効）
                      │
                      └─▶ 実行中の設定に挿入 ─▶ verge-mihomo -t で検証 ─▶ 名前付きパイプでホットリロード（即時反映）
```

- 各ルールは `🎯 ` で始まるプロキシグループを生成し、Clash Verge のプロキシ画面にも表示されます
- 固定 = ノード 1 つだけの `select` グループ、優先 = `fallback` グループ
- 「中国国内サイトは直接接続」は `AND,((PROCESS-NAME,xxx),(GEOSITE,cn))` のような論理ルールで実現
- 初回保存時に元のグローバルスクリプトを `Script.js.before-proxy-router` としてバックアップ
- 通信はローカルの mihomo とのみ。外部へは何も送信しません

## よくある質問

<details>
<summary><b>ルールの順序は重要？</b></summary>

はい。上から順に照合され、最初に一致したルールが適用されます。claude.ai をどのブラウザでも同じノードにしたい場合は、「Claude Web」の**ドメイン**ルールを「Chrome」の**アプリ**ルールより上に置いてください。
</details>

<details>
<summary><b>サブスクリプション本来のルールは残る？</b></summary>

残ります。あなたのルールは先頭に挿入されるだけで、一致しなかった通信は従来どおりサブスクのルールで処理されます。
</details>

<details>
<summary><b>macOS / Linux は？</b></summary>

現在は Windows のみ対応です（Clash Verge Rev の Windows 版の名前付きパイプと設定ディレクトリに依存）。PR 歓迎です。
</details>

## 応援

役に立ったら **⭐ Star** をお願いします。同じ悩みを持つ人が見つけやすくなります。

不具合やアイデアは [Issues](https://github.com/RickLisfdsdf/proxy-router/issues) へ。

## License

[MIT](LICENSE)
