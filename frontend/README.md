# MetaFuse Frontend

React + Tailwind frontend for MetaFuse.

## Run

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

App routes:
- `/` landing
- `/login`
- `/signup`
- `/dashboard`

The frontend expects the FastAPI server at `VITE_API_BASE_URL`.
