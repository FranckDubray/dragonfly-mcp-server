#!/bin/bash
# System health check script
# Usage: ssh_admin exec_file --script_path scripts_ssh/health_check.sh

set -e

echo "=== System Health Check ==="
echo ""

echo "📊 CPU Load:"
uptime | awk -F'load average:' '{print $2}'

echo ""
echo "💾 Memory Usage:"
free -h | grep Mem | awk '{printf "Used: %s / %s (%.1f%%)\n", $3, $2, ($3/$2)*100}'

echo ""
echo "💿 Disk Usage:"
df -h / | tail -1 | awk '{printf "Used: %s / %s (%s)\n", $3, $2, $5}'

echo ""
echo "🔌 Network:"
ip -4 addr show | grep inet | grep -v 127.0.0.1 | awk '{print $2}'

echo ""
echo "✅ Health check completed"
