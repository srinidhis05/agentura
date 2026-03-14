#!/bin/bash
# Fix MCP connections in EKS

set -e

echo "=== Fixing MCP Connections in EKS ==="
echo ""

# Step 1: Check current pods
echo "Step 1: Checking current pods..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system get pods
echo ""

# Step 2: Check current environment variables
echo "Step 2: Checking current MCP environment variables..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system get deployment executor -o jsonpath='{.spec.template.spec.containers[0].env[*].name}' | tr ' ' '\n' | grep -E "OBOT|MCP|ANTHROPIC" || echo "No MCP env vars found!"
echo ""
echo ""

# Step 3: Get current env values
echo "Step 3: Current OBOT_URL and MCP_GATEWAY_API_KEY:"
assume infrastructure -- kubectl --context infrastructure -n agentura-system get deployment executor -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="OBOT_URL")].value}' && echo ""
assume infrastructure -- kubectl --context infrastructure -n agentura-system get deployment executor -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="MCP_GATEWAY_API_KEY")].value}' && echo ""
echo ""

# Step 4: Check if Obot is running
echo "Step 4: Checking if Obot is running..."
assume infrastructure -- kubectl --context infrastructure -n obot-system get pods 2>/dev/null || echo "Obot namespace not found or not accessible"
echo ""

# Step 5: Set MCP environment variables (MODIFY THESE VALUES)
echo "Step 5: Setting MCP environment variables..."
echo "⚠️  IMPORTANT: Update these values before running!"
echo ""
echo "Current values (if any) shown above."
echo "You need to set:"
echo "  - OBOT_URL (Obot service URL)"
echo "  - MCP_GATEWAY_API_KEY (your Obot API key)"
echo "  - ANTHROPIC_API_KEY (for Claude)"
echo ""

read -p "Do you want to set these env vars now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    read -p "Enter OBOT_URL (e.g., http://obot-service.obot-system.svc.cluster.local:8080): " OBOT_URL
    read -p "Enter MCP_GATEWAY_API_KEY: " MCP_GATEWAY_API_KEY
    read -p "Enter ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY

    echo ""
    echo "Setting environment variables..."
    assume infrastructure -- kubectl --context infrastructure -n agentura-system set env deployment/executor \
        OBOT_URL="$OBOT_URL" \
        MCP_GATEWAY_API_KEY="$MCP_GATEWAY_API_KEY" \
        ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

    echo "✓ Environment variables set!"
    echo ""
fi

# Step 6: Restart services
echo "Step 6: Restarting executor and gateway..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system rollout restart deployment/executor
assume infrastructure -- kubectl --context infrastructure -n agentura-system rollout restart deployment/gateway
echo "✓ Deployments restarted"
echo ""

# Step 7: Wait for pods to be ready
echo "Step 7: Waiting for pods to be ready..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system wait --for=condition=ready pod -l app=executor --timeout=2m
assume infrastructure -- kubectl --context infrastructure -n agentura-system wait --for=condition=ready pod -l app=gateway --timeout=2m
echo "✓ Pods ready"
echo ""

# Step 8: Verify MCP registry
echo "Step 8: Verifying MCP registry..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system exec deployment/executor -- python3 -c "
from agentura_sdk.mcp.registry import get_registry
reg = get_registry()
print('MCP Servers discovered:')
servers = reg.list_servers()
if not servers:
    print('  ⚠️  No MCP servers found!')
else:
    for s in servers:
        print(f'  ✓ {s.name}: {s.url} ({len(s.tools)} tools)')
"
echo ""

# Step 9: Check logs
echo "Step 9: Recent executor logs (checking for MCP activity)..."
assume infrastructure -- kubectl --context infrastructure -n agentura-system logs deployment/executor --tail=50 | grep -i "mcp" || echo "No MCP activity in recent logs"
echo ""

echo "=== Fix Complete ==="
echo ""
echo "Next steps:"
echo "1. Test in Slack: Send '@pm-bot morning briefing'"
echo "2. Check output for:"
echo "   - Current date (March 2026, not January 2025)"
echo "   - Real project data (not generic examples)"
echo "   - systems_checked: [granola, clickup, notion, slack]"
echo "   - posted_to_slack: true"
echo ""
echo "If still seeing issues, check:"
echo "  - Obot UI: Verify MCP servers are configured and connected"
echo "  - Slack app: Verify 'chat:write' scope is enabled"
echo "  - Executor logs: assume infrastructure -- kubectl -n agentura-system logs deployment/executor -f"
echo ""
