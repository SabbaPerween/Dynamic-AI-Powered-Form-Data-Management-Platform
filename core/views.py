from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse  # <--- ADD THIS LINE
from .decorators import user_has_permission
from .forms import CustomUserCreationForm, FormCreateForm
from .models import Form, FormSubmission, SubmissionData, CustomUser, FormPermission, ChildRelationship
from .utils import generate_fields_with_llama, generate_excel_from_dataframe,generate_pdf_from_dataframe
import json
from django.contrib.auth import logout
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import pandas as pd
from django.contrib import messages

def home(request):
    """ The main landing page. """
    return render(request, 'core/home.html')

def register(request):
    """ Handles new user registration. """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Automatically log in the user after registration
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
@login_required
def dashboard(request):
    """
    Displays the advanced, two-column dashboard with a command-center feel.
    """
    user = request.user

    # Base queryset for accessible forms
    if user.role == 'admin':
        accessible_forms = Form.objects.exclude(status='archived').order_by('-updated_at')
    else:
        allowed_form_ids = FormPermission.objects.filter(user=user).values_list('form_id', flat=True)
        creator_condition = Q(created_by=user) & ~Q(status='archived')
        permission_condition = Q(id__in=list(allowed_form_ids))
        accessible_forms = Form.objects.filter(creator_condition | permission_condition).distinct().order_by('-updated_at')

    # Handle search functionality
    search_query = request.GET.get('q', None)
    if search_query:
        accessible_forms = accessible_forms.filter(form_name__icontains=search_query)
    
    # Pre-fetch data for efficiency
    forms_list = accessible_forms.select_related('created_by').prefetch_related('submissions')
    
    # Data for the stat cards and sidebar
    my_submissions_count = FormSubmission.objects.filter(submitted_by=user).count()
    active_forms_count = accessible_forms.filter(status='active').count()
    draft_forms_count = accessible_forms.filter(status='draft').count()

    context = {
        'forms_list': forms_list,
        'total_forms_count': accessible_forms.count(),
        'active_forms_count': active_forms_count,
        'draft_forms_count': draft_forms_count,
        'my_submissions_count': my_submissions_count,
        'search_query': search_query,
        'active_page': 'dashboard', # THIS LINE IS CRUCIAL
    }
    return render(request, 'core/dashboard.html', context)
# @login_required
# def dashboard(request):
#     """
#     Displays the advanced, two-column dashboard with a command-center feel.
#     """
#     user = request.user

#     # Base queryset for accessible forms
#     if user.role == 'admin':
#         accessible_forms = Form.objects.exclude(status='archived').order_by('-updated_at')
#     else:
#         allowed_form_ids = FormPermission.objects.filter(user=user).values_list('form_id', flat=True)
#         creator_condition = Q(created_by=user) & ~Q(status='archived')
#         permission_condition = Q(id__in=list(allowed_form_ids))
#         accessible_forms = Form.objects.filter(creator_condition | permission_condition).distinct().order_by('-updated_at')

#     # Handle search functionality
#     search_query = request.GET.get('q', None)
#     if search_query:
#         accessible_forms = accessible_forms.filter(form_name__icontains=search_query)
    
#     # Pre-fetch data for efficiency
#     forms_list = accessible_forms.select_related('created_by').prefetch_related('submissions')
    
#     # Data for the stat cards and sidebar
#     my_submissions_count = FormSubmission.objects.filter(submitted_by=user).count()
#     active_forms_count = accessible_forms.filter(status='active').count()
#     draft_forms_count = accessible_forms.filter(status='draft').count()

#     context = {
#         'forms_list': forms_list,
#         'total_forms_count': accessible_forms.count(),
#         'active_forms_count': active_forms_count,
#         'draft_forms_count': draft_forms_count,
#         'my_submissions_count': my_submissions_count,
#         'search_query': search_query,
        
#     }
#     return render(request, 'core/dashboard.html', context)

@login_required
def form_create(request):
    """ Handles creation of a new form. """
    if request.method == 'POST':
        form = FormCreateForm(request.POST)
        fields_json = request.POST.get('fields_json')

        if form.is_valid() and fields_json:
            try:
                # The form is valid, but we don't save it directly yet
                new_form = form.save(commit=False) # Create the object in memory
                
                # Now add the data from our custom logic
                new_form.fields = json.loads(fields_json)
                new_form.created_by = request.user
                
                # Now save the complete object to the database
                new_form.save()
                
                # If a parent was selected, the form.save() handles the relationship.
                # Important: The model for FormSubmission also needs to be created.
                # This logic assumes we don't need a DB table right away, but we do.
                # For now, this saves the metadata.
                
                return redirect('form_detail', form_id=new_form.id) # Redirect to the new form's detail page
            except json.JSONDecodeError:
                form.add_error(None, "There was an error processing the form fields.")
        else:
            if not fields_json:
                form.add_error(None, "The form must have at least one field.")
    else:
        form = FormCreateForm()
    
    return render(request, 'core/form_create.html', {'form': form})
