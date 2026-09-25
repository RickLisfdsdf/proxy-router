# 🎯 分流管家 (proxy-router)

本地网页，用来管理 **Clash Verge Rev（mihomo 内核）** 的分流：指定某个软件或某个服务走哪个节点。

- 按**软件**分流（进程名 / 进程路径正则），比如 Chrome 走节点 A，Claude 走节点 B
- 按**服务**分流（域名、geosite 分类、IP 段、端口）
- **锁定**：只能走指定节点，节点挂了就断网，不会漏到别的节点
- **优先**：主节点不可用时自动切换到备用节点（fallback）
- 软件规则可选“国内网站直连”
- 实时查看每个软件正在走的节点和命中的规则，一键给它建规则
- 节点测速

## 工作原理

1. 规则保存在 `rules.json`
2. 生成 Clash Verge 的全局扩展脚本 `profiles/Script.js`，以后更新订阅、重启 Verge 规则依然有效（首次会备份原脚本为 `Script.js.before-proxy-router`）
3. 同时把规则插入当前运行配置，用 `verge-mihomo.exe -t` 校验后，通过 mihomo 的命名管道控制接口热加载，立即生效

自动生成的代理组都以 `🎯 ` 开头。节点在当前订阅中不存在的规则会自动跳过，不会让配置报错。

## 使用

需要 Windows + Clash Verge Rev + Python 3.10+：

```
pip install flask pyyaml
python app.py
```

打开 http://127.0.0.1:9123 。也可以双击 `启动分流管家.vbs` 在后台启动。

建议在 Clash Verge 里开启 **TUN 模式**、使用**规则模式**，否则不读系统代理的命令行程序不会被接管。

> 启用后请不要在 Clash Verge 里手动编辑全局扩展脚本，下次保存时会被覆盖。
