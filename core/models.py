from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# 1. Custom User Model
# Translates your `users` table. We extend Django's built-in User model
# to add your custom fields. This is best practice.
class CustomUser(AbstractUser):
    # Django's AbstractUser already has: username, email, password, etc.
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    # The 'role' column is now a CharField with choices for data integrity.
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer')
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

# 2. Form Model
# Translates your `forms` metadata table.
class Form(models.Model):
    # THIS IS THE KEY CHANGE: REMOVE unique=True
    form_name = models.CharField(max_length=255) # No longer unique
    
    # All other fields remain the same
    fields = models.JSONField()
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_form = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_forms')
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    version = models.PositiveIntegerField(default=1)
    original_form = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions')

    def __str__(self):
        return f"{self.form_name} (v{self.version})"
    
class FormPermission(models.Model):
    """Links a user to a specific form with a granular permission level."""
    PERMISSION_CHOICES = (
        ('viewer', 'Can View & Submit'),
        ('editor', 'Can Edit Form & View Submissions'),
        ('admin', 'Full Control (Manage Permissions)'),
    )
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='form_permissions')
    permission_level = models.CharField(max_length=10, choices=PERMISSION_CHOICES)

    class Meta:
        # A user can only have one permission level per form
        unique_together = ('form', 'user')
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} has {self.get_permission_level_display()} access to {self.form.form_name}"
# 3. Form Submission Model (NEW - Replaces Dynamic Tables)
# This table stores one record for every time a form is submitted.
class FormSubmission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    # Optional: link to the user who submitted it, if they were logged in.
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    # NEW: If this is a submission to a child form, this links back to the specific parent record.
    parent_submission = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_submissions')

    def __str__(self):
        """
        Tries to find a representative piece of data (like a name or title)
        to display as the string representation of this submission.
        """
        # A list of common field names to check for, in order of preference.
        # We check for lowercase to make the matching case-insensitive.
        REPRESENTATIVE_FIELDS = [
            'name', 'full name', 'full_name', 'title', 'school name', 'school_name',
            'teacher name', 'teacher_name', 'student name', 'student_name', 'username'
        ]

        # Use prefetch_related in the admin for performance.
        # Here we do a direct query.
        for field_name_to_check in REPRESENTATIVE_FIELDS:
            try:
                # Query the related SubmissionData entries.
                # We use __iexact for a case-insensitive match on the field_name.
                data_entry = self.data_entries.get(field_name__iexact=field_name_to_check)
                if data_entry.field_value:
                    # Found a good field, return its value plus the form type for context.
                    return f"{data_entry.field_value} ({self.form.form_name})"
            except SubmissionData.DoesNotExist:
                # This field name wasn't in the submission, so we continue to the next.
                continue
        
        # If no representative field was found after checking all possibilities,
        # fall back to a more informative default.
        return f"Submission for {self.form.form_name} (ID: {self.id})"

# 4. Submission Data Model (NEW - Replaces Dynamic Tables)
# This stores the actual key-value pairs of the submitted data.
class SubmissionData(models.Model):
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='data_entries')
    field_name = models.CharField(max_length=255) # e.g., 'email', 'age'
    field_value = models.TextField() # Stores all values as text; can be cast later.

    class Meta:
        # Ensures a field name is unique for each submission.
        unique_together = ('submission', 'field_name')

    def __str__(self):
        return f"{self.field_name}: {self.field_value[:50]}"

# 5. Child Relationship Model
class ChildRelationship(models.Model):
    # --- NEW FIELD ---
    # Direct link to the parent submission this relationship belongs to.
    parent_submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='child_relationships',
        limit_choices_to={'parent_submission__isnull': True},
        null=True # <-- ADD THIS LINE to allow the field to be empty
    )
    # --- END OF NEW FIELD ---

    source_submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='relationships_as_source',
        help_text="The 'from' side of the relationship (e.g., a Teacher)."
    )
    target_submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='relationships_as_target',
        help_text="The 'to' side of the relationship (e.g., a Student)."
    )
    relationship_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Prevent duplicate relationships
        unique_together = ('parent_submission', 'source_submission', 'target_submission', 'relationship_type')

    def __str__(self):
        return f"{self.source_submission} -> {self.target_submission} ({self.relationship_type})"
