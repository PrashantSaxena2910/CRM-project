# Django CRM API Project

A Django REST Framework project for managing Users, Organizations, and Customers with data sharing capabilities.

**Built with Django REST Framework's APIView classes for clean, explicit API endpoints.**

## Features

- **User Management**: Users belong to organizations
- **Organization Management**: Organizations can have multiple users
- **Customer Management**: Customers belong to organizations, users can add customers
- **Data Sharing**: Users can only access customers from their organization
- **REST API**: Complete CRUD operations via Django REST Framework APIView classes
- **Authentication**: Token-based authentication
- **Permissions**: Organization-based access control
- **Multi-tenant Architecture**: Complete data isolation between organizations

## Models Structure

```
User (Django's built-in User extended with Profile)
  └── belongs to → Organization
  
Organization
  ├── has many → Users
  └── has many → Customers
  
Customer
  └── belongs to → Organization
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install django djangorestframework
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get token
- `POST /api/auth/logout/` - Logout

### Organizations
- `GET /api/organizations/my/` - **Get YOUR organization only** (recommended)
- `GET /api/organizations/` - List organizations (returns only your org)
- `GET /api/organizations/{id}/` - Get organization details (only your org)
- `PUT /api/organizations/{id}/` - Update organization (only your org)
- `GET /api/organizations/{id}/users/` - List organization users
- `GET /api/organizations/{id}/customers/` - List organization customers

**Note:** You can ONLY access your own organization. Other organizations are completely hidden.

### Customers
- `GET /api/customers/` - List customers (from your organization ONLY)
- `POST /api/customers/` - Create customer (automatically added to your org)
- `GET /api/customers/{id}/` - Get customer details
- `PUT /api/customers/{id}/` - Update customer
- `DELETE /api/customers/{id}/` - Delete customer

**Note:** All customer operations are restricted to your organization only.

### Users
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/me/` - Update current user profile

## Usage Example

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "pass123", "organization_name": "Acme Corp"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "pass123"}'

# Create a customer (use token from login)
curl -X POST http://localhost:8000/api/customers/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{"name": "John Doe", "email": "johndoe@example.com", "phone": "+1234567890"}'

# List customers from your organization
curl -X GET http://localhost:8000/api/customers/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

## Data Sharing Rules

- **Users can ONLY see and manage customers from their own organization** - complete data isolation
- **Users can ONLY view their own organization details** - no access to other organizations
- **Organization admins can manage all users in their organization**
- **Each customer belongs to exactly one organization**
- **Users automatically get assigned to an organization on registration**
- **Multi-tenant architecture ensures zero data leakage between organizations**

## Project Structure

```
django_crm/
├── manage.py
├── crm_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api/
    ├── models.py            # Organization, UserProfile, Customer
    ├── serializers.py       # DRF serializers
    ├── views.py             # APIView-based views
    ├── urls.py              # URL routing with path()
    ├── permissions.py       # Custom permissions
    ├── admin.py             # Django admin config
    └── tests.py             # Test cases
```

## API Architecture

This project uses **Django REST Framework's APIView classes** for all API endpoints, providing:

- ✅ **Explicit control** over request handling (GET, POST, PUT, PATCH, DELETE)
- ✅ **Clear endpoint definitions** using `path()` in URLs
- ✅ **Granular permissions** per view and method
- ✅ **Easy to understand** code flow for each endpoint
- ✅ **Flexible customization** of response formats and behavior

### Example APIView Structure

```python
class CustomerListCreateView(APIView):
    """API View to list all customers or create a new customer."""
    permission_classes = [IsAuthenticated, CanManageCustomers]
    
    def get(self, request):
        """List all customers from user's organization."""
        # Implementation
        
    def post(self, request):
        """Create a new customer."""
        # Implementation
```

All views inherit from `APIView` and implement methods for HTTP verbs (get, post, put, patch, delete).
