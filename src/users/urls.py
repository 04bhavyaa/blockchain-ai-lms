"""
User service URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('profile/', UserViewSet.as_view({'get': 'profile', 'put': 'update_profile'}), name='user-profile'),
    path('connect-wallet/', UserViewSet.as_view({'post': 'connect_wallet'}), name='user-connect-wallet'),
    path('disconnect-wallet/', UserViewSet.as_view({'post': 'disconnect_wallet'}), name='user-disconnect-wallet'),
    path('change-password/', UserViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
    path('token-balance/', UserViewSet.as_view({'get': 'token_balance'}), name='user-token-balance'),
]
