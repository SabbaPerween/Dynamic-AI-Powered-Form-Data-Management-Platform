# core/forms.py (NEW FILE)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Form
from .models import ChildRelationship, FormSubmission 
# Registration form that includes our custom fields
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone', 'role')

# Form for creating a new Form's metadata
class FormCreateForm(forms.ModelForm):
    # This form only handles the name and parent, as the fields are built with JS
    class Meta:
        model = Form
        fields = ['form_name', 'parent_form']
        widgets = {
            'form_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_form': forms.Select(attrs={'class': 'form-select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the queryset for the parent_form dropdown
        # to only include forms that are not archived.
        self.fields['parent_form'].queryset = Form.objects.exclude(status='archived')
from .models import ChildRelationship, FormSubmission, Form # Add Form import

class ChildRelationshipForm(forms.ModelForm):
    # --- ADD TWO NEW, NON-MODEL FIELDS ---
    source_form_type = forms.ModelChoiceField(
        queryset=Form.objects.none(), # We will populate this dynamically
        label="Source Form Type",
        required=False
    )
    target_form_type = forms.ModelChoiceField(
        queryset=Form.objects.none(),
        label="Target Form Type",
        required=False
    )

    class Meta:
        model = ChildRelationship
        # Order the fields for a logical UI flow
        fields = [
            'source_form_type', 'source_submission',
            'target_form_type', 'target_submission',
            'relationship_type'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the parent submission object if we are editing an existing relationship
        parent_instance = None
        if self.instance and self.instance.parent_submission_id:
            parent_instance = self.instance.parent_submission
        
        # This part handles the initial population when the form is first loaded
        if parent_instance:
            # Get all form types that are children of the parent's form type
            child_form_types = Form.objects.filter(parent_form=parent_instance.form)
            self.fields['source_form_type'].queryset = child_form_types
            self.fields['target_form_type'].queryset = child_form_types

            # If we are editing an existing record, pre-populate the dropdowns
            if self.instance.source_submission_id:
                self.fields['source_form_type'].initial = self.instance.source_submission.form
                self.fields['source_submission'].queryset = FormSubmission.objects.filter(
                    parent_submission=parent_instance,
                    form=self.instance.source_submission.form
                )

            if self.instance.target_submission_id:
                self.fields['target_form_type'].initial = self.instance.target_submission.form
                self.fields['target_submission'].queryset = FormSubmission.objects.filter(
                    parent_submission=parent_instance,
                    form=self.instance.target_submission.form
                )
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Your Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("No user is associated with this email address.")
        return email

class OTPVerifyForm(forms.Form):
    otp = forms.CharField(
        label="OTP",
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit OTP'})
    )

class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return cleaned_data
