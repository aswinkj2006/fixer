"""
fixer.ai — FastAPI application entry point
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL, FRONTEND_ORIGIN
from backend.database.models import Base
from backend.simulation.simulator import run_simulation_loop, init_simulators
from backend.api import machines, tickets, sensor_readings, chat, admin, websocket as ws_router


# ─────────────────────────────────────────────────────────────────────────────
# DB engine (shared across app)
# ─────────────────────────────────────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — startup / shutdown
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Register WebSocket broadcast callback
    from backend.api.websocket import broadcast_to_machine
    from backend.simulation.simulator import set_ws_broadcast_callback
    set_ws_broadcast_callback(broadcast_to_machine)

    # Start simulation loop as background task
    sim_task = asyncio.create_task(run_simulation_loop(AsyncSessionLocal))

    yield  # App is running

    # Cleanup
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="fixer.ai API",
    description="Per-machine AI diagnostic system for industrial machinery fleets",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(machines.router, prefix="/api", tags=["machines"])
app.include_router(tickets.router, prefix="/api", tags=["tickets"])
app.include_router(sensor_readings.router, prefix="/api", tags=["sensors"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(ws_router.router, tags=["websocket"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "fixer.ai"}
