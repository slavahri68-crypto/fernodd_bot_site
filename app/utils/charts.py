# ============================================================
#  app/utils/charts.py — графики matplotlib
# ============================================================
import io
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from ..database import daily_activity, pool

plt.rcParams.update({
    "figure.facecolor": "#0f172a",
    "axes.facecolor": "#0f172a",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#cbd5e1",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "text.color": "#e2e8f0",
    "font.size": 11,
    "axes.grid": True,
    "grid.color": "#1e293b",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
})


async def activity_chart() -> bytes:
    rows = await daily_activity(14)
    by_day = {r["day"]: r["n"] for r in rows}
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    counts = [by_day.get(d, 0) for d in days]

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)
    ax.plot(days, counts, color="#38bdf8", linewidth=2.5,
            marker="o", markersize=6, markerfacecolor="#f472b6",
            markeredgecolor="#38bdf8")
    ax.fill_between(days, counts, color="#38bdf8", alpha=0.15)

    for d, v in zip(days, counts):
        if v > 0:
            ax.annotate(str(v), (d, v), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=9, color="#e2e8f0")

    ax.set_title("📈 Вопросы за 14 дней", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Кол-во")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.set_ylim(0, max(counts + [1]) + 2)
    fig.autofmt_xdate(rotation=30, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


async def pie_media_chart() -> bytes:
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT COALESCE(media_type, 'text') AS t, COUNT(*) AS n
            FROM questions GROUP BY t ORDER BY n DESC
        """)
    if not rows:
        return await _empty("Нет данных")

    labels = [r["t"] for r in rows]
    sizes = [r["n"] for r in rows]
    colors = ["#38bdf8", "#f472b6", "#facc15", "#4ade80", "#a78bfa", "#fb923c"]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.0f%%",
        colors=colors[: len(labels)],
        startangle=90, wedgeprops={"edgecolor": "#0f172a", "linewidth": 2},
        textprops={"color": "#e2e8f0", "fontsize": 11})
    for a in autotexts:
        a.set_color("#0f172a")
        a.set_fontweight("bold")
    ax.set_title("📎 Типы вопросов", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


async def _empty(text):
    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=16, color="#94a3b8")
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()