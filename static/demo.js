// 演示模式：在 GitHub Pages 上或网址带 ?demo 时启用，用假数据模拟后端，不需要安装任何东西
(function () {
  const q = new URLSearchParams(location.search);
  if (!(location.hostname.endsWith('github.io') || q.has('demo'))) return;

  const nodes = [
    ['香港 01', 38], ['香港 02', 45], ['日本 01', 72], ['日本 02', 81],
    ['新加坡 01', 96], ['台湾 01', 64], ['美国 洛杉矶 01', 158], ['美国 洛杉矶 02', 171],
    ['美国 住宅IP', 203], ['英国 01', 231], ['德国 01', 0], ['韩国 01', 88],
  ].map(([name, delay]) => ({name, type: 'Hysteria2', delay}));
  const groups = [
    {name: '节点选择', type: 'Selector', now: '日本 01'},
    {name: '自动选择', type: 'URLTest', now: '香港 01'},
    {name: 'ChatGPT', type: 'Selector', now: '美国 洛杉矶 01'},
    {name: 'Telegram', type: 'Selector', now: '新加坡 01'},
    {name: 'YouTube', type: 'Selector', now: '香港 02'},
  ];
  const P = v => ({type: 'PROCESS-NAME', value: v});
  const D = v => ({type: 'DOMAIN-SUFFIX', value: v});
  let state = {
    settings: {lan_direct: true},
    rules: [
      {id: 'r1', name: 'Claude 网页和 API', enabled: true, matchers: [D('claude.ai'), D('claude.com'), D('anthropic.com')],
        target: {kind: 'node', name: '美国 住宅IP'}, mode: 'strict', backups: [], cn_direct: false},
      {id: 'r2', name: 'Claude', enabled: true, matchers: [P('claude.exe')],
        target: {kind: 'node', name: '美国 住宅IP'}, mode: 'strict', backups: [], cn_direct: false},
      {id: 'r3', name: 'Chrome', enabled: true, matchers: [P('chrome.exe')],
        target: {kind: 'node', name: '日本 01'}, mode: 'fallback', backups: ['日本 02', '香港 01'], cn_direct: true},
      {id: 'r4', name: 'Git 和 npm', enabled: true, matchers: [P('git.exe'), P('git-remote-https.exe'), P('node.exe')],
        target: {kind: 'node', name: '香港 01'}, mode: 'fallback', backups: ['香港 02'], cn_direct: true},
      {id: 'r5', name: 'Telegram', enabled: true, matchers: [P('Telegram.exe'), {type: 'GEOSITE', value: 'telegram'}],
        target: {kind: 'group', name: 'Telegram'}, mode: 'strict', backups: [], cn_direct: false},
      {id: 'r6', name: '微信', enabled: true, matchers: [P('WeChat.exe')],
        target: {kind: 'direct', name: ''}, mode: 'strict', backups: [], cn_direct: false},
      {id: 'r7', name: '游戏反作弊', enabled: false, matchers: [P('ACE-Tray.exe')],
        target: {kind: 'reject', name: ''}, mode: 'strict', backups: [], cn_direct: false},
    ],
  };
  const report = () => Object.fromEntries(state.rules.map(r => [r.id, {active: true, missing: []}]));
  const r = (route, rule, count) => ({route, rule, count});
  const conns = [
    {process: 'chrome.exe', paths: ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'], count: 23, up: 1.2e6, down: 48e6,
      routes: [r('🎯 Chrome → 日本 01', 'ProcessName chrome.exe', 17), r('🎯 国内直连 → DIRECT', 'AND chrome.exe + GeoSite cn', 6)],
      hosts: ['www.youtube.com', 'www.bilibili.com', 'github.com', 'www.google.com', 'i.ytimg.com']},
    {process: 'claude.exe', paths: ['C:\\Program Files\\WindowsApps\\Claude_x64\\app\\claude.exe'], count: 6, up: 3.1e5, down: 2.4e6,
      routes: [r('🎯 Claude → 美国 住宅IP', 'ProcessName claude.exe', 6)], hosts: ['claude.ai', 'api.anthropic.com']},
    {process: 'Telegram.exe', paths: ['D:\\Telegram Desktop\\Telegram.exe'], count: 4, up: 9e4, down: 7.7e5,
      routes: [r('🎯 Telegram → Telegram → 新加坡 01', 'ProcessName Telegram.exe', 4)], hosts: ['149.154.167.51']},
    {process: 'Code.exe', paths: ['C:\\Users\\me\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe'], count: 3, up: 4e4, down: 3e5,
      routes: [r('节点选择 → 日本 01', 'Match', 3)], hosts: ['marketplace.visualstudio.com', 'update.code.visualstudio.com']},
    {process: 'WeChat.exe', paths: ['C:\\Program Files\\Tencent\\WeChat\\WeChat.exe'], count: 5, up: 2e4, down: 1.1e5,
      routes: [r('🎯 微信 → DIRECT', 'ProcessName WeChat.exe', 5)], hosts: ['long.weixin.qq.com', 'szshort.weixin.qq.com']},
  ];
  const clone = x => JSON.parse(JSON.stringify(x));
  const wait = ms => new Promise(res => setTimeout(res, ms));

  window.DEMO_API = async function (path, opt = {}) {
    await wait(120);
    if (path === '/api/state') return {state: clone(state), report: report()};
    if (path === '/api/status') return {ok: true, version: 'v1.19 (演示模式)', mode: 'rule', tun: true, profile: '示例订阅'};
    if (path === '/api/proxies') return {nodes: clone(nodes), groups: clone(groups)};
    if (path === '/api/connections') return {apps: clone(conns)};
    if (path.startsWith('/api/delay')) {
      await wait(300 + Math.random() * 500);
      return {delay: Math.random() < 0.1 ? 0 : Math.round(30 + Math.random() * 250)};
    }
    if (path === '/api/mode') return {ok: true};
    if (path === '/api/apply') {
      await wait(500);
      state = JSON.parse(opt.body);
      return {ok: true, report: report()};
    }
    throw new Error('演示模式不支持：' + path);
  };
  document.addEventListener('DOMContentLoaded', () => {
    const bar = document.createElement('div');
    bar.style.cssText = 'background:#2f6fed;color:#fff;text-align:center;padding:6px 12px;font-size:13px';
    bar.innerHTML = '这是演示模式，数据都是假的，点“保存”也不会真的修改任何配置。' +
      '<a style="color:#fff;font-weight:600;margin-left:8px" href="https://github.com/RickLisfdsdf/proxy-router">去 GitHub 下载 →</a>';
    document.body.prepend(bar);
  });
})();
