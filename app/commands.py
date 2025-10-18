import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from .config import LOCAL_TZ, TZ_NAME
from .db import ensure_sub, set_sub, get_sub
from .ff_client import fetch_calendar
from .filters import filter_events
from .formatting import event_to_text
from .utils import csv_to_list, chunk
from .keyboards import settings_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    await m.answer(
        (
            "<b>Привіт!</b> Я шле економічні події з ForexFactory.\n\n"
            "Команди:\n"
            "• /settings — відкриє інлайн‑панель для фільтрів\n"
            "• /subscribe HH:MM — щоденна розсилка\n"
            "• /alert N — пуш за N хв до події (напр. /alert 30)\n"
            "• /impact High,Medium — фільтри важливості (текстово)\n"
            "• /countries USD,EUR — фільтр валют/країн (текстово)\n"
            "• /lang uk|en|auto — мова заголовків (автопереклад)\n"
            "• /postto @channel — слати у вказаний канал (додайте мене адміністратором)\n"
            "• /today — події на сьогодні зараз\n"
            "• /stop — вимкнути нотифікації\n"
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

@router.message(Command("settings"))
async def cmd_settings(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    subs = get_sub(m.from_user.id, m.chat.id)
    impacts = csv_to_list(subs["impact_filter"])
    currencies = csv_to_list(subs["countries_filter"])
    alert_minutes = int(subs["alert_minutes"])
    lang_mode = subs["lang_mode"]
    kb = settings_kb(impacts, currencies, alert_minutes, lang_mode)
    await m.answer("⚙️ Налаштування фільтрів:", reply_markup=kb)

@router.callback_query(F.data.startswith("imp:"))
async def cb_impact(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    impacts = set(csv_to_list(subs["impact_filter"]))
    val = c.data.split(":",1)[1]
    if val in impacts: impacts.remove(val)
    else: impacts.add(val)
    set_sub(c.from_user.id, c.message.chat.id, impact_filter=",".join(sorted(impacts)))
    subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]), int(subs["alert_minutes"]), subs["lang_mode"])
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Impact оновлено")

@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    curr = set(csv_to_list(subs["countries_filter"]))
    val = c.data.split(":",1)[1]
    if val in curr: curr.remove(val)
    else: curr.add(val)
    set_sub(c.from_user.id, c.message.chat.id, countries_filter=",".join(sorted(curr)))
    subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]), int(subs["alert_minutes"]), subs["lang_mode"])
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Валюти оновлено")

@router.callback_query(F.data.startswith("al:"))
async def cb_alert(c: CallbackQuery):
    val = int(c.data.split(":",1)[1])
    set_sub(c.from_user.id, c.message.chat.id, alert_minutes=val)
    subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]), int(subs["alert_minutes"]), subs["lang_mode"])
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Час алерту оновлено")

@router.callback_query(F.data.startswith("lang:trash"))  # guard if needed
async def cb_lang_noop(c: CallbackQuery):
    await c.answer()

@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(c: CallbackQuery):
    val = c.data.split(":",1)[1]
    set_sub(c.from_user.id, c.message.chat.id, lang_mode=val)
    subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]), int(subs["alert_minutes"]), subs["lang_mode"])
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Мову автоперекладу оновлено")

@router.callback_query(F.data=="reset")
async def cb_reset(c: CallbackQuery):
    set_sub(c.from_user.id, c.message.chat.id, impact_filter="High,Medium", countries_filter="", alert_minutes=30, lang_mode="en")
    subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]), int(subs["alert_minutes"]), subs["lang_mode"])
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Скинуто налаштування")

@router.message(Command("subscribe"))
async def cmd_subscribe(m: Message):
    time_str = _arg_tail(m.text)
    if not re.match(r"^\d{1,2}:\d{2}$", time_str or ""):
        return await m.answer("Приклад: /subscribe 09:00")
    hh, mm = map(int, time_str.split(":"))
    set_sub(m.from_user.id, m.chat.id, daily_time=f"{hh:02d}:{mm:02d}")
    await m.answer(f"Щоденна розсилка о {hh:02d}:{mm:02d} ({TZ_NAME}).")

@router.message(Command("alert"))
async def cmd_alert(m: Message):
    try:
        mins = int((_arg_tail(m.text) or "").strip())
    except Exception:
        mins = 0
    if not mins or mins < 5 or mins > 180:
        return await m.answer("Вкажіть хвилини 5–180, напр. /alert 30")
    set_sub(m.from_user.id, m.chat.id, alert_minutes=mins)
    await m.answer(f"Нагадування за {mins} хв до події активовано.")

@router.message(Command("impact"))
async def cmd_impact(m: Message):
    s = _arg_tail(m.text)
    if not s:
        return await m.answer("Приклад: /impact High,Medium")
    set_sub(m.from_user.id, m.chat.id, impact_filter=s)
    await m.answer(f"Фільтр важливості: {s}")

@router.message(Command("countries"))
async def cmd_countries(m: Message):
    s = _arg_tail(m.text) or ""
    set_sub(m.from_user.id, m.chat.id, countries_filter=s)
    await m.answer(f"Фільтр валют/країн: {s or 'всі'}")

@router.message(Command("lang"))
async def cmd_lang(m: Message):
    s = (_arg_tail(m.text) or "").lower()
    if s not in ("en","uk","auto"):
        return await m.answer("Використай: /lang en | /lang uk | /lang auto")
    set_sub(m.from_user.id, m.chat.id, lang_mode=s)
    await m.answer(f"Мова автоперекладу: {s}")

@router.message(Command("postto"))
async def cmd_postto(m: Message):
    # set output channel/chat where messages will be sent
    val = _arg_tail(m.text) or ""
    if not val:
        return await m.answer("Приклад: /postto @your_channel або /postto -1001234567890")
    try:
        chat = await m.bot.get_chat(val)
        out_id = chat.id
    except TelegramBadRequest:
        try:
            out_id = int(val)
        except Exception:
            return await m.answer("Не вдалося визначити чат. Спробуй @username або numeric id.")
    set_sub(m.from_user.id, m.chat.id, out_chat_id=out_id)
    await m.answer(f"Розсилка тепер йтиме в чат/канал: <code>{out_id}</code>", parse_mode="HTML")

@router.message(Command("today"))
async def cmd_today(m: Message):
    subs = get_sub(m.from_user.id, m.chat.id)
    if not subs:
        ensure_sub(m.from_user.id, m.chat.id)
        subs = get_sub(m.from_user.id, m.chat.id)
    lang = subs["lang_mode"]
    events = await fetch_calendar(lang=lang)
    now_local = datetime.now(LOCAL_TZ)
    start_utc = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
    end_utc = start_utc + timedelta(days=1)
    todays = [e for e in events if start_utc <= e.date <= end_utc]

    filtered = filter_events(todays, csv_to_list(subs["impact_filter"]), csv_to_list(subs["countries_filter"]))
    if not filtered:
        return await m.answer("Сьогодні подій за вашими фільтрами немає.")

    # If out_chat_id set, send there
    target_chat = subs["out_chat_id"] or m.chat.id
    for ch in chunk(filtered, 8):
        await m.bot.send_message(target_chat, "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in ch), parse_mode="HTML", disable_web_page_preview=True)

@router.message(Command("stop"))
async def cmd_stop(m: Message):
    from .db import db
    with db() as conn:
        conn.execute("DELETE FROM subscriptions WHERE user_id=? AND chat_id=?", (m.from_user.id, m.chat.id))
        conn.commit()
    await m.answer("Підписку вимкнено для цього чату.")

def _arg_tail(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else None
