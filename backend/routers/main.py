from datetime import date
from pathlib import Path
from typing import Annotated
from cruds import main as main_cruds
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import db
from shcemas.main import (
    HabitCreateSchema,
    HabitDeleteSchema,
    HabitResponseSchema,
    HabitSchema,
    HabitUpdateSchema,
    UserPublic,
    ResponseSchema,
)
import cruds.main as habit_cruds
import models.main as habit_models
from shcemas.main import (
    CalendarMemoCreateSchema,
    CalendarMemoDeleteSchema,
    CalendarMemoSchema,
    CalendarMemoUpdateSchema,
    CalendarMonthSummarySchema,
    DiaryEntryCreateSchema,
    DiaryEntryDeleteSchema,
    DiaryEntrySchema,
    DiaryEntryUpdateSchema,
    TimerStartSchema,
    TimerStatusSchema,
)

from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    get_password_hash,
)

from timer_service import timer_manager

router = APIRouter(tags=["habits"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
SOURCE_CATEGORIES = ["Health", "Personal Development", "Mental Health", "Original"]
MY_HABITS_CATEGORY = "My Habits"

# Habits every newly registered user starts with under "My Habits".
DEFAULT_MY_HABITS = [
    ("Squad", "Spend time with your squad."),
    ("Meditate", "Practice mindfulness meditation."),
    ("Write three good things", "Write down three good things that happened today."),
    ("Write 10 thanks list", "Write a list of 10 things you are thankful for."),
]

auth_router = APIRouter(tags=["auth"])

@auth_router.post("/register", response_model=UserPublic)
async def register_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: AsyncSession = Depends(db.get_dbsession)
) -> UserPublic:
    username = form_data.username.strip()
    if len(username) < 3 or len(form_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    user = await main_cruds.get_user_by_username(db_session, username)
    if user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    new_user = habit_models.User(
        username=username,
        password_hash=get_password_hash(form_data.password),
    )
    created_user = await main_cruds.post_user(db_session, new_user)

    for name, description in DEFAULT_MY_HABITS:
        db_session.add(
            habit_models.Habit(
                name=name,
                description=description,
                category=MY_HABITS_CATEGORY,
                user_id=created_user.id,
            )
        )
    await db_session.commit()

    return created_user

@auth_router.post("/login", response_model=ResponseSchema)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: AsyncSession = Depends(db.get_dbsession),
) -> ResponseSchema:
    username = form_data.username.strip()
    if not username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    user = await authenticate_user(db_session, username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return ResponseSchema(message="ok")


@auth_router.post("/logout")
async def logout():
    redirect = RedirectResponse("/login-page", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(COOKIE_NAME, path="/")
    return redirect


@auth_router.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@auth_router.get("/register-page", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})


def _calendar_year_month(year: int | None, month: int | None) -> tuple[int, int]:
    today = date.today()
    resolved_year = year if year is not None else today.year
    resolved_month = month if month is not None else today.month
    return resolved_year, resolved_month


def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


async def _calendar_context(
    db_session: AsyncSession,
    year: int | None,
    month: int | None,
    user_id: int,
) -> dict[str, object]:
    resolved_year, resolved_month = _calendar_year_month(year, month)
    summary = await habit_cruds.get_calendar_month_summary(db_session, resolved_year, resolved_month, user_id)
    diary_entries = await habit_cruds.get_diary_entries(db_session, user_id)
    prev_year, prev_month = _previous_month(resolved_year, resolved_month)
    next_year, next_month = _next_month(resolved_year, resolved_month)
    return {
        "calendar_summary": summary,
        "diary_entries": diary_entries,
        "calendar_year": resolved_year,
        "calendar_month": resolved_month,
        "calendar_label": f"{resolved_year}-{resolved_month:02d}",
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }


async def _my_habits_context(db_session: AsyncSession, user_id: int) -> dict[str, object]:
    habits = await habit_cruds.get_habit_by_category(db_session, MY_HABITS_CATEGORY, user_id)
    return {"my_habits": habits}


async def _memo_context(db_session: AsyncSession, user_id: int) -> dict[str, object]:
    return {"calendar_memos": await habit_cruds.get_calendar_memos(db_session, user_id)}


async def _page1_context(db_session: AsyncSession, user_id: int) -> dict[str, object]:
    today = date.today()
    entries = await habit_cruds.get_diary_entries_by_date(db_session, today, user_id)
    my_habits = await habit_cruds.get_habit_by_category(db_session, MY_HABITS_CATEGORY, user_id)
    return {
        "today": today,
        "today_entries": entries,
        "my_habits": my_habits,
    }


async def _page2_context(
    db_session: AsyncSession,
    category: str | None,
    year: int | None,
    month: int | None,
    user_id: int,
) -> dict[str, object]:
    active_category = category if category in SOURCE_CATEGORIES else SOURCE_CATEGORIES[0]
    resolved_year, resolved_month = _calendar_year_month(year, month)
    source_habits = await habit_cruds.get_habit_by_category(db_session, active_category, user_id)
    my_habits = await habit_cruds.get_habit_by_category(db_session, MY_HABITS_CATEGORY, user_id)
    summary = await habit_cruds.get_calendar_month_summary(db_session, resolved_year, resolved_month, user_id)
    prev_year, prev_month = _previous_month(resolved_year, resolved_month)
    next_year, next_month = _next_month(resolved_year, resolved_month)
    return {
        "source_categories": SOURCE_CATEGORIES,
        "active_category": active_category,
        "source_habits": source_habits,
        "my_habits": my_habits,
        "calendar_summary": summary,
        "calendar_year": resolved_year,
        "calendar_month": resolved_month,
        "calendar_label": f"{resolved_year}-{resolved_month:02d}",
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }


async def _diary_context(
    db_session: AsyncSession,
    year: int | None,
    month: int | None,
    user_id: int,
) -> dict[str, object]:
    context = await _calendar_context(db_session, year, month, user_id)
    return {
        **context,
        "diary_entries": await habit_cruds.get_diary_entries(db_session, user_id),
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int | None, Depends(get_current_user_optional)],
):
    if user_id is None:
        return RedirectResponse("/login-page", status_code=status.HTTP_303_SEE_OTHER)
    context = await _page1_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "page1.html", context)


