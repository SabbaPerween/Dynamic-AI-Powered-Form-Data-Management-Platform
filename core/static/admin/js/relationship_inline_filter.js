window.addEventListener('load', function() {
    // This code waits for Django's jQuery to be loaded
    (function($) {
        // Function to update a submission dropdown
        async function updateSubmissionDropdown(formTypeSelect, submissionSelect, parentSubmissionId) {
            const formTypeId = $(formTypeSelect).val();
            const submissionDropdown = $(submissionSelect);

            // Clear current options
            submissionDropdown.empty().append('<option value="">---------</option>');

            if (!formTypeId) {
                return; // Do nothing if no form type is selected
            }

            // Fetch the new options from our API view
            const url = `/api/admin/get-child-submissions/?parent_submission_id=${parentSubmissionId}&child_form_id=${formTypeId}`;
            
            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.error) {
                    console.error("API Error:", data.error);
                    return;
                }

                // Populate the dropdown with new options
                data.forEach(function(item) {
                    submissionDropdown.append($('<option>', {
                        value: item.id,
                        text: item.text
                    }));
                });
            } catch (error) {
                console.error('Failed to fetch child submissions:', error);
            }
        }

        // We need to handle dynamically added forms (when you click "Add another")
        $(document).on('change', 'select[id^="id_childrelationship_set-"][id$="-source_form_type"], select[id^="id_childrelationship_set-"][id$="-target_form_type"]', function() {
            const selectId = $(this).attr('id');
            const prefix = selectId.substring(0, selectId.lastIndexOf('-') + 1);
            
            // Determine if we're updating the source or target
            const isSource = selectId.endsWith('-source_form_type');
            const submissionSelectId = isSource ? `${prefix}source_submission` : `${prefix}target_submission`;
            
            // The parent submission ID is not directly available, so we get it from the URL
            const pathParts = window.location.pathname.split('/').filter(Boolean);
            const parentSubmissionId = pathParts[pathParts.length - 2]; // e.g., /admin/core/formsubmission/5/change/ -> 5

            if (parentSubmissionId) {
                updateSubmissionDropdown(this, `#${submissionSelectId}`, parentSubmissionId);
            }
        });

    })(django.jQuery);
});