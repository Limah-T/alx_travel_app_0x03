from django.urls import path
from .views import UserApiView, Verify_signup_token, ModifyUserViewset, LoginApiView, UserProfileViewset, VerifyEmailUpdate, ResetPassword, VerifyPasswordReset, SetPasswordView, Change_passwordView, VerifyAcctDeactivation, LogoutView, PropertyViewset, BookingViewset, payment_view

urlpatterns = [
    path('register/', UserApiView.as_view(), name='register'),
    path('verify', Verify_signup_token, name='verify'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('users/', ModifyUserViewset.as_view({'get': 'list'}), name='users'),
    path('user/<uuid:uuid>/', ModifyUserViewset.as_view({'get':'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'}), name='user'),
    path('profile/', UserProfileViewset.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'}), name='profile'),
    path('verify_update', VerifyEmailUpdate, name='verify_update'),

    path('reset_password/', ResetPassword.as_view(), name='reset_password'),
    path('reset_password_verify', VerifyPasswordReset, name='reset_password_verify'),
    path('set_password/', SetPasswordView.as_view(), name='set_password'),
    path('change_password/', Change_passwordView.as_view(), name='change_password'),
    path('deactivate_acct_verify', VerifyAcctDeactivation, name='deactivate_acct_verify'),
    
    path('logout/', LogoutView.as_view(), name='logout'),

    path('property/', PropertyViewset.as_view({'post': 'create', 'get': 'list'}), name='property'),
    path('property/<str:pk>', PropertyViewset.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'})),
    path('booking/', BookingViewset.as_view({'post': 'create', 'get': 'list'}), name='booking'),
    path('booking/<str:pk>', BookingViewset.as_view({'get': 'retrieve', 'patch': 'update', 'put': 'update', 'delete': 'destroy'}), name='booking'),
    path('payment/<str:pk>', payment_view, name='payment'),
]