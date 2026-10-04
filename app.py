"""分流管家：本地网页管理 Clash Verge (mihomo) 的「软件/服务 → 节点」分流规则。

工作方式：
  1. 规则存在 rules.json
  2. 保存时生成 Clash Verge 的全局扩展脚本 profiles/Script.js，以后 Verge 每次生成配置都会带上
  3. 同时把规则插进当前运行配置，先用 mihomo -t 校验，再通过命名管道热加载，立即生效
所有自动生成的代理组、节点提供者都以「🎯 」开头，便于识别和替换。
规则目标除了当前订阅里的节点，还可以是「其他订阅」：把那个订阅的链接作为节点提供者接进来，
选里面延迟最低的节点（url-test），或锁定其中某个节点。主订阅照常用，换主订阅也不影响这类规则。
"""
import copy
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

import yaml
from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE, "rules.json")
VERGE_DIR = os.path.join(os.environ["APPDATA"], "io.github.clash-verge-rev.clash-verge-rev")
RUNTIME_YAML = os.path.join(VERGE_DIR, "clash-verge.yaml")
SCRIPT_JS = os.path.join(VERGE_DIR, "profiles", "Script.js")
PROFILES_YAML = os.path.join(VERGE_DIR, "profiles.yaml")
PREFIX = "🎯 "
SELF_PREFIX = "🏠 "  # 自建节点（rules.json 里的 self_nodes）注入到配置时的名字前缀
LAN_GROUP = PREFIX + "局域网直连"
CN_GROUP = PREFIX + "国内直连"
LAN_CIDRS = ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
             "169.254.0.0/16", "100.64.0.0/10", "fc00::/7", "fe80::/10"]
TEST_URL = "https://www.gstatic.com/generate_204"
BUILTIN = {"DIRECT", "REJECT"}
GROUP_TYPES = {"Selector", "URLTest", "Fallback", "LoadBalance", "Relay"}
SKIP_TYPES = {"Direct", "Reject", "RejectDrop", "Compatible", "Pass", "Dns"}
SUB_UA = "clash.meta"
# 机场常在节点列表里塞「剩余流量」「到期时间」之类的假节点，自动选最快时排除掉
INFO_NODES = "剩余|到期|过期|官网|重置|套餐|流量|Expire|Traffic|Website"

app = Flask(__name__, static_folder="static", static_url_path="")


# ---------------------------------------------------------------- mihomo 管道 API

def find_pipe():
    names = [n for n in os.listdir("\\\\.\\pipe\\") if n.startswith("verge-mihomo")]
    if not names:
        raise RuntimeError("找不到 mihomo 控制管道，Clash Verge 是否在运行？")
    return "\\\\.\\pipe\\" + names[0]


def read_secret():
    try:
        with open(RUNTIME_YAML, encoding="utf-8") as f:
            for line in f:
                if line.startswith("secret:"):
                    return line.split(":", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    return ""


def _dechunk(body):
    out = b""
    while body:
        size_line, _, rest = body.partition(b"\r\n")
        size = int(size_line.split(b";")[0] or b"0", 16)
        if size == 0:
            break
        out += rest[:size]
        body = rest[size + 2:]
    return out


def _complete(raw):
    """响应是否已读完（mihomo 有时不主动关管道，不能只靠 EOF）。"""
    hdr, sep, body = raw.partition(b"\r\n\r\n")
    if not sep:
        return False
    hdr = hdr.lower()
    if b"transfer-encoding: chunked" in hdr:
        return body.endswith(b"0\r\n\r\n")
    for line in hdr.split(b"\r\n"):
        if line.startswith(b"content-length:"):
            return len(body) >= int(line.split(b":")[1])
    return False


def mihomo(method, path, body=None):
    pipe = find_pipe()
    for _ in range(40):
        try:
            f = open(pipe, "r+b", buffering=0)
            break
        except OSError as e:
            if getattr(e, "winerror", None) == 231:  # 管道忙
                time.sleep(0.05)
                continue
            raise
    else:
        raise RuntimeError("mihomo 管道一直忙")
    with f:
        head = f"{method} {path} HTTP/1.1\r\nHost: mihomo\r\nConnection: close\r\n"
        secret = read_secret()
        if secret:
            head += f"Authorization: Bearer {secret}\r\n"
        data = b""
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            head += f"Content-Type: application/json\r\nContent-Length: {len(data)}\r\n"
        f.write(head.encode("utf-8") + b"\r\n" + data)
        raw = b""
        while True:
            try:
                chunk = f.read(65536)
            except OSError:  # 对端关闭管道
                break
            if not chunk:
                break
            raw += chunk
            if _complete(raw):
                break
    hdr, _, payload = raw.partition(b"\r\n\r\n")
    status = int(hdr.split(b" ", 2)[1])
    if b"transfer-encoding: chunked" in hdr.lower():
        payload = _dechunk(payload)
    text = payload.decode("utf-8", "replace")
    try:
        parsed = json.loads(text) if text.strip() else None
    except ValueError:
        parsed = text
    if status >= 400:
        msg = parsed.get("message") if isinstance(parsed, dict) else text
        raise RuntimeError(f"mihomo 返回 {status}: {msg}")
    return parsed


def q(name):
    return urllib.parse.quote(name, safe="")


# ---------------------------------------------------------------- 规则 → 配置

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"settings": {"lan_direct": True}, "rules": []}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)