@login_required
def form_fill(request, share_token):
    """ Public view for filling out a shared form. Replaces the ?token= logic. """
    # Find the form by its share token or show a 404 error page.
    # It must also be 'active' to be fillable
    form_obj = get_object_or_404(Form, share_token=share_token, status='active')
    
    if request.method == 'POST':
        # Create the main submission record
        submission = FormSubmission.objects.create(
            form=form_obj
            # Note: No `submitted_by` because it's a public form
        )

        # CORRECTED AND ROBUST DATA SAVING LOGIC
        # Iterate through the DEFINED fields to correctly handle all types
        for field in form_obj.fields:
            field_name = field['name']
            field_type = field.get('type')

            # Handle File Uploads
            if field_type == 'FILE':
                if field_name in request.FILES:
                    uploaded_file = request.FILES[field_name]
                    # NOTE: In a production app, you would save this file to a proper
                    # media storage (like S3 or local MEDIA_ROOT) and store its path.
                    # For now, we save the filename and size as a record.
                    SubmissionData.objects.create(
                        submission=submission,
                        field_name=field_name,
                        field_value=f"Uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)"
                    )
                continue # Skip to the next field in the loop

            # Handle standard POST data
            if field_name in request.POST:
                # Handle multi-value fields (e.g., MULTISELECT, checkbox groups)
                # This uses getlist() to capture all selected values.
                if field_type in ['MULTISELECT'] or (field_type == 'CHECKBOX' and 'options' in field):
                    values = request.POST.getlist(field_name)
                    # We store the list of values as a JSON string in the database
                    field_value = json.dumps(values)
                else: # Handle single-value fields (text, radio, single checkbox, etc.)
                    field_value = request.POST.get(field_name)
                
                SubmissionData.objects.create(submission=submission, field_name=field_name, field_value=field_value)
        # END OF CORRECTED LOGIC

        return render(request, 'core/form_submit_success.html', {'form': form_obj})

    # For a GET request, render the form based on its JSON fields
    return render(request, 'core/form_fill.html', {'form': form_obj})
# def form_fill(request, share_token):
#     """ Public view for filling out a shared form. Replaces the ?token= logic. """
#     # Find the form by its share token or show a 404 error page.
#     form_obj = get_object_or_404(Form, share_token=share_token)
    
#     if request.method == 'POST':
#         # Create the main submission record
#         submission = FormSubmission.objects.create(form=form_obj)
        
#         # Loop through the submitted data and save it
#         for key, value in request.POST.items():
#             if key not in ['csrfmiddlewaretoken']: # Ignore the CSRF token
#                 SubmissionData.objects.create(
#                     submission=submission,
#                     field_name=key,
#                     field_value=value
#                 )
#         return render(request, 'core/form_submit_success.html', {'form': form_obj})

    # For a GET request, render the form based on its JSON fields
    # return render(request, 'core/form_fill.html', {'form': form_obj})

# forms_app/views.py

# Add these imports at the top of the file
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import generate_fields_with_llama

# ... (keep all your existing views like home, register, etc.) ...

# NEW VIEW for AI generation
@require_POST  # This view only accepts POST requests
@login_required # Make sure only logged-in users can use the AI
def generate_ai_fields_api(request):
    """An API endpoint to generate form fields using AI."""
    try:
        # Get the description from the POST data sent by the frontend
        data = json.loads(request.body)
        description = data.get('description')

        if not description:
            return JsonResponse({'error': 'Description is required.'}, status=400)

        # Call our utility function
        success, content = generate_fields_with_llama(description)

        if success:
            # The content is already a JSON string, so we can return it directly
            # We parse it and dump it again to ensure it's valid JSON.
            return JsonResponse({'fields': json.loads(content)})
        else:
            # If the AI failed, return an error message
            return JsonResponse({'error': f'AI generation failed: {content}'}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    # forms_app/views.py



@user_has_permission(required_levels=['editor', 'admin'])
@login_required
def export_form_data_csv(request, form_id):
    form_obj = get_object_or_404(Form, pk=form_id)
    
    # This is a simplified data retrieval. We'll improve it.
    submissions = form_obj.submissions.all()
    data = []
    for sub in submissions:
        row = {entry.field_name: entry.field_value for entry in sub.data_entries.all()}
        row['submitted_at'] = sub.submitted_at
        data.append(row)

    if not data:
        # Handle case with no submissions
        return HttpResponse("No data to export.", status=404)

    df = pd.DataFrame(data)
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{form_obj.form_name}.csv"'},
    )
    df.to_csv(path_or_buf=response, index=False)
    return response

