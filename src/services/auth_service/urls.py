"""
Authentication service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', AuthViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
    path('profile/', AuthViewSet.as_view({'get': 'profile'}), name='auth-profile'),
    path('profile/update/', AuthViewSet.as_view({'put': 'update_profile'}), name='auth-update-profile'),
    path('change-password/', AuthViewSet.as_view({'post': 'change_password'}), name='auth-change-password'),
    path('forgot-password/', AuthViewSet.as_view({'post': 'forgot_password'}), name='auth-forgot-password'),
    path('reset-password/', AuthViewSet.as_view({'post': 'reset_password'}), name='auth-reset-password'),
    path('verify-email/', AuthViewSet.as_view({'post': 'verify_email'}), name='auth-verify-email'),
    path('resend-verification/', AuthViewSet.as_view({'post': 'resend_verification'}), name='auth-resend-verification'),
    path('connect-wallet/', AuthViewSet.as_view({'post': 'connect_wallet'}), name='auth-connect-wallet'),
    path('wallet-balance/', AuthViewSet.as_view({'get': 'wallet_balance'}), name='auth-wallet-balance'),
    path('disconnect-wallet/', AuthViewSet.as_view({'post': 'disconnect_wallet'}), name='auth-disconnect-wallet'),
]
