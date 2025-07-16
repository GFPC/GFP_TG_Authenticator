#!/bin/sh
# Install TGAuthenticator systemd service (developed by GFP)
# Usage: sh install_tg_authenticator.sh

SERVICE_FILE=tg_authenticator.service
TARGET_PATH=/etc/systemd/system/tg_authenticator.service
CURDIR=$(pwd)
USER_NAME=$(whoami)

if [ ! -f "$SERVICE_FILE" ]; then
  echo "Service file $SERVICE_FILE not found!"
  exit 1
fi

# Prepare a temp file with replaced paths and user
TMP_SERVICE_FILE="/tmp/tg_authenticator.service.$$"
sed \
  -e "s|WorkingDirectory=.*|WorkingDirectory=$CURDIR|" \
  -e "s|EnvironmentFile=.*|EnvironmentFile=$CURDIR/.env|" \
  -e "s|User=.*|User=$USER_NAME|" \
  "$SERVICE_FILE" > "$TMP_SERVICE_FILE"

sudo cp "$TMP_SERVICE_FILE" "$TARGET_PATH"
sudo systemctl daemon-reload
sudo systemctl enable tg_authenticator.service
sudo systemctl restart tg_authenticator.service
rm "$TMP_SERVICE_FILE"

echo "TGAuthenticator service installed and started with WorkingDirectory=$CURDIR and User=$USER_NAME." 