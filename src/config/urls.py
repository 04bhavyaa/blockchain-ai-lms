from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from pathlib import Path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

API_VERSION = 'v1'

def serve_index(request):
    """Serve index.html from frontend-simple"""
    index_path = settings.BASE_DIR.parent / 'frontend-simple' / 'index.html'
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except Exception as e:
        print(f"Error serving index.html: {e}")
        return HttpResponse('index.html not found', status=404)

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

# Serve frontend pages in development
if settings.DEBUG:
    urlpatterns += [
        # Specific frontend pages
        path('pages/auth/login.html', TemplateView.as_view(template_name='pages/auth/login.html'), name='login'),
        path('pages/auth/register.html', TemplateView.as_view(template_name='pages/auth/register.html'), name='register'),
        path('pages/auth/verify-email.html', TemplateView.as_view(template_name='pages/auth/verify-email.html'), name='verify-email'),
        path('pages/auth/resend-verification.html', TemplateView.as_view(template_name='pages/auth/resend-verification.html'), name='resend-verification'),
        path('pages/dashboard/dashboard.html', TemplateView.as_view(template_name='pages/dashboard/dashboard.html'), name='dashboard'),
        path('pages/courses/courses.html', TemplateView.as_view(template_name='pages/courses/courses.html'), name='courses'),
        path('pages/chatbot/chatbot.html', TemplateView.as_view(template_name='pages/chatbot/chatbot.html'), name='chatbot'),
        path('pages/user/profile.html', TemplateView.as_view(template_name='pages/user/profile.html'), name='profile'),
        # Static and media files
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        # Serve assets directly from frontend-simple
        *static('/assets/', document_root=settings.BASE_DIR.parent / 'frontend-simple' / 'assets'),
        # Home page - serve index.html
        path('', serve_index, name='home'),
        path('index.html', serve_index, name='home-index'),
    ]
