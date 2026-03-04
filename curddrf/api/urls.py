from django.urls import path
from . import views

urlpatterns = [
  
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    path('users/me/', views.CurrentUserView.as_view(), name='current-user'),
    
    path('organizations/my/', views.MyOrganizationView.as_view(), name='my-organization'),
  
    path('organizations/', views.OrganizationListView.as_view(), name='organization-list'),
    
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization-detail'),
    path('organizations/<int:pk>/users/', views.OrganizationUsersView.as_view(), name='organization-users'),
    path('organizations/<int:pk>/customers/', views.OrganizationCustomersView.as_view(), name='organization-customers'),
    
    path('customers/', views.CustomerListCreateView.as_view(), name='customer-list-create'),
    
    path('customers/by-status/', views.CustomerByStatusView.as_view(), name='customer-by-status'),
    
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    
    path('customers/<int:pk>/change-status/', views.CustomerChangeStatusView.as_view(), name='customer-change-status'),
    
 
    path('profiles/', views.UserProfileListView.as_view(), name='userprofile-list'),
    
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='userprofile-detail'),
]
