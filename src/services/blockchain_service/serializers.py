from rest_framework import serializers
from .models import OnChainPayment, Certificate, ApprovalRequest

class OnChainPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    class Meta:
        model = OnChainPayment
        fields = ['id', 'user_email', 'course_id', 'course_name', 'tokens_amount',
                  'user_wallet_address', 'platform_treasury_address', 'transaction_hash',
                  'block_number', 'gas_used', 'gas_price', 'status', 'confirmation_count',
                  'metadata', 'created_at', 'confirmed_at']
        read_only_fields = ['id', 'user_email', 'transaction_hash', 'status',
                            'confirmation_count', 'created_at', 'confirmed_at', 'block_number',
                            'gas_used', 'gas_price', 'metadata']

class RequestApprovalSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    tokens_to_approve = serializers.IntegerField(required=False)  # Optional, will be calculated from course

class ApprovalDataSerializer(serializers.Serializer):
    token_contract = serializers.CharField()
    spender_address = serializers.CharField()
    amount = serializers.CharField()
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    message = serializers.CharField()

class ConfirmPaymentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    transaction_hash = serializers.CharField()

class CertificateSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    class Meta:
        model = Certificate
        fields = ['id', 'user_email', 'course_id', 'course_name', 'completion_date',
                  'status', 'nft_token_id', 'nft_contract_address', 'transaction_hash',
                  'certificate_hash', 'zk_proof_hash', 'ipfs_metadata_hash', 'metadata',
                  'issued_at', 'minted_at', 'verified_at', 'verified_by']
        read_only_fields = ['id', 'user_email', 'nft_token_id', 'transaction_hash',
                            'certificate_hash', 'issued_at', 'minted_at', 'verified_at',
                            'verified_by', 'status', 'zk_proof_hash', 'ipfs_metadata_hash']

class IssueCertificateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_name = serializers.CharField(max_length=255)
    completion_date = serializers.DateField()
    metadata = serializers.JSONField(required=False, default=dict)

class VerifyCertificateSerializer(serializers.Serializer):
    certificate_id = serializers.IntegerField()
    zk_proof = serializers.CharField()

class BlockchainStatsSerializer(serializers.Serializer):
    total_on_chain_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    total_tokens_transferred = serializers.IntegerField()
    certificates_minted = serializers.IntegerField()
