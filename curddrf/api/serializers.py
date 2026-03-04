
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Organization, UserProfile, Customer


class OrganizationSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()
    customers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'description', 'email', 'phone', 'address',
            'is_active', 'created_at', 'updated_at', 'users_count', 'customers_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_users_count(self, obj):
        return obj.get_users_count()
    
    def get_customers_count(self, obj):
        return obj.get_customers_count()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'organization', 'organization_name', 'role', 'phone', 'department',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    organization_id = serializers.IntegerField(required=False, allow_null=True)
    organization_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='user')
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'organization_id', 'organization_name', 'role'
        ]
    
    def validate(self, data):
        
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
    
        if not data.get('organization_id') and not data.get('organization_name'):
            raise serializers.ValidationError({
                "organization": "Must provide either organization_id or organization_name."
            })
        
        return data
    
    def create(self, validated_data):
       
        validated_data.pop('password_confirm')
        organization_id = validated_data.pop('organization_id', None)
        organization_name = validated_data.pop('organization_name', None)
        role = validated_data.pop('role', 'user')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        organization = None
        if organization_id:
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise serializers.ValidationError({"organization_id": "Organization not found."})
        elif organization_name:
            organization, created = Organization.objects.get_or_create(
                name=organization_name,
                defaults={'description': f'Organization for {organization_name}'}
            )
        
        user.profile.organization = organization
        user.profile.role = role
        user.profile.save()
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class CustomerSerializer(serializers.ModelSerializer):
  
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'organization', 'organization_name', 'created_by', 'created_by_name',
            'created_by_username', 'name', 'email', 'phone', 'company', 'address',
            'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'organization']
    
    def create(self, validated_data):
        
        
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not hasattr(user, 'profile') or not user.profile.organization:
                raise serializers.ValidationError({
                    "organization": "User must belong to an organization to create customers."
                })
            
            validated_data['organization'] = user.profile.organization
            validated_data['created_by'] = user
        
        return super().create(validated_data)


class CustomerDetailSerializer(CustomerSerializer):
    organization_details = OrganizationSerializer(source='organization', read_only=True)
    
    class Meta(CustomerSerializer.Meta):
        fields = CustomerSerializer.Meta.fields + ['organization_details']
