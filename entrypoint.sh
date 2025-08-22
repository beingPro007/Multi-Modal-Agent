#!/bin/bash

AGENT_NAME=${AGENT_NAME:-LeadAgent}
echo "🚀 Starting agent: $AGENT_NAME"

case "$AGENT_NAME" in
  LeadAgent)
    python Agent/LeadAgent/LeadAgent.py start
    ;;
  SalesAgent)
    python Agent/SalesAgent/SalesAgent.py start
    ;;
  SupportAgent)
    python Agent/SupportAgent/SupportAgent.py start
    ;;
  *)
    echo "❌ Unknown agent: $AGENT_NAME"
    exit 1
    ;;
esac
