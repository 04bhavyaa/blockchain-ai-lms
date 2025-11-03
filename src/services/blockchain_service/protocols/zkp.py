# def generate_zkp(certificate_hash, user_data):
#     # Stub for ZKP hash creation (use real libraries for real ZKP)
#     import hashlib
#     return hashlib.sha256((certificate_hash + str(user_data)).encode()).hexdigest()

# def verify_zkp(certificate_hash, zk_proof_hash, user_data):
#     expected_hash = generate_zkp(certificate_hash, user_data)
#     return expected_hash == zk_proof_hash

def generate_zkp(cert_hash, user_id):
    from hashlib import sha256
    return sha256(f"{cert_hash}_{user_id}".encode()).hexdigest()
def verify_zkp(cert_hash, zkp_hash, user_id):
    return generate_zkp(cert_hash, user_id) == zkp_hash
