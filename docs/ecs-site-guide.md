# 阿里云 ECS 固定新闻站

本机不需要持续开着。ECS 的 Nginx 提供网页，专门的 systemd 任务负责抓取和分类新闻。

当前目标入口：**[http://47.115.130.110/newsflow/](http://47.115.130.110/newsflow/)**。ThinkFlow 继续使用服务器根路径。

## 使用

打开网址，在“管理新闻源”中勾选想看的来源，再按分类或关键词筛选。收藏、人工纠错与 CSV 导出和免费公网版相同。收藏按当前浏览器与网址保存，不在 GitHub Pages、ECS 和不同设备间自动同步。

服务器在每轮抓取完成后约两分钟再次检查；网页每 20 秒读取已发布数据。“检查更新”刷新已发布数据，不让匿名访客触发服务器任务。来源发布时间和采集完成时间分别显示。部分来源连接失败时其余来源继续更新；可用缓存保留七天，公开列表最多 1,000 条。

这是公网 IP 的固定 HTTP 地址，运行期间与当前 ECS 公网 IP 绑定。停止本机不影响它；释放实例或变更公网 IP 后需更新入口。当前没有已提供的域名与证书，因此未把临时隧道当作固定 HTTPS 地址。若以后使用深圳 ECS 上的独立域名，应准备已备案域名，再配置 DNS 和 HTTPS 证书。

## 服务与维护

- 程序及独立虚拟环境：`/opt/newsflow`、`/opt/newsflow/.venv`。
- 公开网页与新闻 JSON：`/var/lib/newsflow/site`。
- 更新单元：`newsflow-update.service`、`newsflow-update.timer`。
- Nginx location 模板：`deploy/ecs/nginx-newsflow-location.conf`；在现有 port-80 server 块中 include。
- 自动更新使用 `newsflow` 系统用户、本地模型、一个 CPU 上限和 700 MiB 内存上限。

在 ECS 的终端检查：

```bash
systemctl status newsflow-update.timer --no-pager
systemctl list-timers newsflow-update.timer --no-pager
journalctl -u newsflow-update.service -n 30 --no-pager
curl -I http://127.0.0.1/newsflow/
```

立即执行一轮更新：

```bash
sudo systemctl start newsflow-update.service
```

systemd 不会为正在执行的同一个 oneshot 单元启动第二个实例。更新先完成抓取与分类，再原子替换 JSON；失败不会截断 Nginx 当前提供的数据。更新任务不复制 HTML、脚本或样式，也不读取 ThinkFlow 配置和任何个人密钥。

## 在另一台 Ubuntu ECS 安装

复制或克隆公开源码到 `/opt/newsflow`，安装 Python 3.12 的 venv 支持并创建独立环境。按照自己的服务器地址调整入口。以下命令不包含任何密码或密钥：

```bash
sudo useradd --system --user-group --home-dir /var/lib/newsflow --shell /usr/sbin/nologin newsflow
sudo install -d -m 0755 -o newsflow -g newsflow /var/lib/newsflow
cd /opt/newsflow
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
sudo -u newsflow .venv/bin/python scripts/update_ecs_site.py --bootstrap
sudo install -m 0644 deploy/ecs/newsflow-update.service /etc/systemd/system/newsflow-update.service
sudo install -m 0644 deploy/ecs/newsflow-update.timer /etc/systemd/system/newsflow-update.timer
sudo install -d -m 0755 /etc/nginx/snippets
sudo install -m 0644 deploy/ecs/nginx-newsflow-location.conf /etc/nginx/snippets/newsflow.conf
```

先备份现有 Nginx 配置，在承载站点的 server 块中加入 `include /etc/nginx/snippets/newsflow.conf;`。检查成功再 reload：

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl daemon-reload
sudo systemctl enable --now newsflow-update.timer
```

只开放站点需要的 HTTP 端口；Python 更新器没有对公网监听的 API。已有 Nginx 的实例直接复用，不重启其他应用。若服务器已有 `newsflow` 用户，使用现有用户即可。

## 更新代码和恢复

更新源码或模型时，先停 NewsFlow timer，再等待或停止 NewsFlow 自己的更新服务；保留 `/var/lib/newsflow/site/data/news.json`，在独立虚拟环境安装匹配依赖，再运行 `--bootstrap` 安装新版资源。该命令优先使用现有公开快照，因此不会以较旧的发行种子覆盖当前新闻。随后重新启用 timer。

每次修改 Nginx 前备份精确配置，语法检查失败就恢复备份，不 reload。恢复旧代码时需要对应的模型与前端资源；不要修改 ThinkFlow 的账号数据库和配置。公开新闻、模型与来源目录可以分发，登录凭据只保存在部署者自己的机器上。
