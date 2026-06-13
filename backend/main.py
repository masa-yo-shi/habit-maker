from fastapi import FastAPI
from routers.main import router
import db

app = FastAPI(title="Habit Maker API")
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    await db.init_db(seed_sample=True, reset=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
