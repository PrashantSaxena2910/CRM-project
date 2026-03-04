from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import Organization, UserProfile, Customer
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, UserSerializer,
    UserRegistrationSerializer, CustomerSerializer, CustomerDetailSerializer,LoginSerializer
)
from .permissions import IsOrganizationMember, IsOrganizationAdmin, CanManageCustomers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response("User Created", UserSerializer),
            400: "Bad Request",
        },
        operation_description="Register a new user and return authentication token."
    )    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
  
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response("Login Successful"),
            401: "Invalid credentials"
        },
        operation_description="Login user and return auth token."
    )
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
   
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    @swagger_auto_schema(security=[{'Token': []}])
    def put(self, request):
        user_data = {
            'first_name': request.data.get('first_name', request.user.first_name),
            'last_name': request.data.get('last_name', request.user.last_name),
            'email': request.data.get('email', request.user.email),
        }
        
        for key, value in user_data.items():
            setattr(request.user, key, value)
        request.user.save()
        
        if hasattr(request.user, 'profile'):
            profile_data = {
                'phone': request.data.get('phone', request.user.profile.phone),
                'department': request.data.get('department', request.user.profile.department),
            }
            
            for key, value in profile_data.items():
                setattr(request.user.profile, key, value)
            request.user.profile.save()
        
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    @swagger_auto_schema(security=[{'Token': []}])
    def patch(self, request):
        return self.put(request)

class MyOrganizationView(APIView):
  
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        organization = user.profile.organization
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
    @swagger_auto_schema(security=[{'Token': []}])
    def put(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not user.profile.is_admin():
            return Response(
                {'error': 'Only admins can update organization details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization = user.profile.organization
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(security=[{'Token': []}])
    def patch(self, request):
        return self.put(request)


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request):
        user = request.user
        
        if hasattr(user, 'profile') and user.profile.organization:
            organizations = [user.profile.organization]
            serializer = OrganizationSerializer(organizations, many=True)
            return Response(serializer.data)
        
        return Response([], status=status.HTTP_200_OK)


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    @swagger_auto_schema(security=[{'Token': []}])
    def get_user_organization(self, request, pk):
        
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return None
        
        if str(user.profile.organization.id) != str(pk):
            return None
        
        return user.profile.organization
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request, pk):
        organization = self.get_user_organization(request, pk)
        
        if not organization:
            return Response(
                {'error': 'Organization not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
    @swagger_auto_schema(security=[{'Token': []}])
    def put(self, request, pk):
        organization = self.get_user_organization(request, pk)
        
        if not organization:
            return Response(
                {'error': 'Organization not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not request.user.profile.is_admin():
            return Response(
                {'error': 'Only admins can update organization details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrganizationSerializer(organization, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(security=[{'Token': []}])
    def patch(self, request, pk):
        organization = self.get_user_organization(request, pk)
        
        if not organization:
            return Response(
                {'error': 'Organization not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not request.user.profile.is_admin():
            return Response(
                {'error': 'Only admins can update organization details'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(security=[{'Token': []}])
    def delete(self, request, pk):
     
        organization = self.get_user_organization(request, pk)
        
        if not organization:
            return Response(
                {'error': 'Organization not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        if not request.user.profile.is_admin():
            return Response(
                {'error': 'Only admins can delete organization'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationUsersView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request, pk):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if str(user.profile.organization.id) != str(pk):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization = user.profile.organization
        users = User.objects.filter(profile__organization=organization)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class OrganizationCustomersView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request, pk):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if str(user.profile.organization.id) != str(pk):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization = user.profile.organization
        customers = Customer.objects.filter(organization=organization)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated, CanManageCustomers]
    @swagger_auto_schema(security=[{'Token': []}],
        responses={200: CustomerSerializer(many=True)},
        operation_description="List customers of logged-in user's organization."
    )
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        customers = Customer.objects.filter(organization=user.profile.organization)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(security=[{'Token': []}],
        request_body=CustomerSerializer,
        responses={201: CustomerSerializer},
        operation_description="Create a new customer."
    )
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You must belong to an organization to create customers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CustomerSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember, CanManageCustomers]
    
    @swagger_auto_schema(security=[{'Token': []}])
    def get_customer(self, request, pk):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return None
        
        try:
            customer = Customer.objects.get(
                pk=pk,
                organization=user.profile.organization
            )
            return customer
        except Customer.DoesNotExist:
            return None
    @swagger_auto_schema(security=[{'Token': []}],
        responses={200: CustomerDetailSerializer}
    )
    def get(self, request, pk):
        customer = self.get_customer(request, pk)
        
        if not customer:
            return Response(
                {'error': 'Customer not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CustomerDetailSerializer(customer)
        return Response(serializer.data)
    
    @swagger_auto_schema(security=[{'Token': []}],
        request_body=CustomerSerializer,
        responses={200: CustomerSerializer}
    )
    def put(self, request, pk):
        customer = self.get_customer(request, pk)
        
        if not customer:
            return Response(
                {'error': 'Customer not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CustomerSerializer(customer, data=request.data, partial=False, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(security=[{'Token': []}],
        request_body=CustomerSerializer,
        responses={200: CustomerSerializer}
    )
    def patch(self, request, pk):
        customer = self.get_customer(request, pk)
        
        if not customer:
            return Response(
                {'error': 'Customer not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CustomerSerializer(customer, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(security=[{'Token': []}],
        responses={204: "Customer deleted"}
    )
    def delete(self, request, pk):
        customer = self.get_customer(request, pk)
        
        if not customer:
            return Response(
                {'error': 'Customer not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerByStatusView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}],
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter customers by status",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: CustomerSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        status_filter = request.query_params.get('status', None)
        customers = Customer.objects.filter(organization=user.profile.organization)
        
        if status_filter:
            customers = customers.filter(status=status_filter)
        
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


class CustomerChangeStatusView(APIView):
    permission_classes = [IsAuthenticated, CanManageCustomers]
    @swagger_auto_schema(security=[{'Token': []}])
    def post(self, request, pk):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            customer = Customer.objects.get(
                pk=pk,
                organization=user.profile.organization
            )
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_status = request.data.get('status')
        
        if new_status not in dict(Customer.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer.status = new_status
        customer.save()
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

class UserProfileListView(APIView):
  
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response([], status=status.HTTP_200_OK)
        
        profiles = UserProfile.objects.filter(organization=user.profile.organization)
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class UserProfileDetailView(APIView):
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(security=[{'Token': []}])
    def get(self, request, pk):
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.organization:
            return Response(
                {'error': 'You do not belong to any organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            profile = UserProfile.objects.get(
                pk=pk,
                organization=user.profile.organization
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)






