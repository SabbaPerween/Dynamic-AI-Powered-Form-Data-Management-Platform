<h1 align="center">
  <img src="https://via.placeholder.com/100x100.png?text=DFG" alt="Project Logo" width="100"/><br/>
  Dynamic Form Generator & Analytics Platform
</h1>

<p align="center">
  <strong>A full-stack Django application for creating, managing, and analyzing complex, dynamic forms with an advanced, aesthetic UI.</strong>
</p>

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-architecture-overview">Architecture</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-local-development-setup">Setup</a> •
  <a href="#-application-workflow">Usage Guide</a> •
  <a href="#-api-endpoints">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

This project provides a robust solution for scenarios where form structures are not static. It replaces the need for creating new database tables for every form type by using a flexible EAV (Entity-Attribute-Value) model. Key functionalities include a drag-and-drop form builder, AI-powered field generation, complex data relationship modeling, and a built-in analytics dashboard, all wrapped in a modern, command-center-style interface.

## ✨ Key Features

<details>
  <summary><strong>📝 Dynamic Form Creation</strong></summary>
  
  - **Drag-and-Drop UI:** Powered by `SortableJS`, users can intuitively reorder form fields.
  - **AI Field Generation:** Leverages a local Ollama instance to interpret natural language descriptions (e.g., "a patient intake form") and generate a complete JSON field structure.
  - **Rich Field Type Support:** Includes standard inputs (Text, Email, Number), choice-based fields (Select, Radio, Checkbox, Multi-Select), date/time pickers, and file uploads.
  - **No Database Migrations Required:** Adding, removing, or changing form fields does not require `makemigrations` or `migrate`, enabling true on-the-fly form editing.
</details>

<details>
  <summary><strong>🔗 Advanced Data Modeling</strong></summary>
  
  - **Parent-Child Form Hierarchies:** A form can be designated as a child of another (e.g., `Student Form` -> `School Form`), enforcing relational data entry.
  - **Record-to-Record Relationships:** Users can create explicit links between individual submissions from different child forms (e.g., linking `Teacher A` to `Student B` and `Student C` within the context of `School X`). This allows for creating complex data graphs.
</details>

<details>
  <summary><strong>📊 Data Management & Analytics</strong></summary>
  
  - **Centralized Submission Viewing:** All form submissions are displayed in a clean, searchable, and paginated table.
  - **Public & Internal Data Entry:** Collect data via shareable public URLs or a secure internal interface for authenticated users.
  - **Automated Analytics Dashboard:** Submission data is automatically visualized with Plotly charts. The system intelligently selects the chart type (e.g., pie charts for `SELECT` fields, histograms for `INTEGER` fields).
  - **Versatile Data Export:** Submissions can be exported in **CSV**, **Excel (XLSX)**, and **PDF** formats.
</details>

<details>
  <summary><strong>🔐 User & Permission System</strong></summary>
  
  - **Custom User Model:** Extends Django's `AbstractUser` to include roles (`Admin`, `Editor`, `Viewer`).
  - **Per-Form Access Control:** A dedicated `FormPermission` model allows form owners to grant granular `view`, `edit`, or `admin` permissions to other users on a per-form basis.
  - **OTP-Based Password Reset:** A secure, custom password reset flow using One-Time Passwords sent via email.
</details>

<details>
  <summary><strong>🎨 Modern User Interface</strong></summary>
  
  - **Command Center Dashboard:** A two-column, app-like layout for all authenticated views provides a seamless user experience.
  - **Aesthetic Public Pages:** A fully custom, professional landing page and styled login/registration forms.
  - **Enhanced Admin Panel:** The default Django Admin is themed with **Django Jazzmin** for a modern, responsive, and feature-rich administrative backend.
</details>

---

## 🏛️ Architecture Overview

The application's core architecture is designed for maximum flexibility, avoiding the anti-pattern of creating a new database table for each form.

*   **`Form` Model:** Stores the metadata for a form, including its name, status, and most importantly, a `JSONField` named `fields`. This JSON object defines the structure (field names, types, options) of the form.
*   **`FormSubmission` Model:** Represents a single instance of a form being filled out. It acts as a container, linking to the `Form` it belongs to and the user who submitted it.
*   **`SubmissionData` (EAV Model):** This is the heart of the dynamic system. Instead of columns, it stores data in rows, with each row representing a single field from a single submission. It has three key columns:
    1.  `submission` (ForeignKey to `FormSubmission`)
    2.  `field_name` (e.g., "Full Name")
    3.  `field_value` (e.g., "John Doe")
    This Entity-Attribute-Value (EAV) structure allows for infinite form variations without altering the database schema.

---

## 🛠️ Tech Stack