@user_has_permission(required_levels=['editor', 'admin'])
@login_required
def export_form_data_excel(request, form_id):
    form_obj = get_object_or_404(Form, pk=form_id)
    
    submissions = form_obj.submissions.all()
    data = []
    for sub in submissions:
        row = {entry.field_name: entry.field_value for entry in sub.data_entries.all()}
        row['submitted_at'] = sub.submitted_at
        data.append(row)

    if not data:
        return HttpResponse("No data to export.", status=404)

    df = pd.DataFrame(data)
    excel_bytes = generate_excel_from_dataframe(df)

    response = HttpResponse(
        excel_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{form_obj.form_name}.xlsx"'},
    )
    return response
# Add this new view to core/views.py

@login_required
def my_submissions(request):
    """
    Displays a list of all form submissions made by the currently logged-in user.
    """
    user_submissions = FormSubmission.objects.filter(
        submitted_by=request.user
    ).select_related('form').order_by('-submitted_at')

    context = {
        'submissions': user_submissions,
    }
    return render(request, 'core/my_submissions.html', context)

@user_has_permission(required_levels=['viewer', 'editor', 'admin'])
@login_required
def form_detail(request, form_id):
    form_obj = get_object_or_404(Form, pk=form_id)
    
    # --- MODIFICATION: PRE-FETCH THE PARENT SUBMISSION ---
    # We use select_related to efficiently get the parent submission data in the same query.
    submissions = form_obj.submissions.select_related(
        'parent_submission'
    ).prefetch_related('data_entries').order_by('-submitted_at')
    
    # Get the header names from the form's JSON definition
    headers = [field['name'] for field in form_obj.fields]

    # --- NEW: ADD "LINKED PARENT" TO HEADERS IF THIS IS A CHILD FORM ---
    if form_obj.parent_form:
        headers.append('Linked Parent')
    
    headers.append('Submitted At') # Add our own column

    # Process submissions into a list of lists for easy rendering in the template
    processed_submissions = []
    for sub in submissions:
        # Create a dictionary with default empty values for all headers
        row_dict = {header: "" for header in headers}
        for entry in sub.data_entries.all():
            if entry.field_name in row_dict:
                row_dict[entry.field_name] = entry.field_value
        
        # --- NEW: POPULATE THE "LINKED PARENT" DATA ---
        if form_obj.parent_form and sub.parent_submission:
            # The str(sub.parent_submission) will use our intelligent __str__ method
            # to display a user-friendly name, e.g., "TCS (Company Form)"
            row_dict['Linked Parent'] = str(sub.parent_submission)
        
        row_dict['Submitted At'] = sub.submitted_at.strftime('%Y-%m-%d %H:%M')
        
        # Ensure the row is ordered according to the headers
        ordered_row = [row_dict[header] for header in headers]
        processed_submissions.append(ordered_row)

    # ... (The rest of the view, including context, remains the same) ...
    all_users = CustomUser.objects.all()
    full_share_url = None
    if form_obj.share_token:
        relative_url = reverse('form_fill', kwargs={'share_token': form_obj.share_token})
        full_share_url = request.build_absolute_uri(relative_url)

    user_is_form_admin = False
    if request.user.role == 'admin' or form_obj.created_by == request.user or FormPermission.objects.filter(form=form_obj, user=request.user, permission_level='admin').exists():
        user_is_form_admin = True
        
    context = {
        'form': form_obj,
        'headers': headers,
        'submissions_data': processed_submissions,
        'full_share_url': full_share_url,
        'all_users': all_users,
        'user_is_form_admin': user_is_form_admin,
    }
    return render(request, 'core/form_detail.html', context)
