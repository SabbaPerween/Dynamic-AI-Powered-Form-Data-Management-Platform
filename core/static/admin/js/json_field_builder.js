// This script will be loaded on the Form add/change page in the Django admin.
document.addEventListener('DOMContentLoaded', function() {
    // Find the original JSON textarea and the label
    const originalTextarea = document.querySelector('.json-field-builder-data');
    if (!originalTextarea) {
        console.error("JSON Field Builder: Could not find the target textarea.");
        return;
    }
    const fieldBuilderContainer = document.getElementById('json-field-builder-container');
    if (!fieldBuilderContainer) {
        console.error("JSON Field Builder: Could not find the main container div.");
        return;
    }
    
    // Hide the original textarea, we'll use it as a data store
    originalTextarea.style.display = 'none';
    
    // The data store for our fields
    let formFields = [];
    try {
        const initialData = originalTextarea.value;
        if (initialData) {
            formFields = JSON.parse(initialData);
        }
    } catch (e) {
        console.error("Could not parse initial JSON data:", e);
    }
    
    // --- UI Elements ---
    const fieldsDisplay = document.getElementById('fields-display');
    const fieldNameInput = document.getElementById('builder-field-name');
    const fieldTypeSelect = document.getElementById('builder-field-type');
    const fieldOptionsContainer = document.getElementById('builder-options-container');
    const fieldOptionsInput = document.getElementById('builder-field-options');
    const addFieldBtn = document.getElementById('builder-add-btn');

    // --- Functions ---
    const updateTextarea = () => {
        originalTextarea.value = JSON.stringify(formFields, null, 2); // Pretty print JSON
    };

    const renderFields = () => {
        fieldsDisplay.innerHTML = '';
        if (formFields.length === 0) {
            fieldsDisplay.innerHTML = '<p class="text-muted">No fields defined.</p>';
        } else {
            const list = document.createElement('ul');
            list.className = 'list-group';
            formFields.forEach((field, index) => {
                const item = document.createElement('li');
                item.className = 'list-group-item d-flex justify-content-between align-items-center';
                item.innerHTML = `
                    <span>
                        <strong>${field.name}</strong>
                        <span class="badge bg-secondary rounded-pill ms-2">${field.type}</span>
                        ${field.options ? `<br><small class="text-muted">Options: ${field.options.join(', ')}</small>` : ''}
                    </span>
                    <button type="button" class="btn btn-danger btn-sm" data-index="${index}">Remove</button>
                `;
                list.appendChild(item);
            });
            fieldsDisplay.appendChild(list);
        }
        updateTextarea();
    };

    const addField = () => {
        const name = fieldNameInput.value.trim();
        const type = fieldTypeSelect.value;
        if (!name || !type) {
            alert('Please provide a field name and type.');
            return;
        }

        const newField = { name, type };
        const needsOptions = ['SELECT', 'RADIO', 'MULTISELECT'];
        if (needsOptions.includes(type)) {
            const options = fieldOptionsInput.value.split(',').map(opt => opt.trim()).filter(Boolean);
            if (options.length === 0) {
                alert('Please provide comma-separated options.');
                return;
            }
            newField.options = options;
        }
        
        formFields.push(newField);
        
        // Reset inputs
        fieldNameInput.value = '';
        fieldTypeSelect.value = '';
        fieldOptionsInput.value = '';
        fieldOptionsContainer.style.display = 'none';
        
        renderFields();
    };

    // --- Event Listeners ---
    fieldTypeSelect.addEventListener('change', () => {
        const needsOptions = ['SELECT', 'RADIO', 'MULTISELECT'];
        if (needsOptions.includes(fieldTypeSelect.value)) {
            fieldOptionsContainer.style.display = 'block';
        } else {
            fieldOptionsContainer.style.display = 'none';
        }
    });

    addFieldBtn.addEventListener('click', addField);

    fieldsDisplay.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' && e.target.dataset.index) {
            const indexToRemove = parseInt(e.target.dataset.index, 10);
            formFields.splice(indexToRemove, 1);
            renderFields();
        }
    });

    // --- Initial Render ---
    renderFields();
});