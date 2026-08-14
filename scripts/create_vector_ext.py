import asyncio
import asyncpg
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    conn = await asyncpg.connect('postgresql://recruitment:recruitment_pass@localhost:5432/recruitment_db')
    try:
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        print('Vector extension created successfully!')
    except Exception as e:
        print(f'Cannot create vector extension: {e}')
    
    # Verify
    rows = await conn.fetch("SELECT * FROM pg_extension WHERE extname='vector'")
    print(f'Vector extension found: {len(rows) > 0}')
    
    await conn.close()

asyncio.run(main())
