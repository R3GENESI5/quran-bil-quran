#!/bin/bash
# Quran bil-Quran — local launcher

PORT=8080
DIR="$(cd "$(dirname "$0")/app" && pwd)"

# Check Python
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "Python not found. Install Python 3 from https://python.org"
    echo "Or open app/index.html directly in your browser."
    exit 1
fi

# Get local IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LOCAL_IP" ] && LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null)

echo ""
echo "  Quran bil-Quran"
echo ""
echo "  Local:   http://localhost:$PORT"
[ -n "$LOCAL_IP" ] && echo "  Phone:   http://$LOCAL_IP:$PORT"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# Open browser
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$PORT" &
elif command -v open &>/dev/null; then
    open "http://localhost:$PORT"
fi

# Start server
cd "$DIR"
$PY -m http.server $PORT
