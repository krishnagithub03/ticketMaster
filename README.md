# ticketly

## Run the frontend

The React app lives in [`frontend/`](./frontend). Install dependencies and start
Vite on the same port allowed by the backend CORS configuration:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The default API URL is `http://localhost:5000`. Override it with
`VITE_API_BASE_URL` when the Flask server runs elsewhere.

## Backend integration

The frontend uses the backend authentication endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Access tokens are sent as Bearer tokens and refresh requests include cookies.
Movie, event, venue, showtime, and booking cards currently use local demo data
because those backend endpoints do not exist yet.

## API documentation

The Flask backend serves interactive Swagger documentation:

- Swagger UI: `http://localhost:5000/api/docs`
- OpenAPI JSON: `http://localhost:5000/api/swagger.json`

The documentation is generated at runtime from the registered Flask routes.
When a new route is added, it appears automatically after restarting the Flask
development server. Add an OpenAPI YAML docstring above the route when you want
to describe its request body, parameters, authentication, or response schema.