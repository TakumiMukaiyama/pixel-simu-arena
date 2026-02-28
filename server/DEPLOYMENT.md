# デプロイメントガイド

Pixel Simulation Arena サーバーのデプロイ手順。

## 前提条件

- Python 3.11+
- PostgreSQL 16+
- Mistral API キー
- uvパッケージマネージャー

## 本番環境セットアップ

### 1. サーバー準備

```bash
# リポジトリクローン
git clone <repository-url>
cd pixel-simu-arena/server

# uvインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係インストール
uv sync --no-dev
```

### 2. PostgreSQLセットアップ

#### Option A: マネージドサービス（推奨）

- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL

#### Option B: セルフホスティング

```bash
# PostgreSQL 16インストール
sudo apt install postgresql-16

# データベース作成
sudo -u postgres createdb pixel_simu_arena
sudo -u postgres createuser -P pixel_user
```

### 3. 環境変数設定

本番用`.env`ファイル作成：

```env
# Mistral API
MISTRAL_API_KEY=<production-key>

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Database（本番URLに置き換え）
DATABASE_URL=postgresql://pixel_user:secure_password@prod-host:5432/pixel_simu_arena

# Game Settings
TICK_MS=200
INITIAL_COST=10.0
MAX_COST=20.0
COST_RECOVERY_PER_TICK=0.6
INITIAL_BASE_HP=100
```

### 4. データベースマイグレーション

```bash
uv run alembic upgrade head
```

### 5. 静的ファイルディレクトリ作成

```bash
mkdir -p static/sprites static/cards static/placeholders
```

## プロセス管理

### systemdサービス（推奨）

`/etc/systemd/system/pixel-simu-arena.service`:

```ini
[Unit]
Description=Pixel Simulation Arena API Server
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/pixel-simu-arena/server
Environment="PATH=/home/www-data/.local/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/pixel-simu-arena/server/.env
ExecStart=/home/www-data/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービス起動：

```bash
sudo systemctl daemon-reload
sudo systemctl enable pixel-simu-arena
sudo systemctl start pixel-simu-arena
sudo systemctl status pixel-simu-arena
```

### Supervisord

`/etc/supervisor/conf.d/pixel-simu-arena.conf`:

```ini
[program:pixel-simu-arena]
command=/home/www-data/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/var/www/pixel-simu-arena/server
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pixel-simu-arena.log
environment=PATH="/home/www-data/.local/bin:%(ENV_PATH)s"
```

## リバースプロキシ（Nginx）

### SSL証明書取得（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.pixel-simu-arena.com
```

### Nginx設定

`/etc/nginx/sites-available/pixel-simu-arena`:

```nginx
upstream pixel_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.pixel-simu-arena.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.pixel-simu-arena.com;

    ssl_certificate /etc/letsencrypt/live/api.pixel-simu-arena.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.pixel-simu-arena.com/privkey.pem;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # タイムアウト設定
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # 静的ファイル
    location /static/ {
        alias /var/www/pixel-simu-arena/server/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # API
    location / {
        proxy_pass http://pixel_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS（本番では適切に設定）
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

有効化：

```bash
sudo ln -s /etc/nginx/sites-available/pixel-simu-arena /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## モニタリング

### ヘルスチェック

```bash
curl https://api.pixel-simu-arena.com/health
```

### ログ監視

```bash
# systemdログ
sudo journalctl -u pixel-simu-arena -f

# Nginxアクセスログ
sudo tail -f /var/log/nginx/access.log

# エラーログ
sudo tail -f /var/log/nginx/error.log
```

### メトリクス（推奨）

- Prometheus + Grafana
- DataDog
- New Relic

## バックアップ

### データベースバックアップ

```bash
# 日次バックアップスクリプト
#!/bin/bash
BACKUP_DIR=/backups/pixel-simu-arena
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -h prod-host -U pixel_user pixel_simu_arena | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 7日以上古いバックアップを削除
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

cronジョブ設定：

```bash
# 毎日午前3時に実行
0 3 * * * /usr/local/bin/backup-pixel-db.sh
```

### 静的ファイルバックアップ

```bash
# S3やGCSにアップロード
aws s3 sync /var/www/pixel-simu-arena/server/static/ s3://pixel-simu-backups/static/
```

## スケーリング

### 水平スケーリング

1. **ロードバランサー**: AWS ALB、Google Cloud Load Balancing
2. **セッション管理**: Redis使用

```python
# app/storage/session.py をRedis対応に変更
import redis.asyncio as redis

redis_client = redis.from_url("redis://redis-host:6379")
```

3. **静的ファイル**: CDN使用（CloudFlare、AWS CloudFront）

### 垂直スケーリング

```bash
# Uvicornワーカー数調整
uv run uvicorn app.main:app --workers 8
```

ワーカー数目安: CPU コア数 × 2 + 1

## セキュリティ

### ファイアウォール

```bash
# ufw設定
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### レート制限（Nginx）

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /units/create {
    limit_req zone=api_limit burst=5 nodelay;
    proxy_pass http://pixel_api;
}
```

### API認証（将来）

JWTトークン認証の実装推奨。

## トラブルシューティング

### サービスが起動しない

```bash
# ログ確認
sudo journalctl -u pixel-simu-arena -n 100

# 環境変数確認
sudo systemctl show pixel-simu-arena -p Environment

# 手動起動テスト
cd /var/www/pixel-simu-arena/server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### データベース接続エラー

```bash
# PostgreSQL稼働確認
sudo systemctl status postgresql

# 接続テスト
psql -h prod-host -U pixel_user -d pixel_simu_arena
```

### Mistral API エラー

- Rate limit到達: 待機またはキャッシング実装
- タイムアウト: `timeout`設定を増やす
- 認証エラー: APIキーを確認

## パフォーマンスチューニング

### PostgreSQL

```sql
-- コネクションプール設定
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### Uvicorn

```bash
# パフォーマンス最適化オプション
uv run uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --access-log \
  --log-level info
```

## 更新手順

```bash
# 1. 最新コードをpull
cd /var/www/pixel-simu-arena
git pull origin main

# 2. 依存関係更新
cd server
uv sync

# 3. マイグレーション実行
uv run alembic upgrade head

# 4. サービス再起動
sudo systemctl restart pixel-simu-arena

# 5. ヘルスチェック
curl https://api.pixel-simu-arena.com/health
```

## 連絡先

問題が発生した場合:
- GitHub Issues: <repository-url>/issues
- Email: support@pixel-simu-arena.com
