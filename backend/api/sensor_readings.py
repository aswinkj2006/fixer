"""fixer.ai — Sensor readings API (historical data for charts)"""
from fastapi import APIRouter, Query
from sqlalchemy import select
from backend.database.models import SensorReading

router = APIRouter()


@router.get("/sensors/{machine_id}/history")
async def get_sensor_history(
    machine_id: str,
    sensor_type: str = Query(None, description="Filter by sensor type"),
    limit: int = Query(200, description="Max readings to return per sensor"),
):
    """
    Returns recent sensor readings for charts.
    Returns last `limit` readings per sensor type.
    """
    from backend.main import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        query = select(SensorReading).where(SensorReading.machine_id == machine_id)
        if sensor_type:
            query = query.where(SensorReading.sensor_type == sensor_type)
        query = query.order_by(SensorReading.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        readings = result.scalars().all()

        # Group by sensor type for frontend convenience
        grouped: dict[str, list] = {}
        for r in reversed(readings):  # Reverse to chronological order
            if r.sensor_type not in grouped:
                grouped[r.sensor_type] = []
            grouped[r.sensor_type].append({
                "timestamp": r.timestamp,
                "value": r.value,
                "unit": r.unit,
            })

        return {
            "machine_id": machine_id,
            "sensors": grouped,
        }