@login_required
def internal_form_fill(request):
    """
    A view for authenticated users to fill out any form.
    Handles parent-child relationships.
    """
    all_forms = Form.objects.all()
    selected_form = None
    parent_records = None
    selected_parent_info = None
    
    # Get the form_id from the URL to determine which form to show
    form_id = request.GET.get('form_id')
    if form_id:
        selected_form = get_object_or_404(Form, pk=form_id)
        
        # If this is a child form, get its parent's records for the dropdown
        if selected_form.parent_form:
            parent_submissions = FormSubmission.objects.filter(form=selected_form.parent_form)
            # The __str__ method on FormSubmission now handles user-friendly display text
            parent_records = [{'id': sub.id, 'display_text': str(sub)} for sub in parent_submissions]

            # --- NEW LOGIC: GET SELECTED PARENT INFO ---
            # Check if a specific parent has been selected from the dropdown
            selected_parent_id = request.GET.get('parent_id')
            if selected_parent_id:
                try:
                    parent_submission = FormSubmission.objects.get(pk=selected_parent_id)
                    # Extract its data into a simple dictionary for display in the template
                    selected_parent_info = {
                        'id': parent_submission.id,
                        'form_name': parent_submission.form.form_name,
                        'data': {entry.field_name: entry.field_value for entry in parent_submission.data_entries.all()}
                    }
                except FormSubmission.DoesNotExist:
                    pass # Ignore if an invalid ID is passed
            # --- END OF NEW LOGIC ---

    if request.method == 'POST':
        form_to_submit_id = request.POST.get('form_id')
        parent_submission_id = request.POST.get('parent_submission_id')
        
        if not form_to_submit_id:
            messages.error(request, "Could not identify the form being submitted.")
            return redirect('dashboard')

        form_to_submit = get_object_or_404(Form, pk=form_to_submit_id)
        submission = FormSubmission.objects.create(
            form=form_to_submit,
            submitted_by=request.user,
            parent_submission_id=parent_submission_id if parent_submission_id else None
        )

        # CORRECTED AND ROBUST DATA SAVING LOGIC
        for field in form_to_submit.fields:
            field_name = field['name']
            field_type = field.get('type')

            # Handle file uploads
            if field_type == 'FILE' and field_name in request.FILES:
                uploaded_file = request.FILES[field_name]
                SubmissionData.objects.create(
                    submission=submission, field_name=field_name,
                    field_value=f"Uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)"
                )
                continue

            # Handle standard POST data
            if field_name in request.POST:
                # Handle multi-value fields
                if field_type in ['MULTISELECT'] or (field_type == 'CHECKBOX' and 'options' in field):
                    values = request.POST.getlist(field_name)
                    field_value = json.dumps(values)
                else: # Handle single-value fields
                    field_value = request.POST.get(field_name)
                
                SubmissionData.objects.create(submission=submission, field_name=field_name, field_value=field_value)
        # END OF CORRECTED LOGIC
        
        messages.success(request, "Submission saved successfully!")
        return redirect('form_detail', form_id=form_to_submit.id)
    context = {
        'all_forms': all_forms,
        'selected_form': selected_form,
        'parent_records': parent_records,
        'selected_parent_info': selected_parent_info, # <-- Pass new data to template
        'selected_parent_id': request.GET.get('parent_id'), # Pass the ID back to pre-select the dropdown
    }
    return render(request, 'core/internal_form_fill.html', context)

@user_has_permission(required_levels=['editor', 'admin'])
@login_required
def form_edit(request, form_id):
    """
    Handles editing a form and creating a new version.
    """
    original_form = get_object_or_404(Form, pk=form_id)

    if request.method == 'POST':
        # We still use the form for validation, but handle saving manually
        form_meta = FormCreateForm(request.POST) 
        fields_json = request.POST.get('fields_json')

        if form_meta.is_valid() and fields_json:
            # --- CORRECTED VERSIONING LOGIC ---
            
            # 1. Archive the old form version.
            original_form.status = 'archived'
            original_form.save()

            # 2. Create a new Form instance for the new version.
            # We explicitly set its properties rather than relying on form.save().
            new_version_form = Form()

            # 3. Copy properties from the submitted form meta and the original form.
            # The name and parent can be changed in the edit form.
            new_version_form.form_name = form_meta.cleaned_data['form_name']
            new_version_form.parent_form = form_meta.cleaned_data['parent_form']
            
            # These properties are inherited or calculated.
            new_version_form.created_by = request.user
            new_version_form.fields = json.loads(fields_json)
            new_version_form.version = original_form.version + 1
            new_version_form.original_form = original_form.original_form or original_form
            new_version_form.status = 'active' # The new version is always active.
            
            # 4. Save the new version to the database. This will now succeed.
            new_version_form.save()

            messages.success(request, f"Successfully created version {new_version_form.version} of '{new_version_form.form_name}'.")
            return redirect('form_detail', form_id=new_version_form.id)
        
        else:
            # If the form is not valid, add an error message
            messages.error(request, "Please correct the errors below.")
            # We fall through to re-render the page with the errors
            form = form_meta # Pass the invalid form back to the template
    
    else:
        # GET request: pre-populate the form with the original form's data
        initial_data = {
            'form_name': original_form.form_name,
            'parent_form': original_form.parent_form,
        }
        form = FormCreateForm(initial=initial_data)

    context = {
        'form': form,
        'editing_form': original_form,
        'fields_as_json': json.dumps(original_form.fields),
    }
    return render(request, 'core/form_edit.html', context)
