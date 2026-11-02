# 阿里云 ECS 固定新闻站

本机不需要持续开着。ECS 的 Nginx 提供网页，专门的 systemd 任务负责抓取和分类新闻。

固定入口：**[https://47.115.130.110/newsflow/](https://47.115.130.110/newsflow/)**。已经实际通过公网访问与 Edge 验收；HTTP 的同一路径也保留。ThinkFlow 继续使用原来的 HTTP 根路径。

## 使用

在 Edge 打开网址，按 `Ctrl+D` 收藏，以后直接从收藏夹进入。在“管理新闻源”中勾选想看的来源，再按分类或关键词筛选；点击标题查看原文入口和分类依据。收藏、人工纠错与 CSV 导出和免费公网版相同。收藏按当前浏览器与网址保存，不在 GitHub Pages、HTTP、HTTPS 和不同设备间自动同步。

服务器在每轮抓取完成后约两分钟再次检查；网页每 20 秒读取已发布数据。“检查更新”刷新已发布数据，不让匿名访客触发服务器任务。来源发布时间和采集完成时间分别显示。部分来源连接失败时其余来源继续更新；可用缓存保留七天，公开列表最多 1,000 条。

入口与当前 ECS 公网 IP 绑定。停止本机不影响它；保持 ECS 运行并保留当前公网 IP，即可持续使用。释放实例或变更公网 IP 后需调整入口和证书。可信 IP 证书不需要购买域名；若以后使用境内 ECS 上的独立域名，按阿里云要求准备备案、DNS 和对应证书。

首次真实更新检查了 43 个频道并新增 389 条新闻，公开列表保持 1,000 条；当时有 15 个来源连接失败，其余来源正常采集。一次完整采集约 236 秒，随后等待约两分钟再检查，因此不能把调度间隔理解为所有新闻恰好两分钟更新。页面显示来源的实际连接状态，失败来源可保留七天内的旧数据。

## 服务与维护

- 程序及独立虚拟环境：`/opt/newsflow`、`/opt/newsflow/.venv`。
- 公开网页与新闻 JSON：`/var/lib/newsflow/site`。
- 更新单元：`newsflow-update.service`、`newsflow-update.timer`。
- 证书单元：`newsflow-cert-renew.service`、`newsflow-cert-renew.timer`，每天两次检查是否需要续期。
- Nginx location 模板：`deploy/ecs/nginx-newsflow-location.conf`；在现有 port-80 server 块中 include。
- HTTPS server 模板：`deploy/ecs/nginx-newsflow-https.conf`；证书客户端在 `/opt/newsflow-acme/.venv`，私有账户与证书在 `/etc/newsflow-acme`，均不属于源码仓库。
- 自动更新使用 `newsflow` 系统用户、本地模型、一个 CPU 上限和 700 MiB 内存上限。

在 ECS 的终端检查：

```bash
systemctl status newsflow-update.timer --no-pager
systemctl list-timers newsflow-update.timer newsflow-cert-renew.timer --no-pager
journalctl -u newsflow-update.service -n 30 --no-pager
curl -I http://127.0.0.1/newsflow/
curl -I https://47.115.130.110/newsflow/
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

在 ECS 安全组允许站点的 TCP 80 与 443 端口；Python 更新器没有对公网监听的 API。已有 Nginx 的实例直接复用，不重启其他应用。若服务器已有 `newsflow` 用户，使用现有用户即可。

## 公网 IP 的 HTTPS

[Let's Encrypt 已于 2026 年 1 月 15 日正式开放短期 IP 证书](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability)。IP 证书必须使用 `shortlived` profile，约六天有效，因此自动续期是部署的一部分。当前使用官方 Certbot 5.9.0，签发与完整续期演练都已成功；普通 TLS 验证通过，没有使用自签名证书或跳过证书验证。

在现有 HTTP server 中保留下面的 ACME 验证路径，80 端口需能从公网访问：

```nginx
location ^~ /.well-known/acme-challenge/ {
    root /var/www/acme;
    default_type "text/plain";
    try_files $uri =404;
}
```

为另一台服务器安装时，把下面的 `47.115.130.110` 和 HTTPS 模板的 `server_name` 改为那台服务器的公网 IP，再执行。账户、私钥只在服务器中产生：

```bash
sudo python3 -m venv /opt/newsflow-acme/.venv
sudo /opt/newsflow-acme/.venv/bin/python -m pip install 'certbot==5.9.0'
sudo install -d -m 0755 /var/www/acme/.well-known/acme-challenge
sudo install -d -m 0700 /etc/newsflow-acme /var/lib/newsflow-acme /var/log/newsflow-acme
sudo /opt/newsflow-acme/.venv/bin/certbot certonly --webroot --webroot-path /var/www/acme \
  --ip-address 47.115.130.110 --required-profile shortlived --cert-name newsflow-ip \
  --non-interactive --agree-tos --register-unsafely-without-email \
  --config-dir /etc/newsflow-acme --work-dir /var/lib/newsflow-acme --logs-dir /var/log/newsflow-acme
sudo install -m 0644 deploy/ecs/nginx-newsflow-https.conf /etc/nginx/sites-available/newsflow-https
sudo ln -s /etc/nginx/sites-available/newsflow-https /etc/nginx/sites-enabled/newsflow-https
sudo nginx -t
sudo systemctl reload nginx
sudo install -m 0755 deploy/ecs/newsflow-reload-nginx /usr/local/sbin/newsflow-reload-nginx
sudo install -m 0644 deploy/ecs/newsflow-cert-renew.service /etc/systemd/system/newsflow-cert-renew.service
sudo install -m 0644 deploy/ecs/newsflow-cert-renew.timer /etc/systemd/system/newsflow-cert-renew.timer
sudo systemctl daemon-reload
sudo systemctl enable --now newsflow-cert-renew.timer
```

在正式签发命令上加 `--dry-run` 可先验证 ACME 挑战；正式部署后再验证续期，包括 Nginx 的平滑 reload：

```bash
sudo /opt/newsflow-acme/.venv/bin/certbot renew --dry-run --run-deploy-hooks \
  --no-random-sleep-on-renew --config-dir /etc/newsflow-acme \
  --work-dir /var/lib/newsflow-acme --logs-dir /var/log/newsflow-acme \
  --deploy-hook /usr/local/sbin/newsflow-reload-nginx
systemctl is-enabled newsflow-update.timer newsflow-cert-renew.timer
```

证书只有成功续期才执行 reload；reload 前先检查 Nginx 语法。它不重启 ThinkFlow。定时器每天 03:00、15:00 按服务器本地时区检查，最多随机延后 30 分钟，漏过的证书任务会补执行。

## 更新代码和恢复

更新源码或模型时，先停 NewsFlow timer，再等待或停止 NewsFlow 自己的更新服务；保留 `/var/lib/newsflow/site/data/news.json`，在独立虚拟环境安装匹配依赖，再运行 `--bootstrap` 安装新版资源。该命令优先使用现有公开快照，因此不会以较旧的发行种子覆盖当前新闻。随后重新启用 timer。

每次修改 Nginx 前备份精确配置，语法检查失败就恢复备份，不 reload。恢复旧代码时需要对应的模型与前端资源；不要修改 ThinkFlow 的账号数据库和配置。公开新闻、模型与来源目录可以分发，登录凭据只保存在部署者自己的机器上。
