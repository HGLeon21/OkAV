"""Massage Parlor Tycoon - Main Entry Point.

A tycoon/management game where you build and run a massage parlor business.

Features:
- Hire and manage employees with unique skills and traits
- Unlock and price 8 different massage service types
- Buy and upgrade rooms from basic to VIP suites
- Upgrade reception, ambiance, equipment, and marketing
- Manage advertising to attract more clients
- Random events: celebrity visits, inspections, reviews, and more
- Day-by-day simulation with detailed financial reports
- Reputation system that affects client quality and volume

Controls:
- Mouse: Click buttons and navigate menus
- Scroll wheel: Scroll through long lists
- Space: Advance to next day / dismiss report
- Keyboard: Type parlor name on title screen
"""
from ui import GameUI


def main():
    game = GameUI()
    game.run()


if __name__ == "__main__":
    main()
