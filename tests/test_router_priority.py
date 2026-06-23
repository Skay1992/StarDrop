from pathlib import Path


def test_start_router_is_registered_before_fsm_routers():
    bot_py = Path("bot.py").read_text(encoding="utf-8")

    start_position = bot_py.index("dp.include_router(start.router)")
    stars_position = bot_py.index("dp.include_router(stars.router)")
    premium_position = bot_py.index("dp.include_router(premium.router)")

    assert start_position < stars_position
    assert start_position < premium_position