# core/views.py
import plotly.express as px
import pandas as pd
from django.db.models import Count
from django.db.models import Q 

@user_has_permission(required_levels=['editor', 'admin'])
@login_required
def form_analytics(request, form_id):
    """
    Displays an analytics dashboard with dynamic charts for a form.
    """
    form_obj = get_object_or_404(Form, pk=form_id)
    submissions = form_obj.submissions.prefetch_related('data_entries').order_by('-submitted_at')

    # --- DATA PREPARATION ---
    # Pivot the submission data into a pandas DataFrame, which is ideal for analytics.
    data = []
    for sub in submissions:
        # Create a dictionary for each row
        row = {entry.field_name: entry.field_value for entry in sub.data_entries.all()}
        row['submitted_at'] = sub.submitted_at
        data.append(row)

    if not data:
        # If there are no submissions, just render the page with a message
        return render(request, 'core/form_analytics.html', {'form': form_obj, 'charts': []})

    df = pd.DataFrame(data)

    # --- CHART GENERATION ---
    charts = []
    # Get the field types from the form's definition to decide what kind of chart to make
    field_definitions = {field['name']: field for field in form_obj.fields}

    for col in df.columns:
        if col == 'submitted_at' or col not in field_definitions:
            continue # Skip metadata columns

        field_type = field_definitions[col].get('type')
        chart_div = None

        try:
            # Chart for NUMERIC data (Integers, Floats)
            if field_type in ['INTEGER', 'FLOAT']:
                # Convert column to numeric, coercing errors to NaN (Not a Number)
                numeric_series = pd.to_numeric(df[col], errors='coerce').dropna()
                if not numeric_series.empty:
                    fig = px.histogram(numeric_series, x=col, title=f'Distribution of {col}', template='plotly_white')
                    chart_div = fig.to_html(full_html=False, include_plotlyjs='cdn')

            # Chart for CATEGORICAL data (Select, Radio)
            elif field_type in ['SELECT', 'RADIO']:
                # Count the occurrences of each option
                counts = df[col].value_counts()
                if not counts.empty:
                    fig = px.pie(values=counts.values, names=counts.index, title=f'Distribution of {col}', hole=0.3)
                    chart_div = fig.to_html(full_html=False, include_plotlyjs='cdn')

            # Chart for DATE data
            elif field_type in ['DATE', 'DATETIME']:
                # Convert to datetime and group by day
                date_series = pd.to_datetime(df[col], errors='coerce').dropna().dt.date
                if not date_series.empty:
                    counts = date_series.value_counts().sort_index()
                    fig = px.bar(x=counts.index, y=counts.values, title=f'Submissions by Date for {col}', labels={'x':'Date', 'y':'Count'})
                    chart_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            if chart_div:
                charts.append(chart_div)
        
        except Exception as e:
            # This will catch any errors during chart generation for a specific column
            print(f"Could not generate chart for column '{col}': {e}")


    # --- CHILD DATA ROLL-UP ---
    child_form_stats = []
    child_forms = form_obj.child_forms.filter(status='active') # Get all child forms
    if child_forms.exists():
        for child_form in child_forms:
            # Count submissions for each child form that are linked to this parent form's submissions
            count = FormSubmission.objects.filter(
                form=child_form,
                parent_submission__form=form_obj
            ).count()
            child_form_stats.append({'name': child_form.form_name, 'count': count})
            
    context = {
        'form': form_obj,
        'charts': charts,
        'total_submissions': len(df),
        'child_form_stats': child_form_stats,
    }
    return render(request, 'core/form_analytics.html', context)

