# # Agent Payment Protocol (backend logic)
# def sign_ap2_purchase(user_wallet, amount, data, agent_private_key):
#     # Use EIP712 or similar agent signing
#     # This is a skeleton
#     sig = "AGENT_SIMULATED_SIGNATURE"
#     return sig

# def verify_ap2_purchase(agent_sig, expected_data):
#     # Stub: Validate AP2 protocol agent signature
#     return agent_sig == "AGENT_SIMULATED_SIGNATURE"

def sign_ap2(user_wallet, amount, data, agent_private_key):
    return "FAKE_SIGNATURE_FOR_DEMO"
def verify_ap2(agent_sig, expected):
    return agent_sig == "FAKE_SIGNATURE_FOR_DEMO"
