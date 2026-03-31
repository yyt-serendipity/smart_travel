from __future__ import annotations

import argparse
import os
import secrets
import string
from pathlib import Path

import paramiko


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def sql_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def random_alnum(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def run(ssh: paramiko.SSHClient, label: str, command: str, timeout: int = 1800) -> str:
    print(f"==> {label}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="ignore")
    error = stderr.read().decode("utf-8", errors="ignore")
    combined = (output + error).strip()
    if combined:
        print(combined[-4000:])
    print(f"EXIT={exit_code}")
    if exit_code != 0:
        raise RuntimeError(f"{label} failed with exit code {exit_code}")
    return combined


def write_remote_file(sftp: paramiko.SFTPClient, path: str, content: str) -> None:
    with sftp.file(path, "w") as remote_file:
        remote_file.write(content)


def build_remote_env(local_env: dict[str, str], host: str, db_name: str, db_user: str, db_password: str) -> str:
    # Generate production-only secrets here while forwarding third-party integration keys from local .env.
    lines = [
        f"SECRET_KEY={secrets.token_urlsafe(50)}",
        "DEBUG=False",
        f"ALLOWED_HOSTS={host},127.0.0.1,localhost",
        f"CSRF_TRUSTED_ORIGINS=http://{host}",
        "CORS_ALLOW_ALL_ORIGINS=False",
        f"CORS_ALLOWED_ORIGINS=http://{host}",
        f"DB_NAME={db_name}",
        f"DB_USER={db_user}",
        f"DB_PASSWORD={db_password}",
        "DB_HOST=127.0.0.1",
        "DB_PORT=3306",
    ]
    passthrough_keys = [
        "OSS_ACCESS_KEY_ID",
        "OSS_ACCESS_KEY_SECRET",
        "OSS_BUCKET_NAME",
        "OSS_REGION",
        "OSS_ENDPOINT",
        "OSS_MEDIA_PREFIX",
        "OSS_SIGN_URL_EXPIRE_SECONDS",
        "LLM_PROVIDER",
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_MODEL",
        "DASHSCOPE_BASE_URL",
        "LLM_API_TIMEOUT",
        "AMAP_API_KEY",
        "AMAP_BASE_URL",
        "AMAP_REQUEST_TIMEOUT",
    ]
    for key in passthrough_keys:
        value = local_env.get(key)
        if value:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def build_service_content(app_user: str, app_root: str) -> str:
    return f"""[Unit]
Description=Smart Travel Gunicorn
After=network.target mysql.service
Requires=mysql.service

[Service]
User={app_user}
Group={app_user}
WorkingDirectory={app_root}/backend
ExecStart={app_root}/backend/.venv/bin/gunicorn smart_travel.wsgi:application --workers 2 --bind 127.0.0.1:8000 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def build_nginx_content(host: str, app_root: str) -> str:
    return f"""server {{
    listen 80;
    listen [::]:80;
    server_name {host} _;

    root {app_root}/frontend/dist;
    index index.html;
    client_max_body_size 20M;

    location /static/ {{
        alias {app_root}/backend/staticfiles/;
    }}

    location /api/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }}

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""


def deploy(args: argparse.Namespace) -> None:
    ssh_password = os.environ.get(args.password_env)
    if not ssh_password:
        raise RuntimeError(f"Missing SSH password env var: {args.password_env}")

    local_env = load_env(args.local_env)
    db_password = random_alnum(24)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=args.host, username=args.username, password=ssh_password, timeout=20)
    sftp = ssh.open_sftp()
    try:
        print("==> Upload app archive")
        sftp.put(str(args.archive), args.remote_archive)
        print("==> Upload database dump")
        sftp.put(str(args.dump), args.remote_dump)

        # Replace the remote release in a fixed order: OS packages -> code -> venv -> DB -> config -> services.
        run(ssh, "Install base packages", "export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -y nginx mysql-server python3-venv python3-pip && systemctl enable --now mysql nginx", timeout=2400)
        run(ssh, "Create app user", f"id -u {args.app_user} >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash {args.app_user}")
        run(ssh, "Prepare app directory", f"if [ -d {args.app_root} ] && [ \"$(ls -A {args.app_root} 2>/dev/null)\" ]; then mv {args.app_root} {args.app_root}_backup_$(date +%Y%m%d%H%M%S); fi && mkdir -p {args.app_root}")
        run(ssh, "Extract app archive", f"tar -xzf {args.remote_archive} -C {args.app_root}")
        run(ssh, "Create virtualenv", f"python3 -m venv {args.app_root}/backend/.venv")
        run(ssh, "Install Python dependencies", f"{args.app_root}/backend/.venv/bin/pip install --upgrade pip && {args.app_root}/backend/.venv/bin/pip install -r {args.app_root}/backend/requirements.txt", timeout=2400)

        db_exists = run(ssh, "Check existing database", f"mysql -Nse \"SHOW DATABASES LIKE '{args.db_name}';\" || true")
        if args.db_name in db_exists:
            # Keep a one-off server backup before replacing the remote database from the local dump.
            run(ssh, "Backup existing remote database", f"mysqldump --single-transaction {args.db_name} > /root/{args.db_name}_predeploy_$(date +%Y%m%d%H%M%S).sql", timeout=2400)

        sql = f"""
DROP DATABASE IF EXISTS `{args.db_name}`;
CREATE DATABASE `{args.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '{args.db_user}'@'127.0.0.1' IDENTIFIED BY '{sql_quote(db_password)}';
CREATE USER IF NOT EXISTS '{args.db_user}'@'localhost' IDENTIFIED BY '{sql_quote(db_password)}';
ALTER USER '{args.db_user}'@'127.0.0.1' IDENTIFIED BY '{sql_quote(db_password)}';
ALTER USER '{args.db_user}'@'localhost' IDENTIFIED BY '{sql_quote(db_password)}';
GRANT ALL PRIVILEGES ON `{args.db_name}`.* TO '{args.db_user}'@'127.0.0.1';
GRANT ALL PRIVILEGES ON `{args.db_name}`.* TO '{args.db_user}'@'localhost';
FLUSH PRIVILEGES;
""".strip()
        run(ssh, "Create database and app user", f"cat <<'SQL' | mysql\n{sql}\nSQL")
        run(ssh, "Import database dump", f"mysql --binary-mode=1 {args.db_name} < {args.remote_dump}", timeout=2400)

        remote_env_content = build_remote_env(local_env, args.host, args.db_name, args.db_user, db_password)
        write_remote_file(sftp, f"{args.app_root}/backend/.env", remote_env_content)
        write_remote_file(sftp, "/etc/systemd/system/smart_travel.service", build_service_content(args.app_user, args.app_root))
        write_remote_file(sftp, "/etc/nginx/sites-available/smart_travel", build_nginx_content(args.host, args.app_root))

        run(
            ssh,
            "Set file permissions",
            f"chown -R {args.app_user}:{args.app_user} {args.app_root} && chmod -R u=rwX,go=rX {args.app_root} && chmod 600 {args.app_root}/backend/.env",
        )
        run(ssh, "Run Django migrations", f"su -s /bin/bash -c 'cd {args.app_root}/backend && ./.venv/bin/python manage.py migrate --noinput' {args.app_user}", timeout=1800)
        run(ssh, "Collect static files", f"su -s /bin/bash -c 'cd {args.app_root}/backend && ./.venv/bin/python manage.py collectstatic --noinput' {args.app_user}", timeout=1800)
        run(ssh, "Run Django system check", f"su -s /bin/bash -c 'cd {args.app_root}/backend && ./.venv/bin/python manage.py check' {args.app_user}", timeout=1800)

        run(ssh, "Enable nginx site", "find /etc/nginx/sites-enabled -maxdepth 1 -type l -name 'default*' -delete && ln -sfn /etc/nginx/sites-available/smart_travel /etc/nginx/sites-enabled/smart_travel")
        run(ssh, "Reload systemd and restart app", "systemctl daemon-reload && systemctl enable smart_travel && systemctl restart smart_travel")
        run(ssh, "Validate nginx config", "nginx -t")
        run(ssh, "Restart nginx", "systemctl restart nginx")
        run(ssh, "Verify services", "systemctl --no-pager --full status smart_travel nginx mysql | tail -n 80")
        run(ssh, "Verify local HTTP endpoints", "curl -I http://127.0.0.1/ && printf '\n' && curl -s http://127.0.0.1/api/overview/ | head -c 400", timeout=180)
    finally:
        sftp.close()
        ssh.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Smart Travel to a remote Ubuntu server.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password-env", default="SMART_TRAVEL_SSH_PASSWORD")
    parser.add_argument("--local-env", type=Path, default=Path("backend/.env"))
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--remote-archive", default="/root/smart_travel_app.tar.gz")
    parser.add_argument("--remote-dump", default="/root/smart_travel.sql")
    parser.add_argument("--app-root", default="/srv/smart_travel")
    parser.add_argument("--app-user", default="smarttravel")
    parser.add_argument("--db-name", default="smart_travel")
    parser.add_argument("--db-user", default="smart_travel")
    return parser.parse_args()


if __name__ == "__main__":
    deploy(parse_args())