def validate_state(state):
    seen = set()
    for r in state.get("rules", []):
        name = (r.get("name") or "").strip()
        if not name:
            raise ValueError("有规则没填名称")
        if any(c in name for c in ",()"):
            raise ValueError(f"规则名「{name}」不能包含逗号或括号")
        if name in seen:
            raise ValueError(f"规则名「{name}」重复了")
        seen.add(name)
        if not r.get("matchers"):
            raise ValueError(f"规则「{name}」至少要有一个匹配条件")
        for m in r["matchers"]:
            if not (m.get("value") or "").strip():
                raise ValueError(f"规则「{name}」有空的匹配条件")
            if "," in m["value"]:
                raise ValueError(f"规则「{name}」的匹配值不能包含逗号")
        t = r.get("target") or {}
        if t.get("kind") in ("node", "group") and not t.get("name"):
            raise ValueError(f"规则「{name}」还没选节点")
        if t.get("kind") == "sub":
            sub = t.get("sub") or {}
            if not (sub.get("name") or "").strip() or not (sub.get("url") or "").startswith("http"):
                raise ValueError(f"规则「{name}」的订阅名称或链接不对")
            if any(c in sub["name"] for c in ",()"):
                raise ValueError(f"订阅名「{sub['name']}」不能包含逗号或括号")
            if t.get("pick") == "node" and not t.get("name"):
                raise ValueError(f"规则「{name}」还没选订阅里的节点")
            if (t.get("test_url") or "").strip() and not t["test_url"].strip().startswith("http"):
                raise ValueError(f"规则「{name}」的测速地址要以 http:// 或 https:// 开头")
    for n in state.get("self_nodes", []):
        if not str(n.get("name", "")).startswith(SELF_PREFIX) or not n.get("type") or not n.get("server"):
            raise ValueError(f"自建节点「{n.get('name')}」要有 name(以「{SELF_PREFIX}」开头)、type、server")
    urls = {}
    for r in state.get("rules", []):
        t = r.get("target") or {}
        if t.get("kind") == "sub":
            sname = t["sub"]["name"].strip()
            if urls.setdefault(sname, t["sub"]["url"]) != t["sub"]["url"]:
                raise ValueError(f"有两个不同的订阅链接都叫「{sname}」，请改个名字")


def provider_name(sub):
    return PREFIX + sub["name"].strip()


def provider_conf(sub):
    h = hashlib.sha1(sub["url"].encode("utf-8")).hexdigest()[:12]
    return {"type": "http", "url": sub["url"], "path": f"./proxy_providers/router-{h}.yaml",
            "interval": 86400, "header": {"User-Agent": [SUB_UA]},
            "health-check": {"enable": False}}