@user_has_permission(required_levels=['admin']) # Only form admins can manage permissions
@login_required
def manage_form_permissions(request, form_id):
    form = get_object_or_404(Form, pk=form_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        permission_level = request.POST.get('permission_level')
        
        if not user_id:
            # Add an error message to be displayed to the user
            messages.error(request, 'You must select a user.')
            return redirect('form_detail', form_id=form.id)

        try:
            # Ensure the user_id is a valid integer and the user exists
            user_to_update = get_object_or_404(CustomUser, pk=int(user_id))
        except (ValueError, TypeError):
            # This happens if user_id is not a number
            messages.error(request, 'An invalid user was selected.')
            return redirect('form_detail', form_id=form.id)
        # --- END OF IMPROVED LOGIC ---

        if permission_level == 'none':
            # If 'none' is selected, delete the permission entry
            FormPermission.objects.filter(form=form, user=user_to_update).delete()
            messages.success(request, f'Access for {user_to_update.username} has been revoked.')
        else:
            # Otherwise, create or update the permission
            permission, created = FormPermission.objects.update_or_create(
                form=form,
                user=user_to_update,
                defaults={'permission_level': permission_level}
            )
            if created:
                messages.success(request, f'Permission granted to {user_to_update.username}.')
            else:
                messages.success(request, f'Permission for {user_to_update.username} updated.')
    
    return redirect('form_detail', form_id=form.id)
@user_has_permission(required_levels=['editor', 'admin'])
@login_required
def export_form_data_pdf(request, form_id):
    """
    Fetches form submission data and returns it as a downloadable PDF file.
    """
    form_obj = get_object_or_404(Form, pk=form_id)
    
    # 1. Fetch and pivot data into a DataFrame (same logic as CSV/Excel)
    submissions = form_obj.submissions.prefetch_related('data_entries').order_by('submitted_at')
    data = []
    headers = [field['name'] for field in form_obj.fields] # Get headers from form definition
    
    for sub in submissions:
        row_dict = {header: "" for header in headers} # Initialize with all possible headers
        for entry in sub.data_entries.all():
            if entry.field_name in row_dict:
                row_dict[entry.field_name] = entry.field_value
        data.append(row_dict)

    if not data:
        return HttpResponse("No data to export.", status=404)
    
    df = pd.DataFrame(data, columns=headers) # Ensure column order is correct

    # 2. Call the utility function to generate the PDF bytes
    try:
        pdf_bytes = generate_pdf_from_dataframe(df, title=form_obj.form_name)
    except Exception as e:
        # Handle potential errors during PDF generation
        print(f"Error generating PDF: {e}")
        return HttpResponse("An error occurred while generating the PDF.", status=500)

    # 3. Create the HttpResponse
    response = HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{form_obj.form_name}_submissions.pdf"'},
    )
    return response
