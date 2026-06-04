# Document Management System

This project is a monolithic application with asynchronous background workers. To run it locally, you will need to start the backend, the front-end, and the background task queue.

## Overview:
The core problem most software developing teams have in terms of collaboration; is the amount of documentation you need to make in order to keep everyone on the same page and track changes efficiently. The Document Management System will speed up this process, give developing teams a central hub to track and easily see changes in versions. We are using a legacy code-base to start off with, and then updating the tech-stack as we carry on. This ensures that we use more scalable and robust dependencies. This means that we should be able to do updates smoothly in the future, latency will be less and the central website should load dynamically without any stutters or outdated dependencies.

## Key Features:
- **Automatic Synchronization:** Webhook-driven listeners that automatically detect external repository updates and automatically trigger background syncing.
- **Asynchronous Automation Engine:** Built on Celery and Redis, the backend queues and executes heavy operations without blocking the main web thread.
- **Documentation Compilation:** Doesn't use traditional static site generation. It is done in a more dynamic way.
- **API-Free Architecture:** We eliminated the need for a traditional REST API. Django routes intercept web requests and use Inertia to inject database payloads directly into React component properties.
- **Fast SPA:** The front-end is a highly reactive Single Page Application built with React and Vite, providing snappy page transitions and real-time document rendering without browser reloads.
- **Centralized PostgreSQL Storage:** All project configurations, repository states, and compiled HTML document bodies are relationally mapped.

## Tech-Stack:
This application is built on a hybrid monolith architecture, combining the heavy-lifting capabilities of a Python backend with the instant reactivity of a modern JavaScript Single Page Application.

| Architecture Layer | Technologies | Purpose in System |
| :--- | :--- | :--- |
| **Frontend UI** | [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/) [![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](https://vitejs.dev/) | Renders the reactive Single Page Application (SPA) and instantly bundles frontend assets. |
| **Styling** | [![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/) | Provides utility-first CSS classes for rapid, consistent, and responsive UI design. |
| **The Bridge** | [![Inertia.js](https://img.shields.io/badge/Inertia.js-9553E9?style=for-the-badge&logo=inertia&logoColor=white)](https://inertiajs.com/) | Replaces traditional APIs by securely injecting Django database queries directly into React props. |
| **Backend Core** | [![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/) [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) | Manages the core business logic, database migrations, security, and view routing. |
| **Database** | [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/) | Stores relational project configurations and highly structured, compiled JSON document fragments. |
| **Task Workers** | [![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/) [![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/) | Acts as the message broker and background queue to handle heavy operations without freezing the web UI. |
| **Doc Engine** | [![Sphinx](https://img.shields.io/badge/Sphinx-000000?style=for-the-badge&logo=sphinx&logoColor=white)](https://www.sphinx-doc.org/) [![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)](https://git-scm.com/) | Syncs remote repositories and headless-compiles raw `.rst` and Markdown files into web-ready JSON. |

## Getting Started:
### Prerequisites
Ensure you have the following installed on your machine before starting:
* **Python 3.10+**
* **Node.js & npm** (v18+)
* **PostgreSQL** (Running locally on port 5432)
* **Redis** (Running locally on port 6379, required for Celery)
* **Git**

If you do not have PostgreSQL installed on your machine, here is how to set it up and configure it for this project:
**1. Install PostgreSQL**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**2. Ensure the Database Service is Running**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**3. Create the Database and Dedicated User**
```bash
sudo -u postgres psql
```
Then, run these SQL commands to set up the environment exactly as Django expects it. (Note: If you change the username or password here, make sure to update your .env file in Step 2 to match!)
```SQL
CREATE DATABASE document_management;
CREATE USER document_admin WITH PASSWORD 'your_super_secret_password';
ALTER ROLE document_admin SET client_encoding TO 'utf8';
ALTER ROLE document_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE document_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE document_management TO document_admin;
\q
```

### Step 1: Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/document-management-system.git](https://github.com/YOUR_USERNAME/document-management-system.git)
cd document-management-system
```

### Step 2: Backend Setup
```bash
# Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install Python requirements
pip install -r requirements.txt
```

Next, configure your environment variables. Create a .env file in the root directory and add your local database credentials:

```plaintext
# .env file
SECRET_KEY=your_django_secret_key_here
DEBUG=True

# Database Configuration
DB_NAME=document_management
DB_USER=postgres  # Or your custom postgres user
DB_PASSWORD=your_super_secret_password
DB_HOST=localhost
DB_PORT=5432
```

Finally, set up the database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
```

## Running the application:
Because this application uses background workers and a modern asset bundler, you will need to run three separate processes simultaneously during local development.

Open three terminal tabs and run the following commands from the root directory of the project: (ensure your .venv is activated in each terminal)

__Terminal 1: Django Server__
```bash
python manage.py runserver
```

__Terminal 2: The Vite Dev Server__
```bash
cd frontend
npm run dev
```

__Terminal 3: Celery Worker__
```bash
celery -A core worker -l info
```

Once all three are running, open your browser and navigate to `http://localhost:8000/dashboard/`
