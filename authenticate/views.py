from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import dumps,loads
from datetime import datetime,timedelta
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
import random,string
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from django.contrib.auth.models import User
from base.models import UserProfile,OTP
import re
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer, UserProfileSerializer, UserSerializer
from random import randint
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def get_information(request):
    print("-----------------")
    print(request.user)
    try:
        user = request.user
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    print("-----------------")
    print(username, email, first_name, last_name)
    return Response({"username": username, "email": email, "first_name": first_name, "last_name": last_name}, status=status.HTTP_200_OK)


@api_view(["POST"])
def user_register(request):
    print(request.data)
    serializer = UserSerializer(data=request.data)
    required_fields = ["username", "password", "email", "first_name", "last_name"]
    data = {field: request.data.get(field, '').strip() for field in required_fields}

    missing_fields = [field for field, value in data.items() if not value]
    if missing_fields:
        return Response({"message": f"{', '.join(missing_fields).capitalize()} is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(data['email'])
    except ValidationError:
        return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

    if len(data['password']) < 8:
        return Response({"message": "Password must be at least 8 characters long"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=data['username']).exists():
        return Response({"message": "Username is already taken"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=data['email']).exists():
        return Response({"message": "Email is already taken"}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        user = User.objects.create_user(
            username=data['username'], email=data['email'], password=data['password'],
            first_name=data['first_name'], last_name=data['last_name']
        )

        employee_email = data['email']
        employee_name = data["first_name"] + " " + data["last_name"]
        email_subject = "Chào mừng đến với FinMa"
        email_message = f" Xin chào {employee_name},\n\n"
        email_message += f" Tài khoản của bạn đã được kích hoạt thành công trong hệ thống.\n"
        email_message += f"\tUsername: {data['username']}\n" 
        email_message += "\n\n*Đây là email từ hệ thống đề nghị không reply."

        send_mail(
            email_subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [employee_email],
            fail_silently=False,
        )
        return Response({
            "response": "User registered successfully",
            "data": {
                "username": user.username,
                "email": user.email
            },
            "status": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)
    
    return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def user_login(request):
    print(request.data)
    if request.method == "POST":
        try:
            username = request.data.get("username", "").lower()
            password = request.data.get("password", "")
            
            if not username or not password:
                return Response(
                    {"error": "Username and password are required", "status": status.HTTP_400_BAD_REQUEST},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = authenticate(request, username=username, password=password)

            if user is not None:
                try:
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                except TokenError as e:
                    if isinstance(e, InvalidToken) and e.args[0] == "Token has expired":
                        return Response(
                            {"error": "Access token has expired. Please refresh the token.",
                             "status": status.HTTP_401_UNAUTHORIZED},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                    else:
                        return Response(
                            {"error": "Invalid token.", "status": status.HTTP_401_UNAUTHORIZED},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                    
                response_data = {
                    "response": "Login successful",
                    "data": {"username": user.username, "email": user.email,"first_name":user.first_name,"last_name":user.last_name},
                    'token': {
                        'refresh': str(refresh),
                        'access': access_token,
                    },
                    "status": status.HTTP_200_OK,
                }
                response = Response(response_data, status=status.HTTP_200_OK)
                return response
            else:
                return Response(
                    {'error': 'Invalid username or password', "status": status.HTTP_401_UNAUTHORIZED},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except Exception as e:
            return Response(
                {'error': str(e), "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    try:
        refresh_token = request.data.get("refresh_token")
        access_token = request.auth

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(access_token)
            token.blacklist()
        except TokenError:
            pass 

        return Response(
            {"message": "Logged out successfully. All tokens have been invalidated"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



def generate_and_send_otp(email):
    code = str(randint(100000, 999999))

    otp, created = OTP.objects.update_or_create(
        email=email,
        defaults={'code': code, 'created_at': now()}  
    )

    try:
        username = User.objects.get(email=email).username

        send_mail(
            'Your OTP Code',
            f'Your OTP code for account {username} is {code}. It will expire in 5 minutes.',
            'noreply@example.com',
            [email],
            fail_silently=False,
        )
        return True
    except User.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False


def verify_otp(email, input_code):
    try:
        print(email)

        otp = OTP.objects.get(email=email)  
        print(otp)
        if otp.is_valid() and otp.code == input_code: 
            return True
        elif not otp.is_valid():
            return "expired" 
    except OTP.DoesNotExist:
        return "not_found"
    return False


@api_view(["POST"])
def send_otp(request):
    email = request.data.get("email", "")
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

    if generate_and_send_otp(email):
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
    return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def verify_otp_view(request):
    print(request.data)
    email = request.data.get("email", "")
    code = request.data.get("code", "")
    if not email or not code:
        return Response({"error": "Email and code are required"}, status=status.HTTP_400_BAD_REQUEST)

    result = verify_otp(email, code)
    print(result)
    if result == True:
        username = User.objects.get(email=email).username
        return Response({"message": "OTP verified successfully", "username": username}, status=status.HTTP_200_OK)
    elif result == "expired":
        return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
    elif result == "not_found":
        return Response({"error": "Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def change_password(request):
    print(request.data)
    otp_code = request.data.get("otp_code", "")
    email = request.data.get("email", "")
    password = request.data.get("password", "")

    if not otp_code or not email or not password:
        return Response({"error": "OTP code, email, and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    print("1")
    try:
        otp = OTP.objects.get(email=email, code=otp_code)
        print(otp)
        if not otp.is_valid():
            return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
        otp.delete() 


        user = User.objects.get(email=email)
        print("-----++++++")
        print(user)
        user.set_password(password)
        user.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    except OTP.DoesNotExist:
        return Response({"error": "Invalid OTP code"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
def forgot_password_view(request):
    email = request.data.get("email", "")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "User not found for the provided email"},
                        status=status.HTTP_404_NOT_FOUND)
    try:
        data={"username":user.username}
        token=dumps(data, key=settings.SECURITY_PASSWORD_SALT)

    except TokenError as e:
        return Response({"error": "Failed to generate reset token",
                         "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    email_subject = "Password Reset Request"
    email_message = f"Here's an email about forgetting the password for account: {user.username} \n "
    email_message += f"Click the following link to reset your password: {settings.BACKEND_URL}/forgot/reset-password/{token}"

    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

    return Response({"message": "Password reset email sent successfully",
                     "status": status.HTTP_200_OK},
                    status=status.HTTP_200_OK)

@api_view(["POST"])
def reset_password_view(request, token):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        username = loads(token,key=settings.SECURITY_PASSWORD_SALT)["username"]
        user = User.objects.get(username=username)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid reset token",
                         "status": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST)
    new_password = serializer.validated_data['password']
    if not new_password:
        raise ValidationError("New password is required")
    hashed_password = make_password(new_password)
    user.password = hashed_password
    user.save()
    refresh = RefreshToken.for_user(user)
    return Response({"message": "Password reset successfully",
                     "status": status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


def validate_to_update(obj, data):
    errors={}
    dict=['id', 'username']
    for key in data:
        if key in dict:
            errors[key]= f"{key} not allowed to change"         
    return errors 


def obj_update(obj, validated_data):
    for key, value in validated_data.items():
        if key == 'avatar':
            try:
                image_data = base64.b64decode(value.split(',')[1])
                image_file = ContentFile(image_data, name='uploaded_image.jpg')
                setattr(obj, key, image_file)
            except Exception as e:
                raise ValueError("Invalid attempt to update avatar")
        elif key == 'password':
            continue 
        else:
            setattr(obj, key, value)

    obj.save()

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def update_profile(request):
    print(request.data)
    try:
        user = request.user
       
    except User.DoesNotExist:
        return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method != 'PATCH':
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    password = request.data.get('password')
    print(password)
    if not password:
        return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
    print(user.password)
    print("-----------------")
    print(check_password(password, user.password))
    if not check_password(password, user.password):
        print("Invalid password")
        return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

    validation_errors = validate_to_update(user, request.data)
    if validation_errors:
        return Response({"errors": validation_errors}, status=status.HTTP_400_BAD_REQUEST)

    if email := request.data.get('email'):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)
    
        if UserProfile.objects.filter(user__email=email).exclude(user=user).exists():
            return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password := request.data.get('new_password'):
        if len(new_password) < 8:
            return Response({"error": "Password must be at least 8 characters long"}, 
                        status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)# Cập nhật mật khẩu mới
        user.save()

    try:
        with transaction.atomic():
            obj_update(user, request.data)
            user.save()
            # Serialize và trả về response
            serializer = UserSerializer(user)
            return Response({
                "message": "Profile updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)