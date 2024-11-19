from .initialize_functions import add_all_collections
import asyncio

async def main():
    await add_all_collections('app/games.json')

if __name__ == "__main__":
    asyncio.run(main())