@router.get("/ui/my-habits", response_class=HTMLResponse)
async def my_habits_section(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    context = await _my_habits_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/my_habits_section.html", context)


@router.get("/ui/page1/memo", response_class=HTMLResponse)
@router.get("/ui/today-diary", response_class=HTMLResponse)
async def page1_memo_section(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    context = await _page1_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/page1_memo_section.html", context)


@router.post("/memos", response_class=HTMLResponse)
async def create_page1_memo(
    request: Request,
    memo_content: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    today = date.today()
    await habit_cruds.create_diary_entry(
        db,
        DiaryEntryCreateSchema(entry_date=today, title="Memo", content=memo_content),
        user_id,
    )
    context = await _page1_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/page1_memo_section.html", context)


@router.get("/page2", response_class=HTMLResponse)
async def page2(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int | None, Depends(get_current_user_optional)],
    category: str | None = None,
    year: int | None = None,
    month: int | None = None,
):
    if user_id is None:
        return RedirectResponse("/login-page", status_code=status.HTTP_303_SEE_OTHER)
    context = await _page2_context(db, category, year, month, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "page2.html", context)


@router.get("/ui/page2/category-picker", response_class=HTMLResponse)
async def page2_category_picker(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    category: str | None = None,
):
    context = await _page2_context(db, category, None, None, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/page2_category_picker.html", context)


@router.post("/ui/page2/register-habit", response_class=HTMLResponse)
async def register_habit_to_my_habits(
    request: Request,
    habit_id: Annotated[int, Form()],
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    category: str | None = None,
):
    existing = await habit_cruds.get_habit_by_id(db, habit_id, user_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    existing.category = MY_HABITS_CATEGORY
    await db.commit()
    await db.refresh(existing)

    context = await _page2_context(db, category, None, None, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/page2_register_bundle.html", context)


@router.post("/ui/page2/register-original-habit", response_class=HTMLResponse)
async def register_original_habit(
    request: Request,
    name: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    description: Annotated[str, Form()] = "",
    category: str | None = None,
):
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Habit name must not be empty.",
        )

    await habit_cruds.create_habit(
        db,
        HabitCreateSchema(name=name.strip(), description=description.strip(), category=MY_HABITS_CATEGORY),
        user_id,
    )

    context = await _page2_context(db, category, None, None, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/page2_register_bundle.html", context)


@router.put("/ui/habits/{habit_id}", response_class=HTMLResponse)
async def update_habit_ui(
    request: Request,
    habit_id: int,
    habit: HabitUpdateSchema,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    if habit.id != habit_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Habit id does not match the payload.")
    try:
        await habit_cruds.update_habit(db, habit, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _my_habits_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/my_habits_section.html", context)


@router.delete("/ui/habits/{habit_id}", response_class=HTMLResponse)
async def delete_habit_ui(
    request: Request,
    habit_id: int,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    try:
        await habit_cruds.delete_habit(db, habit_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _my_habits_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/my_habits_section.html", context)


@router.get("/ui/calendar-memos", response_class=HTMLResponse)
async def memo_section(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    context = await _memo_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/calendar_memos_section.html", context)


@router.post("/ui/calendar-memos", response_class=HTMLResponse)
async def create_memo_ui(
    request: Request,
    memo: CalendarMemoCreateSchema,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    await habit_cruds.create_calendar_memo(db, memo, user_id)
    context = await _memo_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/calendar_memos_section.html", context)


@router.put("/ui/calendar-memos/{memo_id}", response_class=HTMLResponse)
async def update_memo_ui(
    request: Request,
    memo_id: int,
    memo: CalendarMemoUpdateSchema,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    if memo.id != memo_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Calendar memo id does not match the payload.")
    try:
        await habit_cruds.update_calendar_memo(db, memo, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _memo_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/calendar_memos_section.html", context)


@router.delete("/ui/calendar-memos/{memo_id}", response_class=HTMLResponse)
async def delete_memo_ui(
    request: Request,
    memo_id: int,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    try:
        await habit_cruds.delete_calendar_memo(db, memo_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _memo_context(db, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/calendar_memos_section.html", context)


@router.get("/ui/diary-entries", response_class=HTMLResponse)
async def diary_section(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    context = await _diary_context(db, year, month, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/diary_section.html", context)


@router.post("/ui/diary-entries", response_class=HTMLResponse)
async def create_diary_entry_ui(
    request: Request,
    entry: DiaryEntryCreateSchema,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    await habit_cruds.create_diary_entry(db, entry, user_id)
    context = await _diary_context(db, year, month, user_id)
    context["request"] = request
    context["calendar_oob"] = True
    return templates.TemplateResponse(request, "partials/diary_bundle.html", context)


@router.put("/ui/diary-entries/{entry_id}", response_class=HTMLResponse)
async def update_diary_entry_ui(
    request: Request,
    entry_id: int,
    entry: DiaryEntryUpdateSchema,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    if entry.id != entry_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Diary entry id does not match the payload.")
    try:
        await habit_cruds.update_diary_entry(db, entry, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _diary_context(db, year, month, user_id)
    context["request"] = request
    context["calendar_oob"] = True
    return templates.TemplateResponse(request, "partials/diary_bundle.html", context)


@router.delete("/ui/diary-entries/{entry_id}", response_class=HTMLResponse)
async def delete_diary_entry_ui(
    request: Request,
    entry_id: int,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    try:
        await habit_cruds.delete_diary_entry(db, entry_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _diary_context(db, year, month, user_id)
    context["request"] = request
    context["calendar_oob"] = True
    return templates.TemplateResponse(request, "partials/diary_bundle.html", context)


@router.delete("/ui/calendar/diary-entries/{entry_id}", response_class=HTMLResponse)
async def delete_calendar_diary_entry_ui(
    request: Request,
    entry_id: int,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    try:
        await habit_cruds.delete_diary_entry(db, entry_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    context = await _calendar_context(db, year, month, user_id)
    context["request"] = request
    return templates.TemplateResponse(request, "partials/calendar_section.html", context)


@router.get("/ui/calendar", response_class=HTMLResponse)
async def calendar_section(
    request: Request,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
    year: int | None = None,
    month: int | None = None,
):
    context = await _calendar_context(db, year, month, user_id)
    context["request"] = request
    context["diary_oob"] = True
    return templates.TemplateResponse(request, "partials/calendar_bundle.html", context)


@router.post("/ui/timer-record", response_class=HTMLResponse)
async def timer_record(
    request: Request,
    entry_date: date,
    title: str,
    content: str,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    await habit_cruds.create_diary_entry(
        db,
        DiaryEntryCreateSchema(entry_date=entry_date, title=title, content=content),
        user_id,
    )
    context = await _page1_context(db, user_id)
    context["request"] = request
    context["message"] = f"Recorded at {entry_date}"
    return templates.TemplateResponse(request, "partials/page1_memo_section.html", context)


@router.post("/ui/timer/start", response_model=TimerStatusSchema)
async def start_timer(timer: TimerStartSchema, user_id: Annotated[int, Depends(get_current_user)]):
    state = await timer_manager.start_timer(
        user_id=user_id,
        habit=timer.habit,
        memo=timer.memo,
        entry_date=date.today(),
        duration_seconds=timer.duration_seconds,
    )
    return timer_manager.to_status_schema(state)


@router.get("/ui/timer/{timer_id}", response_model=TimerStatusSchema)
async def timer_status(timer_id: str, user_id: Annotated[int, Depends(get_current_user)]):
    state = await timer_manager.get_timer(timer_id)
    if state is None or state.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timer not found")
    return timer_manager.to_status_schema(state)

@router.get("/habits", response_model=list[HabitSchema])
async def get_habits(db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.get_habits(db, user_id)

@router.get("/habits/{category}", response_model=list[HabitSchema])
async def get_habit_by_category(category: str, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        return await habit_cruds.get_habit_by_category(db, category, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/habits", response_model=HabitSchema, status_code=status.HTTP_201_CREATED)
async def create_habit(habit: HabitCreateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.create_habit(db, habit, user_id)

@router.delete("/habits", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit: HabitDeleteSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    await habit_cruds.delete_habit(db, habit.id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/habits", response_model=HabitSchema)
async def update_habit(habit: HabitUpdateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.update_habit(db, habit, user_id)


# Calendar memos
@router.get("/calendar_memos", response_model=list[CalendarMemoSchema])
async def get_calendar_memos(db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.get_calendar_memos(db, user_id)


@router.get("/calendar_memos/{memo_date}", response_model=CalendarMemoSchema)
async def get_calendar_memo_by_date(memo_date: str, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        from datetime import date
        d = date.fromisoformat(memo_date)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    memo = await habit_cruds.get_calendar_memo_by_date(db, d, user_id)
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CalendarMemo not found")
    return memo


@router.post("/calendar_memos", response_model=CalendarMemoSchema, status_code=status.HTTP_201_CREATED)
async def create_calendar_memo(memo: CalendarMemoCreateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        return await habit_cruds.create_calendar_memo(db, memo, user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/calendar_memos", response_model=CalendarMemoSchema)
async def update_calendar_memo(memo: CalendarMemoUpdateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        return await habit_cruds.update_calendar_memo(db, memo, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/calendar_memos", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_memo(memo: CalendarMemoDeleteSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        await habit_cruds.delete_calendar_memo(db, memo.id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/diary_entries", response_model=list[DiaryEntrySchema])
async def get_diary_entries(db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.get_diary_entries(db, user_id)


@router.get("/diary_entries/by-date/{entry_date}", response_model=list[DiaryEntrySchema])
async def get_diary_entries_by_date(entry_date: str, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        from datetime import date
        d = date.fromisoformat(entry_date)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    return await habit_cruds.get_diary_entries_by_date(db, d, user_id)


@router.post("/diary_entries", response_model=DiaryEntrySchema, status_code=status.HTTP_201_CREATED)
async def create_diary_entry(entry: DiaryEntryCreateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    return await habit_cruds.create_diary_entry(db, entry, user_id)


@router.put("/diary_entries", response_model=DiaryEntrySchema)
async def update_diary_entry(entry: DiaryEntryUpdateSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        return await habit_cruds.update_diary_entry(db, entry, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/diary_entries", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diary_entry(entry: DiaryEntryDeleteSchema, db: Annotated[AsyncSession, Depends(db.get_dbsession)], user_id: Annotated[int, Depends(get_current_user)]):
    try:
        await habit_cruds.delete_diary_entry(db, entry.id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/calendar/{year}/{month}", response_model=CalendarMonthSummarySchema)
async def get_calendar_month_summary(
    year: int,
    month: int,
    db: Annotated[AsyncSession, Depends(db.get_dbsession)],
    user_id: Annotated[int, Depends(get_current_user)],
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Month must be between 1 and 12.")
    return await habit_cruds.get_calendar_month_summary(db, year, month, user_id)
