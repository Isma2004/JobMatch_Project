# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomTokenObtainPairView, JobPositionViewSet, JobApplicationViewSet, LogoutView, RegistrationView, CandidateProfileViewSet, UserViewSet
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


router = DefaultRouter()
router.register(r'jobs', JobPositionViewSet, basename='jobposition')
router.register(r'applications', JobApplicationViewSet, basename='jobapplication')
router.register(r'candidate-profile', CandidateProfileViewSet, basename='candidate-profile')
router.register(r'user', UserViewSet, basename='user')


urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # URL for obtaining JWT token
    path('register/', RegistrationView.as_view(), name='register'),  # URL for user registration
    path('', include(router.urls)),
    path('api/jobs/<int:job_id>/resumes/', JobPositionViewSet.as_view({'get': 'view_resumes'}), name='job-resumes'),
    path('api/', include(router.urls)),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),  # Add this
]

