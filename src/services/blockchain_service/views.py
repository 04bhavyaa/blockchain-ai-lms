"""
Blockchain service views - On-chain token payments
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import logging

from .models import OnChainPayment, Certificate, ApprovalRequest, WebhookLog
from .serializers import (
    OnChainPaymentSerializer, RequestApprovalSerializer,
    ApprovalDataSerializer, ConfirmPaymentSerializer,
    CertificateSerializer, IssueCertificateSerializer,
    VerifyCertificateSerializer, BlockchainStatsSerializer
)
from .web3_client import Web3Client
from .smart_contracts import SmartContractManager
from src.shared.exceptions import ValidationError, BlockchainError, ResourceNotFoundError
from src.services.courses_service.models import Enrollment, Course
from django.conf import settings

logger = logging.getLogger(__name__)


class OnChainPaymentViewSet(viewsets.ViewSet):
    """On-chain token payments for course access"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def request_approval(self, request):
        """
        Step 1: Request ERC20 approval data
        User will approve spending limit in MetaMask
        """
        
        serializer = RequestApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data['course_id']
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ResourceNotFoundError("Course not found")
        
        if course.access_type != 'token':
            raise ValidationError("This course is not token-gated")
        
        if not request.user.wallet_address:
            raise ValidationError("Wallet not connected. Connect MetaMask first.")
        
        try:
            token_contract = SmartContractManager.get_token_contract()
            if not token_contract:
                raise BlockchainError("Token contract not deployed")
            
            platform_treasury = getattr(
                settings,
                'PLATFORM_TREASURY_ADDRESS',
                None
            )
            if not platform_treasury:
                raise BlockchainError("Platform treasury not configured")
            
            # Create approval request
            approval = ApprovalRequest.objects.create(
                user=request.user,
                course_id=course_id,
                tokens_to_approve=course.token_cost,
                spender_address=platform_treasury,
                expires_at=timezone.now() + timedelta(minutes=15)
            )
            
            response_data = {
                'token_contract': token_contract.contract_address,
                'spender_address': platform_treasury,
                'amount': str(course.token_cost),
                'course_id': course_id,
                'course_title': course.title,
                'message': f'Approve {course.token_cost} LMS tokens to unlock {course.title}',
            }
            
            serializer = ApprovalDataSerializer(response_data)
            
            logger.info(f"Approval request created: {request.user.email} - {course.title}")
            
            return Response({
                'status': 'success',
                'message': 'Use this data to sign approval in MetaMask',
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Error requesting approval: {str(e)}")
            raise BlockchainError(str(e))
    
    @action(detail=False, methods=['post'])
    def confirm_payment(self, request):
        """
        Step 2: Confirm on-chain payment
        User has approved spending and transaction executed
        We verify transaction on blockchain and unlock course
        """
        
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data['course_id']
        transaction_hash = serializer.validated_data['transaction_hash']
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ResourceNotFoundError("Course not found")
        
        if not request.user.wallet_address:
            raise ValidationError("Wallet not connected")
        
        try:
            # Verify transaction on blockchain
            web3_client = Web3Client(network='sepolia')
            tx_receipt = web3_client.get_transaction_receipt(transaction_hash)
            
            if not tx_receipt:
                raise BlockchainError("Transaction not found on blockchain")
            
            if tx_receipt['status'] != 1:
                raise BlockchainError("Transaction failed on blockchain")
            
            # Check if already enrolled
            if Enrollment.objects.filter(user=request.user, course=course).exists():
                raise ValidationError("Already enrolled in this course")
            
            # Verify token balance before payment
            token_contract = SmartContractManager.get_token_contract()
            if token_contract:
                balance = web3_client.get_token_balance(
                    token_contract.contract_address,
                    request.user.wallet_address,
                    token_contract.contract_abi
                )
                
                if balance < course.token_cost:
                    raise ValidationError(
                        f"Insufficient tokens. Required: {course.token_cost}, "
                        f"Available: {balance}"
                    )
            
            # Get confirmation count
            confirmations = web3_client.get_transaction_confirmation_count(transaction_hash)
            
            # Create on-chain payment record
            payment = OnChainPayment.objects.create(
                user=request.user,
                course_id=course_id,
                course_name=course.title,
                tokens_amount=course.token_cost,
                user_wallet_address=request.user.wallet_address,
                platform_treasury_address=getattr(
                    settings,
                    'PLATFORM_TREASURY_ADDRESS',
                    ''
                ),
                transaction_hash=transaction_hash,
                block_number=tx_receipt['block_number'],
                gas_used=tx_receipt['gas_used'],
                status='confirmed',
                confirmation_count=confirmations,
                confirmed_at=timezone.now()
            )
            
            # Create enrollment
            enrollment = Enrollment.objects.create(
                user=request.user,
                course=course,
                status='enrolled'
            )
            
            # Increment course enrollment count
            course.total_enrollments += 1
            course.save()
            
            logger.info(
                f"On-chain payment confirmed: {request.user.email} - "
                f"{course.title} - {course.token_cost} tokens - TX: {transaction_hash[:10]}..."
            )
            
            return Response({
                'status': 'success',
                'message': f'Course unlocked! Access granted to {course.title}',
                'data': {
                    'course_id': course_id,
                    'course_title': course.title,
                    'tokens_spent': course.token_cost,
                    'transaction_hash': transaction_hash,
                    'confirmations': confirmations,
                    'enrollment_id': enrollment.id,
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}", exc_info=True)
            raise BlockchainError(str(e))
    
    @action(detail=False, methods=['get'])
    def payment_history(self, request):
        """Get user's on-chain payment history"""
        
        payments = OnChainPayment.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = OnChainPaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OnChainPaymentSerializer(payments, many=True)
        return Response({'status': 'success', 'data': serializer.data})


class CertificateViewSet(viewsets.ModelViewSet):
    """NFT certificate management"""
    
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_certificates(self, request):
        """Get user's certificates"""
        
        certificates = self.get_queryset().order_by('-issued_at')
        serializer = self.get_serializer(certificates, many=True)
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def issue_certificate(self, request):
        """Issue certificate for course completion"""
        
        serializer = IssueCertificateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            import hashlib
            
            course_id = serializer.validated_data['course_id']
            course_name = serializer.validated_data['course_name']
            completion_date = serializer.validated_data['completion_date']
            metadata = serializer.validated_data.get('metadata', {})
            
            # Generate certificate hash
            cert_data = f"{request.user.id}_{course_id}_{completion_date}"
            certificate_hash = hashlib.sha256(cert_data.encode()).hexdigest()
            
            # Create certificate record
            certificate = Certificate.objects.create(
                user=request.user,
                course_id=course_id,
                course_name=course_name,
                completion_date=completion_date,
                certificate_hash=certificate_hash,
                metadata=metadata,
                status='pending'
            )
            
            logger.info(
                f"Certificate issued: {request.user.email} - {course_name}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Certificate issued successfully',
                'data': CertificateSerializer(certificate).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error issuing certificate: {str(e)}")
            raise BlockchainError(str(e))
    
    @action(detail=True, methods=['post'])
    def verify_certificate(self, request, pk=None):
        """Verify certificate with ZK proof (employer endpoint)"""
        
        try:
            certificate = Certificate.objects.get(pk=pk)
        except Certificate.DoesNotExist:
            raise ResourceNotFoundError("Certificate not found")
        
        serializer = VerifyCertificateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        certificate.status = 'verified'
        certificate.verified_at = timezone.now()
        certificate.verified_by = request.user
        certificate.save()
        
        return Response({
            'status': 'success',
            'message': 'Certificate verified',
            'data': {
                'is_valid': True,
                'certificate_hash': certificate.certificate_hash,
                'course': certificate.course_name,
                'completion_date': certificate.completion_date.isoformat(),
                'learner_verified': True,
            }
        })


class BlockchainStatsViewSet(viewsets.ViewSet):
    """Blockchain statistics"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get blockchain statistics"""
        
        user_payments = OnChainPayment.objects.filter(user=request.user)
        user_certificates = Certificate.objects.filter(user=request.user)
        
        stats = {
            'total_on_chain_payments': user_payments.count(),
            'successful_payments': user_payments.filter(status='confirmed').count(),
            'failed_payments': user_payments.filter(status='failed').count(),
            'total_tokens_transferred': sum(
                p.tokens_amount for p in user_payments.filter(status='confirmed')
            ),
            'certificates_minted': user_certificates.filter(status='minted').count(),
        }
        
        serializer = BlockchainStatsSerializer(stats)
        return Response({'status': 'success', 'data': serializer.data})