| Category      | Technology                                    | Purpose                                       |
|---------------|-----------------------------------------------|-----------------------------------------------|
| **Backend**   | Python 3.11+, Django 5.2+                     | Core application framework                    |
| **Database**  | PostgreSQL                                    | Relational data storage                       |
| **Frontend**  | HTML5, Bootstrap 5, JavaScript (ES6+)         | UI structure and styling                      |
| **JS Libs**   | SortableJS, Plotly.js                         | Drag-and-drop, data visualization         |
| **Admin**     | Django Jazzmin                                | Modern, responsive admin theme                |
| **AI**        | Ollama (running `llama2` model)               | Natural language to form-field generation     |
| **Async**     | `asgiref`                                     | ASGI compatibility for Django                 |
| **Tooling**   | `python-decouple`, `psycopg2-binary`          | Environment variables, DB connectivity        |

---

## ⚙️ Local Development Setup

### 1. Prerequisites

-   **Python 3.11+** and `pip`.
-   **PostgreSQL:** A running instance is required.
-   **Git:** For cloning the repository.
-   **Ollama (Optional):** Required for the AI form generation feature. [Download from ollama.com](https://ollama.com/).

### 2. Environment Configuration

<details>
  <summary>Click to expand configuration steps</summary>
  
  1.  **Clone the Repository:**
      ```bash
      git clone https://github.com/your-username/your-repo-name.git
      cd your-repo-name
      ```

  2.  **Set up Virtual Environment:**
      ```bash
      # Create
      python -m venv venv
      # Activate
      # Windows: .\venv\Scripts\activate
      # macOS/Linux: source venv/bin/activate
      ```

  3.  **Install Dependencies:**
      ```bash
      pip install -r requirements.txt
      ```

  4.  **Configure Environment Variables:**
      -   Create a file named `.env` in the project's root directory.
      -   Populate it with your local configuration. Use the following as a template:
      ```dotenv
      # --- .env file ---
      # Django Secret Key (generate a new one for production)
      SECRET_KEY="your-secret-key-here"

      # Database (PostgreSQL)
      DB_NAME=dynamic_forms_db
      DB_USER=postgres
      DB_PASSWORD=your_postgres_password
      DB_HOST=localhost
      DB_PORT=5432

      # Email (for OTP Password Reset)
      # Note: Use an App Password for Gmail/Outlook
      SMTP_SERVER=smtp.gmail.com
      SMTP_PORT=587
      SENDER_USER=your.email@example.com
      SENDER_PASSWORD=your_16_digit_app_password
      ```

</details>

### 3. Database and Application Initialization

<details>
  <summary>Click to expand initialization steps</summary>
  
  1.  **Prepare PostgreSQL:**
      -   Ensure your PostgreSQL service is running.
      -   Create a new database matching the `DB_NAME` in your `.env` file.

  2.  **Run Database Migrations:**
      -   This command will create all the necessary tables based on `core/models.py`.
      ```bash
      python manage.py migrate
      ```

  3.  **Create a Superuser:**
      -   This account will have access to the Django Admin panel.
      ```bash
      python manage.py createsuperuser
      ```

  4.  **Initialize AI Model (Optional):**
      -   If Ollama is running, pull the required model from the command line:
      ```bash
      ollama pull llama2
      ```

</details>

### 4. Running the Server

-   Start the Django development server:
    ```bash
    python manage.py runserver
    ```
-   The application is now accessible at `http://127.0.0.1:8000/`.
-   The admin panel is at `http://127.0.0.1:8000/admin/`.

---

## 🗺️ Application Workflow

A quick guide on using the primary features of the application.

<details>
  <summary><strong>Step 1: Creating a Form</strong></summary>
  
  -   Navigate to the **Dashboard** -> **Create Form**.
  -   **Option A (AI):** Type a description like "A form to sign up for a company event" into the AI text area and click "Generate".
  -   **Option B (Manual):** Use the "Manually Add a Field" section to add fields one by one.
  -   **Reorder:** Drag and drop the generated fields into your desired order using the grip handle.
  -   Click **Create Form**.
</details>

<details>
  <summary><strong>Step 2: Collecting Data</strong></summary>
  
  -   Go to the **Form Detail** page for your newly created form.
  -   **Option A (Public):** Copy the **Public Share Link** and send it to anyone. They can submit the form without an account.
  -   **Option B (Internal):** Navigate to the **Fill a Form** page, select your form, and enter data as an authenticated user.
</details>

<details>
  <summary><strong>Step 3: Analyzing and Exporting</strong></summary>
  
  -   On the **Form Detail** page, view all submissions. Use the search bar to filter results.
  -   Click **View Analytics** to see a dashboard of charts visualizing the data.
  -   Use the **Export** buttons (CSV, Excel, PDF) on the detail page to download the raw data.
</details>

---

## 🔌 API Endpoints

The application exposes a few internal API endpoints to support its dynamic frontend.

| Method | Endpoint                             | Description                                            | Auth Required |
|--------|--------------------------------------|--------------------------------------------------------|---------------|
| `POST` | `/api/generate-fields/`              | Takes a JSON `{ "description": "..." }` and returns a JSON field structure. | Yes           |
| `GET`  | `/api/admin/get-child-submissions/`  | Fetches child submissions for use in admin dropdowns.  | Yes (Admin)   |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.