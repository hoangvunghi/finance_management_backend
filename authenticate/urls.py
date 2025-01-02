from django.urls import path
from .views import user_register, user_login, forgot_password_view, reset_password_view, update_profile, user_logout, send_otp, verify_otp_view, change_password, get_information

urlpatterns = [
    # path("forgot/forgot-password", forgot_password_view, name="forgot-password"),
    path('register', user_register,name='register'),
    path('login', user_login,name='login'),
    path('send-otp/', send_otp, name='send_otp'),                  
    path('verify-otp/', verify_otp_view, name='verify_otp'),       
    path('change-password/', change_password, name='change_password'), 
    # path("forgot/reset-password/<str:token>", reset_password_view, name="reset_password"),
    path("update-profile", update_profile, name="update-profile"),
    path("logout", user_logout, name="logout"),
    path("get-information", get_information, name="get-information"),
]
