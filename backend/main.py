from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from routers.main import auth_router, router
import db

app = FastAPI(title="Habit Maker")
app.include_router(router)
app.include_router(auth_router)


@app.exception_handler(StarletteHTTPException)
async def htmx_aware_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and request.headers.get("HX-Request") == "true":
        return Response(status_code=200, headers={"HX-Redirect": "/login-page"})
    return await http_exception_handler(request, exc)


@app.on_event("startup")
async def startup_event() -> None:
    await db.init_db(seed_sample=True, reset=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