def build_plan(state):
    """生成与具体订阅无关的计划：每项 = 一个代理组 + 指向它的规则。"""
    entries = []
    if state.get("self_nodes"):
        entries.append({"proxies": state["self_nodes"], "rules": [], "rule_id": None})
    if state.get("settings", {}).get("lan_direct", True):
        entries.append({"group": {"name": LAN_GROUP, "type": "select", "proxies": ["DIRECT"]},
                        "rules": [f"IP-CIDR{'6' if ':' in c else ''},{c},{LAN_GROUP},no-resolve"
                                  for c in LAN_CIDRS],
                        "rule_id": None})
    user = [r for r in state.get("rules", []) if r.get("enabled", True)]
    if any(r.get("cn_direct") for r in user):
        entries.append({"group": {"name": CN_GROUP, "type": "select", "proxies": ["DIRECT"]},
                        "rules": [], "rule_id": None})
    for r in user:
        t = r["target"]
        gname = PREFIX + r["name"].strip()
        providers = {}
        if t["kind"] == "sub":
            pname = provider_name(t["sub"])
            providers[pname] = provider_conf(t["sub"])
            if t.get("pick") == "node":
                group = {"name": gname, "type": "select", "use": [pname],
                         "filter": "^" + re.escape(t["name"]) + "$"}
            else:
                group = {"name": gname, "type": "url-test", "use": [pname],
                         "url": (t.get("test_url") or "").strip() or TEST_URL,
                         "interval": 300, "tolerance": 50, "lazy": False,
                         "exclude-filter": INFO_NODES}
                if (t.get("filter") or "").strip():
                    group["filter"] = t["filter"].strip()
        elif t["kind"] == "direct":
            members = ["DIRECT"]
        elif t["kind"] == "reject":
            members = ["REJECT"]
        elif r.get("mode") == "fallback":
            members = [t["name"]] + [b for b in r.get("backups", []) if b != t["name"]]
        else:
            members = [t["name"]]
        if t["kind"] != "sub":
            group = {"name": gname, "type": "select", "proxies": members}
            if len(members) > 1:
                group.update(type="fallback", url=TEST_URL, interval=180, lazy=False)
        rules = []
        for m in r["matchers"]:
            base = f"{m['type']},{m['value'].strip()}"
            if r.get("cn_direct") and m["type"].startswith("PROCESS"):
                rules.append(f"AND,(({base}),(GEOSITE,cn)),{CN_GROUP}")
                rules.append(f"AND,(({base}),(GEOIP,CN)),{CN_GROUP}")
            rules.append(f"{base},{gname}")
        entries.append({"group": group, "rules": rules, "rule_id": r.get("id"), "providers": providers})
    return entries


def strip_managed(config):
    config["proxy-groups"] = [g for g in config.get("proxy-groups") or []
                              if not str(g.get("name", "")).startswith(PREFIX)]
    config["rules"] = [r for r in config.get("rules") or [] if "," + PREFIX not in r]
    config["proxies"] = [p for p in config.get("proxies") or []
                         if not str(p.get("name", "")).startswith(SELF_PREFIX)]
    provs = {k: v for k, v in (config.get("proxy-providers") or {}).items() if not k.startswith(PREFIX)}
    if provs:
        config["proxy-providers"] = provs
    else:
        config.pop("proxy-providers", None)
    config.pop("find-process-mode", None)
    return config


def apply_plan(config, entries):
    """与 Script.js 里的 JS 逻辑一致：成员节点不存在就剔除，全部不存在则该规则不生效。"""
    for e in entries:
        if e.get("proxies"):
            config["proxies"] = copy.deepcopy(e["proxies"]) + (config.get("proxies") or [])
    names = set(BUILTIN)
    names.update(p["name"] for p in config.get("proxies") or [])
    names.update(g["name"] for g in config.get("proxy-groups") or [])
    has_providers = bool(config.get("proxy-providers"))
    groups, rules, report, providers = [], [], {}, {}
    for e in entries:
        if not e.get("group"):
            continue
        g = copy.deepcopy(e["group"])
        if "use" in g:  # 其他订阅：节点由提供者下载，这里没法预先检查
            providers.update(e.get("providers") or {})
            if e["rule_id"]:
                report[e["rule_id"]] = {"active": True, "missing": []}
        else:
            members = [n for n in g["proxies"] if has_providers or n in names]
            missing = [n for n in g["proxies"] if n not in members]
            if e["rule_id"]:
                report[e["rule_id"]] = {"active": bool(members), "missing": missing}
            if not members:
                continue
            g["proxies"] = members
            if len(members) < 2 and g["type"] == "fallback":
                g = {"name": g["name"], "type": "select", "proxies": members}
        groups.append(g)
        rules.extend(e["rules"])
    if providers:
        config["proxy-providers"] = {**(config.get("proxy-providers") or {}), **providers}
    if groups:
        config["find-process-mode"] = "always"
        config["proxy-groups"] = (config.get("proxy-groups") or []) + groups
        config["rules"] = rules + (config.get("rules") or [])
    return config, report


