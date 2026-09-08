#!/bin/bash
# CreatorOS startup script
# Run from the root creatorOS/ directory

echo ""
echo "  CreatorOS"
echo "  while you sleep, we handle the busywork"
echo ""

# Check .env exists
if [ ! -f backend/.env ]; then
  echo "⚠️  No .env found. Copying from .env.example..."
  cp backend/.env.example backend/.env
  echo "   Fill in your API keys in backend/.env then run this script again."
  exit 1
fi

echo "Starting backend on http://localhost:8000"
cd backend
venv/bin/uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

cd ../frontend
echo "Starting frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo ""

# Wait for both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
