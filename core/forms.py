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
