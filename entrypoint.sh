AGENT_TYPE=${AGENT_TYPE:-default}

echo "Starting container with AGENT_TYPE=$AGENT_TYPE"

case "$AGENT_TYPE" in
  default)
    exec python agent.py dev"$@"
    ;;
  lead)
    exec python leadagent.py dev"$@"
    ;;
  *)
    echo "Unknown AGENT_TYPE: $AGENT_TYPE"
    exit 1
    ;;
esac
