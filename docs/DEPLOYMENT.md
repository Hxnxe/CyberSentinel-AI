# Deployment Notes

## Foreground run

```bash
source .venv/bin/activate
python main.py
```

## systemd example

Create `/etc/systemd/system/cybersentinel-ai.service`:

```ini
[Unit]
Description=CyberSentinel AI security monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/CyberSentinel-AI
EnvironmentFile=/opt/CyberSentinel-AI/.env
ExecStart=/opt/CyberSentinel-AI/.venv/bin/python main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cybersentinel-ai
sudo systemctl status cybersentinel-ai
```

## Runtime data

Runtime data is generated locally and ignored by git:

```text
cve_database.db
logs/
results/
data/
```

Back up those files separately if they are important for your deployment.
