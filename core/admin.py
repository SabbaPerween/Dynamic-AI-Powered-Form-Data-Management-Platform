from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Form, FormSubmission, SubmissionData, ChildRelationship, FormPermission
from django import forms
from .widgets import JSONFieldBuilderWidget 
from .forms import ChildRelationshipForm
from django.utils.html import format_html

# We customize how the User model is displayed
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

class FormAdminForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = '__all__'
        # Tell the 'fields' field to use our custom widget
        widgets = {
            'fields': JSONFieldBuilderWidget(),
        }

# --- UPDATE THE FormAdmin CLASS ---
# core/admin.py

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('form_name', 'status', 'version', 'created_by', 'submission_count', 'updated_at')
    list_filter = ('status', 'created_by', 'created_at')
    search_fields = ('form_name',)
    list_editable = ('status',)
    ordering = ('-updated_at',)
    readonly_fields = ('submission_count',)

    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'
    
class ChildRelationshipInline(admin.TabularInline):
    model = ChildRelationship
    # Use our custom form to get the smart dropdowns
    form = ChildRelationshipForm
    # We are defining relationships FROM this parent, so 'parent_submission' is the foreign key.
    fk_name = 'parent_submission'
    extra = 1 # Show one empty row for adding a new relationship
    verbose_name = "Child-to-Child Relationship"
    verbose_name_plural = "Child-to-Child Relationships"
    class Media:
        # This tells the admin to load this JS file on any page where this inline is present
        js = ('admin/js/relationship_inline_filter.js',)
        
# An advanced registration for Submissions to show data inline
class SubmissionDataInline(admin.TabularInline):
    model = SubmissionData
    extra = 0
    readonly_fields = ('field_name', 'field_value')
    can_delete = False
@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'form', 'submitted_by', 'submitted_at')
    list_filter = ('form', 'submitted_at')
    search_fields = ('data_entries__field_value', 'submitted_by__username')
    ordering = ('-submitted_at',)
    inlines = [SubmissionDataInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('form', 'submitted_by').prefetch_related('data_entries')

# Register your models with the admin site
admin.site.register(ChildRelationship)
# We don't need to register SubmissionData separately as it's shown inline
@admin.register(FormPermission)
class FormPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'form', 'permission_level')
    list_filter = ('permission_level', 'form')
    search_fields = ('user__username', 'form__form_name')