SCRIPT_TEMPLATE = r"""// ============================================================
// 由「分流管家」(proxy-router) 自动生成，请勿手动修改
// 在网页 http://127.0.0.1:9123 里编辑规则，保存后会覆盖本文件
// ============================================================
var PLAN = __PLAN__;

function main(config, profileName) {
  PLAN.forEach(function (e) {
    if (e.proxies) config.proxies = JSON.parse(JSON.stringify(e.proxies)).concat(config.proxies || []);
  });
  var names = { DIRECT: 1, REJECT: 1 };
  var providers = config["proxy-providers"];
  var hasProviders = providers && Object.keys(providers).length > 0;
  (config.proxies || []).forEach(function (p) { names[p.name] = 1; });
  (config["proxy-groups"] || []).forEach(function (g) { names[g.name] = 1; });
  var groups = [], rules = [], subs = {};
  PLAN.forEach(function (e) {
    if (!e.group) return;
    var g = JSON.parse(JSON.stringify(e.group));
    if (g.use) {
      Object.keys(e.providers || {}).forEach(function (k) { subs[k] = e.providers[k]; });
    } else {
      var members = g.proxies.filter(function (n) { return hasProviders || names[n]; });
      if (members.length === 0) return;
      g.proxies = members;
      if (members.length < 2 && g.type === "fallback") {
        g = { name: g.name, type: "select", proxies: members };
      }
    }
    groups.push(g);
    rules = rules.concat(e.rules);
  });
  if (groups.length === 0) return config;  // 自建节点已在上面注入
  if (Object.keys(subs).length > 0) {
    config["proxy-providers"] = config["proxy-providers"] || {};
    Object.keys(subs).forEach(function (k) { config["proxy-providers"][k] = subs[k]; });
  }
  config["find-process-mode"] = "always";
  config["proxy-groups"] = (config["proxy-groups"] || []).concat(groups);
  config.rules = rules.concat(config.rules || []);
  return config;
}
"""


def write_script(entries):
    backup = SCRIPT_JS + ".before-proxy-router"
    if os.path.exists(SCRIPT_JS) and not os.path.exists(backup):
        shutil.copy2(SCRIPT_JS, backup)
    plan = [{"group": e.get("group"), "rules": e["rules"], "providers": e.get("providers") or {},
             **({"proxies": e["proxies"]} if e.get("proxies") else {})}
            for e in entries]
    content = SCRIPT_TEMPLATE.replace("__PLAN__", json.dumps(plan, ensure_ascii=False, indent=2))
    with open(SCRIPT_JS, "w", encoding="utf-8") as f:
        f.write(content)


