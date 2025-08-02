from django import forms
from django.utils.safestring import mark_safe
import json

class JSONFieldBuilderWidget(forms.Textarea):
    template_name = 'admin/widgets/json_field_builder.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Pass the field types to the template
        context['widget']['field_types'] = [
            "VARCHAR(255)", "TEXTAREA", "EMAIL", "PHONE", "PASSWORD",
            "INTEGER", "FLOAT",
            "SELECT", "RADIO", "MULTISELECT", "CHECKBOX",
            "DATE", "DATETIME"
        ]
        return context

    class Media:
        # This tells the admin to load our custom JS file
        js = ('admin/js/json_field_builder.js',)