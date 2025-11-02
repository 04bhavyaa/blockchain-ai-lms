"""
Main URL configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

API_VERSION = 'v1'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # JWT Token endpoints
    path(f'api/{API_VERSION}/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path(f'api/{API_VERSION}/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path(f'api/{API_VERSION}/auth/', include('src.services.auth_service.urls')),
    path(f'api/{API_VERSION}/admin/', include('src.services.admin_service.urls')),
    path(f'api/{API_VERSION}/recommendations/', include('src.services.ai_recommendations.urls')),
    path(f'api/{API_VERSION}/blockchain/', include('src.services.blockchain_service.urls')),
    path(f'api/{API_VERSION}/chatbot/', include('src.services.chatbot_service.urls')),
    path(f'api/{API_VERSION}/courses/', include('src.services.courses_service.urls')),
    path(f'api/{API_VERSION}/payment/', include('src.services.payment_service.urls')),
    path(f'api/{API_VERSION}/progress/', include('src.services.progress_service.urls')),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)