def find_mihomo():
    cands = [r"C:\Program Files\Clash Verge\verge-mihomo.exe"]
    cands += glob.glob(r"C:\ProgramData\clash-verge-service\cores\verge-mihomo.exe")
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def mihomo_test(config):
    exe = find_mihomo()
    if not exe:
        return
    path = os.path.join(BASE, "_test_config.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
    r = subprocess.run([exe, "-t", "-d", VERGE_DIR, "-f", path], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=60,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    os.remove(path)
    if r.returncode != 0:
        lines = [l for l in (r.stdout + r.stderr).splitlines() if "level=error" in l or "fatal" in l.lower()]
        raise RuntimeError("配置校验失败：" + ("\n".join(lines[-5:]) or (r.stdout + r.stderr)[-800:]))


def current_report(state):
    with open(RUNTIME_YAML, encoding="utf-8") as f:
        config = strip_managed(yaml.safe_load(f))
    return apply_plan(config, build_plan(state))[1]


# ---------------------------------------------------------------- 路由

@app.get("/")
def index():
    return send_from_directory(BASE + "/static", "index.html")


@app.get("/api/state")
def get_state():
    state = load_state()
    try:
        report = current_report(state)
    except Exception:
        report = {}
    return jsonify(state=state, report=report)


@app.post("/api/apply")
def api_apply():
    state = request.get_json()
    try:
        validate_state(state)
        with open(RUNTIME_YAML, encoding="utf-8") as f:
            config = strip_managed(yaml.safe_load(f))
        entries = build_plan(state)
        config, report = apply_plan(config, entries)
        mihomo_test(config)
        save_state(state)
        write_script(entries)
        payload = yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
        with open(RUNTIME_YAML, "w", encoding="utf-8") as f:
            f.write(payload)
        mihomo("PUT", "/configs?force=true", {"path": "", "payload": payload})
        return jsonify(ok=True, report=report)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.get("/api/status")
def api_status():
    try:
        ver = mihomo("GET", "/version")
        cfg = mihomo("GET", "/configs")
    except Exception as e:
        return jsonify(ok=False, error=str(e))
    profile = ""
    try:
        with open(os.path.join(VERGE_DIR, "profiles.yaml"), encoding="utf-8") as f:
            prof = yaml.safe_load(f)
        cur = prof.get("current")
        profile = next((i.get("name") for i in prof.get("items", []) if i.get("uid") == cur), "") or ""
    except Exception:
        pass
    return jsonify(ok=True, version=ver.get("version"), mode=cfg.get("mode"),
                   tun=(cfg.get("tun") or {}).get("enable"), profile=profile)


@app.post("/api/mode")
def api_mode():
    mihomo("PATCH", "/configs", {"mode": request.get_json()["mode"]})
    return jsonify(ok=True)


@app.get("/api/proxies")
def api_proxies():
    data = mihomo("GET", "/proxies")["proxies"]
    nodes, groups, managed = [], [], {}
    for name, p in data.items():
        hist = p.get("history") or []
        delay = hist[-1]["delay"] if hist else None
        if name.startswith(PREFIX) and p["type"] in GROUP_TYPES:
            managed[name] = p.get("now")
        if name == "GLOBAL" or name.startswith(PREFIX):
            continue
        if p["type"] in GROUP_TYPES:
            groups.append({"name": name, "type": p["type"], "now": p.get("now"), "all": p.get("all", [])})
        elif p["type"] not in SKIP_TYPES:
            nodes.append({"name": name, "type": p["type"], "delay": delay})
    # 按订阅里的原始顺序
    order = {n: i for i, n in enumerate(data.get("GLOBAL", {}).get("all", []))}
    nodes.sort(key=lambda n: order.get(n["name"], 1e9))
    groups.sort(key=lambda g: order.get(g["name"], 1e9))
    # 其他订阅（🎯 提供者）里各节点的最近延迟，用来在规则卡片上显示「当前用的节点 xx ms」
    sub_delay = {}
    try:
        for pname, pv in mihomo("GET", "/providers/proxies")["providers"].items():
            if pname.startswith(PREFIX):
                for n in pv.get("proxies") or []:
                    hist = n.get("history") or []
                    sub_delay[n["name"]] = hist[-1]["delay"] if hist else None
    except Exception:
        pass
    return jsonify(nodes=nodes, groups=groups, managed=managed, sub_delay=sub_delay)


@app.get("/api/delay")
def api_delay():
    name = request.args["name"]
    try:
        r = mihomo("GET", f"/proxies/{q(name)}/delay?timeout=5000&url={q(TEST_URL)}")
        return jsonify(delay=r.get("delay"))
    except Exception:
        return jsonify(delay=0)


def verge_subs():
    """Clash Verge 里已添加的远程订阅。"""
    try:
        with open(PROFILES_YAML, encoding="utf-8") as f:
            prof = yaml.safe_load(f) or {}
    except OSError:
        return []
    cur = prof.get("current")
    return [{"name": i.get("name") or i.get("uid"), "url": i["url"], "file": i.get("file"),
             "current": i.get("uid") == cur}
            for i in prof.get("items") or [] if i.get("type") == "remote" and i.get("url")]


def _names_from_yaml(text):
    data = yaml.safe_load(text) or {}
    return [p["name"] for p in data.get("proxies") or [] if isinstance(p, dict) and p.get("name")]


@app.get("/api/subs")
def api_subs():
    return jsonify(subs=[{k: v for k, v in s.items() if k != "file"} for s in verge_subs()])


@app.post("/api/subnodes")
def api_subnodes():
    """某个订阅里的节点：已接入的从 mihomo 读（带延迟），否则读 Verge 下载好的文件，再不行就现下载。"""
    sub = request.get_json()
    pname = provider_name(sub)
    try:
        p = mihomo("GET", f"/providers/proxies/{q(pname)}")
        if p.get("vehicleType") == "HTTP" and p.get("proxies"):
            nodes = []
            for n in p["proxies"]:
                hist = n.get("history") or []
                nodes.append({"name": n["name"], "delay": hist[-1]["delay"] if hist else None})
            return jsonify(ok=True, nodes=nodes, loaded=True)
    except Exception:
        pass
    try:
        names = []
        for s in verge_subs():
            if s["url"] == sub["url"] and s.get("file"):
                path = os.path.join(VERGE_DIR, "profiles", s["file"])
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        names = _names_from_yaml(f.read())
        if not names:
            req = urllib.request.Request(sub["url"], headers={"User-Agent": SUB_UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                names = _names_from_yaml(r.read().decode("utf-8", "replace"))
        if not names:
            raise RuntimeError("订阅里没读到节点（链接不是 Clash 格式？）")
        return jsonify(ok=True, nodes=[{"name": n, "delay": None} for n in names], loaded=False)
    except Exception as e:
        return jsonify(ok=False, error=f"读取订阅失败：{e}"), 400


@app.post("/api/subdelay")
def api_subdelay():
    b = request.get_json()
    try:
        r = mihomo("GET", f"/providers/proxies/{q(provider_name(b['sub']))}/{q(b['name'])}"
                          f"/healthcheck?timeout=5000&url={q(TEST_URL)}")
        return jsonify(delay=r.get("delay"))
    except Exception:
        return jsonify(delay=0)


@app.get("/api/connections")
def api_connections():
    conns = mihomo("GET", "/connections").get("connections") or []
    apps = {}
    for c in conns:
        md = c.get("metadata", {})
        proc = md.get("process") or "(未识别进程)"
        a = apps.setdefault(proc, {"process": proc, "paths": set(), "count": 0, "up": 0, "down": 0,
                                   "routes": {}, "hosts": {}})
        if md.get("processPath"):
            a["paths"].add(md["processPath"])
        a["count"] += 1
        a["up"] += c.get("upload", 0)
        a["down"] += c.get("download", 0)
        chain = c.get("chains") or []
        route = " → ".join(reversed(chain)) if chain else "?"
        rule = c.get("rule", "") + ((" " + c["rulePayload"]) if c.get("rulePayload") else "")
        key = route + "\u0000" + rule
        a["routes"][key] = a["routes"].get(key, 0) + 1
        host = md.get("host") or md.get("destinationIP") or ""
        a["hosts"][host] = a["hosts"].get(host, 0) + 1
    out = []
    for a in apps.values():
        out.append({
            "process": a["process"], "paths": sorted(a["paths"]), "count": a["count"],
            "up": a["up"], "down": a["down"],
            "routes": [{"route": k.split("\u0000")[0], "rule": k.split("\u0000")[1], "count": v}
                       for k, v in sorted(a["routes"].items(), key=lambda kv: -kv[1])],
            "hosts": [h for h, _ in sorted(a["hosts"].items(), key=lambda kv: -kv[1])[:6]],
        })
    out.sort(key=lambda a: -a["count"])
    return jsonify(apps=out)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9123, threaded=True)
