#!/bin/bash
# Service status check script with arguments
# Usage: ssh_admin exec_file --script_path scripts_ssh/service_check.sh --args ["nginx", "postgresql"]

set -e

# Check if services are provided as arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <service1> [service2] [service3] ..."
    echo "Example: $0 nginx postgresql docker"
    exit 1
fi

echo "=== Service Status Check ==="
echo ""

# Check each service
for service in "$@"; do
    echo "Checking $service..."
    
    if systemctl is-active --quiet "$service"; then
        status=$(systemctl is-active "$service")
        uptime=$(systemctl show "$service" -p ActiveEnterTimestamp --value | cut -d' ' -f1-3)
        echo "✅ $service: $status (since $uptime)"
    else
        status=$(systemctl is-active "$service" 2>&1 || echo "not found")
        echo "❌ $service: $status"
    fi
    echo ""
done

echo "✅ Service check completed"