# core/views.py
@login_required
def create_child_relationship(request):
    """
    Handles the POST request to create a new ChildRelationship from the dashboard.
    """
    if request.method != 'POST':
        return redirect('dashboard')

    parent_submission_id = request.POST.get('parent_submission_id')
    source_submission_id = request.POST.get('source_submission_id')
    target_submission_id = request.POST.get('target_submission_id')
    relationship_type = request.POST.get('relationship_type')

    if not all([parent_submission_id, source_submission_id, target_submission_id, relationship_type]):
        messages.error(request, "All fields are required to create a relationship.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    if source_submission_id == target_submission_id:
        messages.error(request, "A record cannot be related to itself.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    try:
        # --- THIS IS THE FIX ---
        # 1. Fetch the parent submission object first.
        parent_submission = get_object_or_404(FormSubmission, pk=parent_submission_id)

        # 2. Create the relationship using the object.
        ChildRelationship.objects.create(
            parent_submission=parent_submission, # Use the object directly
            source_submission_id=source_submission_id,
            target_submission_id=target_submission_id,
            relationship_type=relationship_type.strip()
        )
        messages.success(request, "Relationship created successfully!")

        # 3. Now we can get the parent_form_id from the object for the redirect.
        parent_form_id = parent_submission.form.id

        # --- REDIRECT LOGIC ---
        # The target URL should be the dashboard, not manage_relationships
        redirect_url = f"{reverse('dashboard')}?parent_form_id={parent_form_id}&parent_submission_id={parent_submission_id}"
        return redirect(redirect_url)
        # --- END OF FIX ---

    except FormSubmission.DoesNotExist:
        messages.error(request, "The selected parent record does not exist.")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Could not create relationship. It might already exist.")
        # Redirect back to the previous page on error
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
# @login_required
# def create_child_relationship(request):
#     """
#     Handles the POST request to create a new ChildRelationship.
#     """
#     if request.method != 'POST':
#         # This view should only ever be accessed via POST
#         return redirect('dashboard')

#     parent_submission_id = request.POST.get('parent_submission_id')
#     source_submission_id = request.POST.get('source_submission_id')
#     target_submission_id = request.POST.get('target_submission_id')
#     relationship_type = request.POST.get('relationship_type')

#     # Basic validation
#     if not all([parent_submission_id, source_submission_id, target_submission_id, relationship_type]):
#         messages.error(request, "All fields are required to create a relationship.")
#         return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

#     if source_submission_id == target_submission_id:
#         messages.error(request, "A record cannot be related to itself.")
#         return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

#     try:
#         # Create the relationship
#         ChildRelationship.objects.create(
#             parent_submission_id=parent_submission_id,
#             source_submission_id=source_submission_id,
#             target_submission_id=target_submission_id,
#             relationship_type=relationship_type.strip()
#         )
#         messages.success(request, "Relationship created successfully!")
#     except Exception as e:
#         messages.error(request, f"Could not create relationship. It might already exist. Error: {e}")

#     # Redirect back to the dashboard, preserving the filter
#     redirect_url = f"{reverse('manage_relationships')}?parent_form_id={parent_form_id}&parent_submission_id={parent_submission_id}"
#     return redirect(redirect_url)

@login_required
def manage_form_hierarchy(request):
    """
    A view to set the parent for any given form.
    """
    if request.method == 'POST':
        child_form_id = request.POST.get('child_form_id')
        parent_form_id = request.POST.get('parent_form_id')

        # Use get_object_or_404 to handle cases where an invalid ID is submitted
        child_form = get_object_or_404(Form, pk=child_form_id)
        
        if parent_form_id:
            # If a parent ID was provided, find that form
            parent_form = get_object_or_404(Form, pk=parent_form_id)
            if child_form.id == parent_form.id:
                # Prevent a form from being its own parent
                messages.error(request, "A form cannot be its own parent.")
            else:
                child_form.parent_form = parent_form
                child_form.save()
                messages.success(request, f"'{child_form.form_name}' is now a child of '{parent_form.form_name}'.")
        else:
            # If "None" was selected (parent_form_id is empty), remove the parent link
            if child_form.parent_form:
                messages.success(request, f"'{child_form.form_name}' is no longer a child form.")
                child_form.parent_form = None
                child_form.save()
        
        return redirect('manage_form_hierarchy')

    # For a GET request
    # Get all forms that could be children (all non-archived forms), pre-fetching their parent for efficiency
    all_forms = Form.objects.exclude(status='archived').select_related('parent_form').order_by('form_name')
    
    # The list of potential parents is the same list
    potential_parents = all_forms

    context = {
        'all_forms': all_forms,
        'potential_parents': potential_parents,
    }
    return render(request, 'core/manage_form_hierarchy.html', context)
# core/views.py

@login_required
def get_child_submissions_api(request):
    """
    An API endpoint for the admin to fetch child submissions for a given parent and form type.
    Returns data as JSON.
    """
    parent_submission_id = request.GET.get('parent_submission_id')
    child_form_id = request.GET.get('child_form_id')

    if not parent_submission_id or not child_form_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    submissions = FormSubmission.objects.filter(
        parent_submission_id=parent_submission_id,
        form_id=child_form_id
    )
    
    # Format the data for the dropdown
    data = [
        {'id': sub.id, 'text': str(sub)} for sub in submissions
    ]
    
    return JsonResponse(data, safe=False)
# core/views.py

@login_required
def manage_relationships(request):
    """
    A dedicated page for viewing, creating, and deleting child-to-child relationships.
    """
    # --- This logic is the same as the top of the dashboard view ---
    parent_ids_in_use = Form.objects.exclude(parent_form__isnull=True).values_list('parent_form_id', flat=True).distinct()
    parent_forms = Form.objects.filter(id__in=parent_ids_in_use).exclude(status='archived')
    
    selected_parent_form_id = request.GET.get('parent_form_id')
    selected_parent_submission_id = request.GET.get('parent_submission_id')
    
    parent_submissions = None
    relationships = None
    child_submissions = None
    child_form_types = None
    selected_parent_submission = None

    if selected_parent_form_id:
        parent_submissions = FormSubmission.objects.filter(form_id=selected_parent_form_id)

    if selected_parent_submission_id:
        selected_parent_submission = get_object_or_404(FormSubmission, pk=selected_parent_submission_id)
        relationships = ChildRelationship.objects.filter(parent_submission=selected_parent_submission).select_related('source_submission', 'target_submission')
        child_submissions = FormSubmission.objects.filter(parent_submission=selected_parent_submission).select_related('form')
        child_form_types = Form.objects.filter(parent_form=selected_parent_submission.form)

    context = {
        'parent_forms': parent_forms,
        'selected_parent_form_id': selected_parent_form_id,
        'parent_submissions': parent_submissions,
        'selected_parent_submission_id': selected_parent_submission_id,
        'selected_parent_submission': selected_parent_submission,
        'relationships': relationships,
        'child_submissions': child_submissions,
        'child_form_types': child_form_types,
    }
    return render(request, 'core/manage_relationships.html', context)


@login_required
def delete_child_relationship(request, rel_id):
    """
    Handles the deletion of a single ChildRelationship object.
    """
    # Ensure the user has permission to delete (simplified check for now)
    relationship_to_delete = get_object_or_404(ChildRelationship, pk=rel_id)
    
    # Preserve the parent context for the redirect
    parent_submission_id = relationship_to_delete.parent_submission.id
    parent_form_id = relationship_to_delete.parent_submission.form.id
    
    if request.method == 'POST':
        relationship_to_delete.delete()
        messages.success(request, "Relationship deleted successfully.")
    
    # Redirect back to the management page with the same parent selected
    return redirect(f"{reverse('manage_relationships')}?parent_form_id={parent_form_id}&parent_submission_id={parent_submission_id}")

@require_POST  # Ensures this view can only be accessed via POST
@login_required
def delete_form(request, form_id):
    """
    Archives a form and all of its versions. This is a "soft delete".
    """
    form_to_delete = get_object_or_404(Form, pk=form_id)

    # --- Permission Check ---
    # Check if the user is the creator, a global admin, or has specific 'admin' permission for this form.
    is_creator = form_to_delete.created_by == request.user
    is_global_admin = request.user.role == 'admin'
    has_form_admin_perm = FormPermission.objects.filter(
        form=form_to_delete, 
        user=request.user, 
        permission_level='admin'
    ).exists()

    if not (is_creator or is_global_admin or has_form_admin_perm):
        messages.error(request, "You do not have permission to delete this form.")
        return redirect('form_detail', form_id=form_id)

    # --- Archiving Logic ---
    # Find the root form (version 1)
    root_form = form_to_delete.original_form or form_to_delete

    # Find all forms that are either the root form itself or are versions of it
    forms_to_archive = Form.objects.filter(
        Q(id=root_form.id) | Q(original_form=root_form)
    )

    # Archive all found versions in a single, efficient database query
    updated_count = forms_to_archive.update(status='archived')

    messages.success(request, f"Successfully archived '{root_form.form_name}' and its {updated_count - 1} other version(s).")
    
    # Redirect to the dashboard since the detail page is for active forms
    return redirect('dashboard')
# core/views.py

# ... (imports and other views are unchanged) ...

# ... (the rest of your views.py file) ...
# def password_reset_request(request):
#     if request.method == "POST":
#         form = PasswordResetRequestForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             user = CustomUser.objects.get(email__iexact=email)
            
#             # Generate OTP
#             otp = random.randint(100000, 999999)
#             user.otp = str(otp)
#             user.otp_expires_at = timezone.now() + timedelta(minutes=10) # OTP is valid for 10 minutes
#             user.save()

#             # Store user's ID in session to use on the next page
#             request.session['password_reset_user_id'] = user.id

#             # Send OTP email
#             send_mail(
#                 'Your Password Reset OTP',
#                 f'Your One-Time Password (OTP) for resetting your password is: {otp}\nIt will expire in 10 minutes.',
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#             )
            
#             messages.success(request, 'An OTP has been sent to your email address.')
#             return redirect('password_reset_verify')
#     else:
#         form = PasswordResetRequestForm()
    
#     return render(request, 'registration/password_reset_request.html', {'form': form})


# def password_reset_verify(request):
#     user_id = request.session.get('password_reset_user_id')
#     if not user_id:
#         messages.error(request, "Session expired or invalid request. Please start over.")
#         return redirect('password_reset_request')

#     user = get_object_or_404(CustomUser, id=user_id)

#     if request.method == "POST":
#         form = OTPVerifyForm(request.POST)
#         if form.is_valid():
#             otp_entered = form.cleaned_data['otp']
            
#             # Check if OTP is correct and not expired
#             if user.otp == otp_entered and user.otp_expires_at > timezone.now():
#                 # OTP is valid, mark it as used
#                 user.otp = None
#                 user.otp_expires_at = None
#                 user.save()
                
#                 # Mark in session that OTP was verified
#                 request.session['otp_verified'] = True
#                 messages.success(request, "OTP verified successfully. You can now set a new password.")
#                 return redirect('password_reset_confirm')
#             else:
#                 messages.error(request, "Invalid or expired OTP.")
#     else:
#         form = OTPVerifyForm()

#     return render(request, 'registration/password_reset_verify.html', {'form': form})


# def password_reset_confirm(request):
#     user_id = request.session.get('password_reset_user_id')
#     otp_verified = request.session.get('otp_verified')

#     if not user_id or not otp_verified:
#         messages.error(request, "Invalid request. Please start the password reset process again.")
#         return redirect('password_reset_request')

#     user = get_object_or_404(CustomUser, id=user_id)

#     if request.method == "POST":
#         form = SetNewPasswordForm(request.POST)
#         if form.is_valid():
#             user.set_password(form.cleaned_data['new_password1'])
#             user.save()
            
#             # Clean up the session
#             del request.session['password_reset_user_id']
#             del request.session['otp_verified']

#             messages.success(request, "Your password has been reset successfully. Please log in.")
#             return redirect('login')
#     else:
#         form = SetNewPasswordForm()

#     return render(request, 'registration/password_reset_confirm.html', {'form': form})

@require_POST # Ensures this view can only be accessed via POST
def custom_logout(request):
    """
    Logs the user out of all sessions and redirects to the home page.
    """
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('home')