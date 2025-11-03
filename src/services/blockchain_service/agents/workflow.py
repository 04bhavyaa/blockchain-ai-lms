# from agents.langgraph_agent import LangGraphAgent
# from web3.client import Web3Client
# from protocols import ap2, zkp

# def purchase_and_certificate_workflow(user_wallet, course_id, amount, data, agent_key):
#     agent = LangGraphAgent(Web3Client(), ap2, zkp)
#     return agent.execute_purchase_workflow(user_wallet, course_id, amount, data, agent_key)

def purchase_and_certificate_workflow(user_wallet, course_id, amount, agent_key):
    from agents.langgraph_agent import LangGraphAgent
    from web3.client import Web3Client
    agent = LangGraphAgent(Web3Client(), agent_key)
    return agent.execute_purchase_flow(user_wallet, course_id, amount, "Course purchase")
