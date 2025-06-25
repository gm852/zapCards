#!/bin/bash

set -e

APP_NAME="zapcards"
INSTALL_DIR="/opt/$APP_NAME"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

# check for root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root"
  exit 1
fi

# uninstall flag
if [ "$1" == "-u" ]; then
  echo "🗑️ Uninstalling $APP_NAME..."

  if systemctl is-active --quiet "$APP_NAME"; then
    echo "🛑 Stopping service..."
    systemctl stop "$APP_NAME"
  fi

  if systemctl is-enabled --quiet "$APP_NAME"; then
    echo "🔌 Disabling service..."
    systemctl disable "$APP_NAME"
  fi

  if [ -f "$SERVICE_FILE" ]; then
    echo "🧹 Removing service file..."
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
  fi

  if [ -d "$INSTALL_DIR" ]; then
    echo "🗑️ Removing installation directory..."
    rm -rf "$INSTALL_DIR"
  fi

  echo "✅ $APP_NAME has been successfully uninstalled."
  exit 0
fi

echo "🛠️ Installing $APP_NAME..."

# install dependencies
echo "📦 Ensuring required packages are installed..."
apt update
apt install -y git python3 python3-venv python3-pip

# clone the repo
if [ ! -d "$INSTALL_DIR" ]; then
  echo "📥 Cloning the repository..."
  git clone https://github.com/gm852/zapCards.git "$INSTALL_DIR"
else
  echo "🔁 Updating existing repository..."
  cd "$INSTALL_DIR"
  git pull
fi

# copy settings.conf.example to settings.conf if not exists
if [ -f "$INSTALL_DIR/settings.conf.example" ] && [ ! -f "$INSTALL_DIR/settings.conf" ]; then
  echo "📋 Copying settings.conf.example to settings.conf"
  cp "$INSTALL_DIR/settings.conf.example" "$INSTALL_DIR/settings.conf"
else
  echo "⚙️ settings.conf already exists or example missing, skipping copy."
fi

# check if Python3 is installed
if ! command -v python3 >/dev/null 2>&1; then
  echo "📦 Python3 not found. Installing..."
  apt update && apt install -y python3 python3-venv python3-pip
else
  echo "✅ Python3 is already installed"
fi

# set up venv
cd "$INSTALL_DIR"
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "📦 Installing Python requirements..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r req.txt

# create systemd service
echo "📝 Creating systemd service..."
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=ZapCardsAI
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python run.py --dev --port 8089
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# enable and start the service
echo "🔄 Enabling and starting $APP_NAME service..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

echo "✅ $APP_NAME is now installed and running at port 8089!"
