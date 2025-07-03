# Contract Review Backend

This is the backend service for contract review, supporting file upload, parsing, AI-based risk review, and export. It exposes several APIs to handle user authentication, contract analysis, file operations, and billing.

## Project Setup

### 1. Install dependencies:

Make sure Python 3.8+ is installed. Then, run the following command to install the dependencies.

```bash
pip install -r requirements.txt
```

### 2. Configuration:
The project uses environment variables for sensitive configurations like API keys, JWT secrets, and Stripe configurations. Create a .env file in the root of the project with the following keys:

```
FLASK_APP=run.py
FLASK_ENV=development
JWT_SECRET_KEY=your-jwt-secret-key
STRIPE_SECRET_KEY=your-stripe-secret-key
DATABASE_URL=your-database-url
```

### 3. Database setup:
The project uses SQLAlchemy for database management. To initialize the database, run the following command:

```bash
flask db init
flask db migrate
flask db upgrade
```

### 4. Running the Application:
To start the development server, use the following command:

```bash
python run.py
```

This will start the server on http://127.0.0.1:5000.

Alternatively, you can use gunicorn for production:

```bash
gunicorn -c gunicorn_config.py run:app
```

### 5. API Endpoints

**Auth Service:**
- Login: `POST /auth/login`
- Refresh: `POST /auth/refresh`

**Review Service:**
- Review contract: `POST /api/v1/review`

**Search Service:**
- Search risks: `GET /api/v1/search?q=<keyword>`

**Billing Service:**
- Stripe webhook: `POST /webhook/stripe`

**File Service:**
- Upload file: `POST /api/v1/upload`
- Export file: `GET /api/v1/export/<file_id>`

### 6. Docker Setup:
You can use Docker to run the application in a containerized environment.

Build the Docker image:

```bash
docker build -t contract-review-backend .
```

Run the Docker container:

```bash
docker run -p 5000:5000 --env-file .env contract-review-backend
```

### 7. File Upload & Parsing:
Files uploaded to the `/api/v1/upload` endpoint will be stored and processed. If the file is a PDF, it will be converted to DOCX format using the `pdf2docx` library.

### 8. Risk Review:
Once a contract file is uploaded, it will be passed through the AI model for risk annotation, and the response will be returned to the frontend for display.

### 9. Billing & Webhooks:
Stripe webhook events will be handled by the `/webhook/stripe` endpoint to update user subscription data.