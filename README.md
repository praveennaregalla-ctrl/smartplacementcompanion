# Smart Placement Companion

Smart Placement Companion is a Python project that helps students prepare for campus placements.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1. Clone the repository:

```bash
   git clone https://github.com/praveennaregalla-ctrl/smartplacementcompanion.git
   cd smartplacementcompanion/smart_placement_companion
```

2. Create and activate a virtual environment:

```bash
   python -m venv .venv
   .venv\Scripts\activate
```

   On macOS or Linux, use `source .venv/bin/activate`.

3. Install the dependencies:

```bash
   pip install -r requirements.txt
```

### Running the Project

```bash
python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

## Deployment

### Vercel

1. Import the repository into [Vercel](https://vercel.com) and set the **Root Directory** to `smart_placement_companion`.
2. Add these Production environment variables before deploying:
   - `SECRET_KEY`: a newly generated Django secret key.
   - `DATABASE_URL`: a persistent PostgreSQL connection URL from your database provider. SQLite is supported only for local development.
   - `ALLOWED_HOSTS`: optional comma-separated custom domain names. Vercel deployment hostnames are added automatically.
   - `CSRF_TRUSTED_ORIGINS`: optional comma-separated HTTPS origins for custom domains, for example `https://placements.example.com`.
3. Use Vercel's detected Django build settings so `collectstatic` runs during the build.
4. After the first deployment, run `python manage.py migrate` against the production database.
5. Configure persistent object storage for uploaded resumes and profile pictures. Vercel's filesystem is ephemeral; local database and media files are excluded from deployment.

The deployment intentionally fails its build if `SECRET_KEY` or `DATABASE_URL` is missing. The included Vercel function routes requests to Django, and WhiteNoise serves collected static files.

Generate a secret key locally with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## Author

**Praveen Naregalla**
GitHub: [@praveennaregalla-ctrl](https://github.com/praveennaregalla-ctrl)