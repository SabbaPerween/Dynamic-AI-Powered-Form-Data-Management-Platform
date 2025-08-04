<h1 align="center">
  Dynamic Form Generator & Analytics Platform
</h1>

<p align="center">
  <strong>A comprehensive Django-based web application for creating, managing, and analyzing complex, dynamic forms with an advanced, aesthetic UI.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Django-5.2-green.svg" alt="Django Version">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-blue.svg" alt="Database">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey.svg" alt="License">
</p>

<p align="center">
  - **[🏛️ Project Philosophy](#-project-philosophy)**
- **[✨ Core Features](#-core-features)**
- **[🏗️ System Architecture](#-system-architecture)**
- **[💻 Technology Stack](#-technology-stack)**
- **[🚀 Local Development Setup](#-local-development-setup)**
- **[🚨 Troubleshooting](#-troubleshooting)**
- **[🔮 Future Work](#-future-work)**
- **[📄 License](#-license)**
</p>

---

## Overview

This project solves the challenge of creating and managing custom data collection forms in a secure, multi-user environment. It moves beyond static forms by providing a complete lifecycle management tool: from AI-assisted creation and an intuitive UI to a powerful administrative backend for data filtering, visualization, and export.

## 🏛️ Project Philosophy

The development of this platform is guided by four core principles:

1.  **Security First:** Every feature, from authentication to database interaction, is designed with security as the foremost priority. We leverage Django's built-in, robust, and industry-standard security features for protection against CSRF, XSS, and SQL injection, including its token-based password reset flow.
2.  **Seamless User Experience:** The interface is designed to be intuitive for all user roles. Complex actions like form creation or data analysis are presented in a clean, aesthetic "command center" UI that feels like a native application.
3.  **Flexible & Scalable Architecture:** The EAV (Entity-Attribute-Value) database schema is designed to handle an infinite number of form variations without requiring database schema changes, ensuring long-term scalability and maintainability.
4.  **Developer-Friendly & Maintainable:** With a clear separation of concerns, comprehensive documentation, and adherence to Django best practices, the codebase is easy to understand, maintain, and extend.

## ✨ Core Features

<details>
  <summary><strong>👤 User & Access Management</strong></summary>
  
  - **Secure Authentication:** Comprehensive login, registration, and password reset system using Django's robust and secure built-in authentication framework.
  - **Secure Password Reset:** Industry-standard, secure, time-sensitive token-based password reset links delivered via SMTP.
  - **Role-Based Access Control (RBAC):**
    - **Admin:** Full control over all forms, data, and users.
    - **Editor:** Can create forms and manage permissions for them.
    - **Viewer:** Can only view and submit data to assigned forms.
  - **Per-Form Permissions:** Form creators can grant specific `view`, `edit`, or `admin` access to other users on a per-form basis.
</details>

<details>
  <summary><strong>📝 Form Lifecycle Management</strong></summary>
  
  - **Intuitive Form Builder:** A clean user interface allows for the manual creation of complex forms with various field types.
  - **AI-Powered Field Generation:** Describe a form's purpose in natural language (e.g., "a patient intake form") and have the AI (Ollama/Llama2) instantly generate the corresponding JSON field structure.
  - **Dynamic Schema:** Creating a form does not alter the database schema, allowing for true on-the-fly form creation and editing.
  - **Advanced Form Relationships:**
    - **Parent-Child Links:** Establish hierarchies between forms (e.g., link "Students" to a "School").
    - **Child-to-Child Links:** Create relationships between records from different child forms under the same parent (e.g., link a "Teacher" record to a "Student" record).
  - **Form Versioning:** Editing a form archives the old version and creates a new one, preserving historical data integrity.
</details>

<details>
  <summary><strong>📊 Data Intelligence & Sharing</strong></summary>

  - **Public Sharing:** Generate unique, secure URLs to share forms publicly for data collection from unauthenticated users.
  - **Interactive Analytics Dashboard:**
    - Visualize data with interactive charts (pies, bars, histograms) from **Plotly**.
    - View Key Performance Indicators (KPIs) like total submissions and child form statistics.
  - **Data Export:** Download filtered submission data in **CSV**, **PDF**, and **Excel** formats.
  - **Powerful Search:** Full-text search within all submissions for a given form.
</details>

## 🏗️ System Architecture

The application is built on a flexible **Entity-Attribute-Value (EAV)** model to avoid the rigid and unscalable approach of creating a new database table for each form.

*   **`core.Form`**: Stores the metadata of a form. The `fields` attribute is a `JSONField` that holds the entire structure (field names, types, options, order).
*   **`core.FormSubmission`**: A single entry representing one submission of a form. It acts as a container linking the `Form`, the `User` (if authenticated), and all its related data.
*   **`core.SubmissionData`**: The EAV table. Each row stores a single piece of data for a submission (`submission_id`, `field_name`, `field_value`). This design allows for infinite form structures without database migrations.

For a detailed technical blueprint, including the database schema and component responsibilities, please see the `core/models.py` file.

## 💻 Technology Stack

| Category      | Technology                                    |
|---------------|-----------------------------------------------|
| **Backend**   | Python 3.11+, Django 5.2+                     |
| **Database**  | PostgreSQL                                    |
| **Frontend**  | HTML5, Bootstrap 5, JavaScript (ES6+)         |
| **JS Libs**   | Plotly.js                                     |
| **Admin**     | Django Jazzmin                                |
| **AI**        | Ollama (Llama 2)                              |
| **Data Tools**| Pandas, FPDF, OpenPyXL                        |
| **Security**  | Django Authentication, CSRF & XSS Protection  |

## 🚀 Local Development Setup

Follow these instructions to set up and run the project locally.

### 1. Prerequisites
- Python 3.9+
- PostgreSQL (v12 or higher)
- **(Optional)** Ollama installed and serving a model (e.g., `ollama run llama2`) if you wish to use the AI features.

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-folder-name>
```

### 3. Create a Virtual Environment
```bash
# For MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```
### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
* This command reads requirements.txt and installs all the necessary Python libraries into your active virtual environment.

### 5. Configure Environment Variables
Create a file named .env in the root of your project and add the following, replacing the placeholder values:

```bash
# --- DATABASE CONFIGURATION ---
DB_NAME=dynamic_forms_db
DB_USER=your_postgres_user
DB_PASSWORD=your_super_secret_password
DB_HOST=localhost
DB_PORT=5432

# --- SMTP EMAIL CONFIGURATION (for Password Reset) ---
# For Gmail, you MUST use a 16-digit "App Password".
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_USER=your.email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
```

### 6. Set Up the Database and Run
```bash
# Apply the database schema
python manage.py migrate

# Create your first admin user
python manage.py createsuperuser

# Start the application
python manage.py runserver
```
Navigate to http://localhost:8000 in your web browser to see the application.

### 🚨 Troubleshooting
<details>
<summary>Common setup issues and solutions.</summary>
PostgreSQL Connection Error: Double-check that your .env credentials are correct and that the PostgreSQL server is running.
TemplateDoesNotExist: This usually means a template file is in the wrong directory. Ensure all auth-related templates are in core/templates/registration/ and app pages are in core/templates/core/. Restarting the server after adding new files can also help.
Password Reset Email Fails: If you see an SMTPAuthenticationError, especially with Gmail, it almost certainly means you need to use a 16-digit App Password, not your regular account password.
Admin Panel AlreadyRegistered Error: This error means a model is being registered twice in core/admin.py. Use the @admin.register() decorator OR admin.site.register(), but not both for the same model.
</details>

### 🔮 Future Work
This platform provides a solid foundation. Future enhancements could include:

* REST API: Expose an API for programmatic form submission and data retrieval.
* Pagination: Implement pagination on the Form Detail page for forms with thousands of submissions.
* AJAX Integration: Use AJAX for searching and permissions to avoid full page reloads.
* Advanced Reporting: Create a dedicated report builder with scheduled email delivery.
* Containerization: Provide Dockerfile and docker-compose.yml for easy deployment.

### 📄 License
This project is licensed under the MIT License. -->
 -->
