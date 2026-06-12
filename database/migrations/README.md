# Database Migrations

The runnable Alembic migration scripts live in `backend/alembic`. They are kept with
the backend so the app imports the same SQLAlchemy metadata used by the API.

Run migrations from the `backend` directory:

```bash
alembic upgrade head
```

