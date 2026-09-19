import asyncio, sys
sys.path.insert(0, '.')

async def check_db():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, func
    from backend.config import DATABASE_URL
    from backend.database.models import Machine, Technician, FailureCode, Ticket, TicketMessage

    engine = create_async_engine(DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as s:
        machines = (await s.execute(select(func.count()).select_from(Machine))).scalar()
        techs = (await s.execute(select(func.count()).select_from(Technician))).scalar()
        codes = (await s.execute(select(func.count()).select_from(FailureCode))).scalar()
        tickets = (await s.execute(select(func.count()).select_from(Ticket))).scalar()
        msgs = (await s.execute(select(func.count()).select_from(TicketMessage))).scalar()
        tech_rows = (await s.execute(select(Technician))).scalars().all()
        ticket_sample = (await s.execute(select(Ticket).limit(5))).scalars().all()

    print("Database state:")
    print(f"  Machines:         {machines}  (expected: 4)")
    print(f"  Technicians:      {techs}  (expected: 4)")
    print(f"  Failure codes:    {codes}  (expected: 8)")
    print(f"  Tickets:          {tickets}  (expected: 19+)")
    print(f"  Ticket messages:  {msgs}")
    print()
    print("Technician Slack IDs:")
    for t in tech_rows:
        slack_ok = "OK" if t.slack_user_id else "MISSING"
        print(f"  {t.name} ({t.specialty}): slack_user_id={t.slack_user_id or 'EMPTY'} [{slack_ok}]")
    print()
    print("Sample tickets:")
    for t in ticket_sample:
        print(f"  {t.ticket_id[:8]} | {t.machine_id} | {t.failure_code} | status={t.status} | severity={t.severity}")

    await engine.dispose()
    assert machines == 4
    assert techs == 4
    assert codes == 8
    assert tickets >= 9
    print()
    print("Database assertions PASSED")

asyncio.run(check_db())
