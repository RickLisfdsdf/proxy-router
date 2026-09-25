<div align="center">

[简体中文](README.md) | [English](README.en.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **한국어** | [Русский](README.ru.md)

# 🎯 proxy-router (분류 관리자)

**Clash Verge Rev에 "어떤 앱이 어떤 노드를 쓸지" 관리하는 웹 화면을 추가합니다**

Chrome은 일본, Claude는 미국 주거용 IP로 고정, Git은 홍콩, WeChat은 직접 연결 — 몇 번의 클릭으로 설정하고, 저장하는 즉시 적용됩니다.

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows)
![Clash Verge Rev](https://img.shields.io/badge/Clash%20Verge%20Rev-mihomo-6f42c1)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/RickLisfdsdf/proxy-router?style=social)

### [👉 온라인 데모 (설치 불필요)](https://ricklisfdsdf.github.io/proxy-router/)

</div>

> **참고:** 현재 웹 UI는 중국어 간체만 지원합니다. 번역 기여를 환영합니다.

![라우팅 규칙](docs/rules.png)

## 왜 만들었나

Clash는 프로세스별 라우팅(`PROCESS-NAME`)을 지원하지만, 실제로 쓰려면:

- YAML 규칙을 직접 작성하고 규칙 순서와 프록시 그룹 문법을 기억해야 합니다
- 구독이 업데이트될 때마다 직접 수정한 규칙이 사라집니다 (확장 스크립트 / Merge를 배워야 함)
- 규칙이 실제로 적용됐는지 연결 목록을 하나하나 확인해야 합니다
- "이 노드만 사용하고, 끊기면 연결을 차단하며, 다른 노드로 새지 않게" 하려면 프록시 그룹을 직접 만들어야 합니다

**proxy-router가 이 모든 걸 대신합니다**: 앱을 고르고, 노드를 고르고, 저장하면 끝.

## 기능

| | |
|---|---|
| 🖥️ **앱별 라우팅** | 프로세스 이름 / 프로세스 경로 정규식. 같은 `claude.exe` 이름을 가진 Claude 데스크톱과 Claude Code도 따로 지정 가능 |
| 🌐 **서비스별 라우팅** | 도메인, 도메인 키워드, geosite 분류, IP 대역, 포트 |
| 🔒 **노드 고정** | 지정한 노드만 사용. 노드가 죽으면 연결이 실패하고 **다른 노드로 절대 새지 않음** (IP에 민감한 AI·결제·계정 서비스에 적합) |
| 🔁 **우선 + 예비** | 주 노드가 불통이면 선택한 예비 노드로 자동 전환 |
| 🇨🇳 **중국 내 사이트 직접 연결** | 앱이 프록시를 거쳐도 중국 사이트는 직접 연결 |
| 👀 **실시간 확인** | 각 앱이 **실제로** 사용하는 경로와 적중한 규칙 표시. 통신 중인 앱에 클릭 한 번으로 노드 지정 |
| ⚡ **즉시 적용** | `mihomo -t`로 검증 후 핫 리로드. Clash Verge 재시작 불필요 |
| 🛡️ **구독 업데이트 후에도 유지** | 규칙은 Clash Verge 전역 확장 스크립트에 저장. 새 구독에 없는 노드는 자동으로 건너뛰어 설정 오류가 나지 않음 |
| 📋 **템플릿** | Chrome / Edge / Claude / ChatGPT / Gemini / Telegram / VS Code / Cursor / Git / npm / pip / Steam / Discord… |

<table>
<tr>
<td><img src="docs/editor.png" alt="규칙 편집"></td>
<td><img src="docs/apps.png" alt="통신 중인 앱"></td>
</tr>
<tr>
<td align="center">규칙 편집: 고정 / 우선 + 예비 노드</td>
<td align="center">각 앱이 실제로 쓰는 노드 확인</td>
</tr>
</table>

## 빠른 시작

**요구 사항:** Windows + [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev) (mihomo 코어) + Python 3.10+

```bash
git clone https://github.com/RickLisfdsdf/proxy-router.git
cd proxy-router
pip install -r requirements.txt
python app.py
```

브라우저에서 <http://127.0.0.1:9123> 을 엽니다. 이후에는 `启动分流管家.vbs` 를 더블클릭하면 백그라운드에서 실행됩니다.

**권장 설정:** Clash Verge에서 **TUN 모드**를 켜고 **규칙 모드**를 사용하세요. TUN이 꺼져 있으면 시스템 프록시를 읽지 않는 명령줄 프로그램(git, npm, Claude Code 등)은 잡히지 않습니다.

## 작동 원리

```
웹에서 규칙 편집 ─▶ rules.json
                      │
                      ├─▶ Clash Verge 전역 확장 스크립트 Script.js 생성 (업데이트·재시작 후에도 유지)
                      │
                      └─▶ 실행 중인 설정에 삽입 ─▶ verge-mihomo -t 검증 ─▶ 명명된 파이프로 핫 리로드 (즉시 적용)
```

- 규칙마다 `🎯 ` 로 시작하는 프록시 그룹이 생성되며 Clash Verge 프록시 화면에서도 보입니다
- 고정 = 노드 하나짜리 `select` 그룹, 우선 = `fallback` 그룹
- "중국 사이트 직접 연결"은 `AND,((PROCESS-NAME,xxx),(GEOSITE,cn))` 같은 논리 규칙으로 구현
- 첫 저장 시 기존 전역 스크립트를 `Script.js.before-proxy-router` 로 백업
- 로컬 mihomo와만 통신하며 외부로 아무것도 전송하지 않습니다

## 자주 묻는 질문

<details>
<summary><b>규칙 순서가 중요한가요?</b></summary>

네. 위에서 아래로 매칭되며 먼저 일치한 규칙이 적용됩니다. claude.ai를 어느 브라우저에서든 같은 노드로 쓰려면 "Claude 웹" **도메인** 규칙을 "Chrome" **앱** 규칙보다 위에 두세요.
</details>

<details>
<summary><b>구독 원래 규칙은 그대로인가요?</b></summary>

네. 내 규칙은 맨 앞에 삽입될 뿐이고, 일치하지 않은 트래픽은 기존처럼 구독 규칙을 따릅니다.
</details>

<details>
<summary><b>macOS / Linux는요?</b></summary>

현재는 Windows만 지원합니다 (Clash Verge Rev Windows 버전의 명명된 파이프와 설정 경로에 의존). PR 환영합니다.
</details>

## 응원하기

도움이 되셨다면 **⭐ Star** 를 눌러 주세요. 같은 고민을 가진 사람들이 찾기 쉬워집니다.

버그나 아이디어는 [Issues](https://github.com/RickLisfdsdf/proxy-router/issues) 로.

## License

[MIT](LICENSE)
