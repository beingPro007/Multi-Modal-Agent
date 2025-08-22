import sys

if __name__ == "__main__":
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "LeadAgent"

    if agent_name == "LeadAgent":
        from Agent.LeadAgent.Leadagent import LeadAgent
        LeadAgent().start()

    # elif agent_name == "SalesAgent":
    #     from Agent.SalesAgent.SalesAgent import SalesAgent
    #     SalesAgent().start()

    # elif agent_name == "SupportAgent":
    #     from Agent.SupportAgent.SupportAgent import SupportAgent
    #     SupportAgent().start()

    else:
        print(f"Unknown agent: {agent_name}")
