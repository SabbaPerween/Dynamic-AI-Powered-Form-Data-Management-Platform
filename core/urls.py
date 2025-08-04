# core/urls.py (NEW FILE)
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    # We use Django's built-in views for login, logout, and password reset.
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', views.custom_logout, name='logout'),
    # Custom registration view
    path('register/', views.register, name='register'),
    
    # Password Reset Flow (This replaces your OTP email logic)
    # path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('password_reset/', 
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), 
        name='password_reset'),
        
    path('password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
        name='password_reset_done'),
        
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
        name='password_reset_confirm'),
        
    path('reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
        name='password_reset_complete'),
    # Main application pages (we will create these views next)
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('forms/create/', views.form_create, name='form_create'),
    path('forms/<int:form_id>/', views.form_detail, name='form_detail'), # The new detail page    
    path('my-submissions/', views.my_submissions, name='my_submissions'), # <-- ADD THIS LINE

    path('fill/', views.internal_form_fill, name='internal_form_fill'), # <-- ADD THIS LINE
    path('forms/<int:form_id>/edit/', views.form_edit, name='form_edit'),
    path('forms/<int:form_id>/analytics/', views.form_analytics, name='form_analytics'), # <-- ADD THIS LINE
    path('forms/<int:form_id>/permissions/', views.manage_form_permissions, name='manage_form_permissions'), # <-- ADD THIS LINE
    path('hierarchy/', views.manage_form_hierarchy, name='manage_form_hierarchy'),
    path('relationships/', views.manage_relationships, name='manage_relationships'),
    path('relationships/create/', views.create_child_relationship, name='create_child_relationship'),
    path('relationships/delete/<int:rel_id>/', views.delete_child_relationship, name='delete_child_relationship'),
    path('forms/<int:form_id>/delete/', views.delete_form, name='form_delete'),
    path('api/admin/get-child-submissions/', views.get_child_submissions_api, name='admin_api_get_child_submissions'),
    # This URL captures the share_token from the link
    path('submit/<uuid:share_token>/', views.form_fill, name='form_fill'), 
    path('api/generate-fields/', views.generate_ai_fields_api, name='api_generate_fields'),
    path('forms/<int:form_id>/export/csv/', views.export_form_data_csv, name='export_csv'),
    path('forms/<int:form_id>/export/excel/', views.export_form_data_excel, name='export_excel'),
    path('forms/<int:form_id>/export/pdf/', views.export_form_data_pdf, name='export_pdf'), 
]