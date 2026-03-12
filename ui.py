"""UI system for Massage Parlor Tycoon using Pygame."""
import pygame
import sys
from models import (
    GameState, Employee, Room, RoomType, Skill,
    SERVICE_CATALOG, ROOM_INFO, TRAITS,
)
from engine import (
    simulate_day, generate_hire_candidates, get_upgrade_cost,
    get_advertising_cost, UPGRADE_DESCRIPTIONS,
)


# Colors
BG_DARK = (30, 25, 35)
BG_PANEL = (45, 38, 52)
BG_HEADER = (60, 45, 75)
BG_BUTTON = (80, 60, 100)
BG_BUTTON_HOVER = (110, 85, 135)
BG_BUTTON_DISABLED = (50, 45, 55)
BG_SUCCESS = (40, 90, 60)
BG_DANGER = (130, 45, 45)
BG_WARNING = (150, 120, 30)
TEXT_WHITE = (240, 235, 245)
TEXT_LIGHT = (200, 195, 210)
TEXT_DIM = (140, 130, 155)
TEXT_GOLD = (255, 215, 100)
TEXT_GREEN = (100, 220, 120)
TEXT_RED = (240, 90, 90)
TEXT_BLUE = (100, 170, 255)
ACCENT = (170, 120, 220)
ACCENT_BRIGHT = (200, 150, 255)
BORDER = (70, 60, 85)

SCREEN_W, SCREEN_H = 1024, 768


class Button:
    def __init__(self, x, y, w, h, text, color=BG_BUTTON, hover_color=BG_BUTTON_HOVER,
                 text_color=TEXT_WHITE, enabled=True, font_size=18):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.enabled = enabled
        self.font_size = font_size
        self.hovered = False

    def draw(self, surface, font_cache):
        if not self.enabled:
            color = BG_BUTTON_DISABLED
            tc = TEXT_DIM
        elif self.hovered:
            color = self.hover_color
            tc = TEXT_WHITE
        else:
            color = self.color
            tc = self.text_color

        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BORDER, self.rect, 1, border_radius=6)

        font = font_cache.get(self.font_size)
        text_surf = font.render(self.text, True, tc)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.enabled and self.rect.collidepoint(mouse_pos)


class FontCache:
    def __init__(self):
        self._fonts = {}

    def get(self, size):
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont("segoeui,arial,helvetica", size)
        return self._fonts[size]


class ScrollableList:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.scroll_offset = 0
        self.content_height = 0
        self.items = []

    def scroll(self, dy):
        self.scroll_offset = max(0, min(self.scroll_offset + dy,
                                        max(0, self.content_height - self.rect.h)))

    def get_visible_offset(self):
        return self.scroll_offset


class GameUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Massage Parlor Tycoon")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.fonts = FontCache()
        self.running = True

        self.state = None  # "title", "playing", "game_over"
        self.screen_name = "dashboard"  # current sub-screen
        self.game = None
        self.hire_candidates = []
        self.last_day_result = None
        self.show_day_report = False
        self.message = ""
        self.message_timer = 0
        self.message_color = TEXT_GREEN
        self.scroll_offset = 0
        self.name_input = "Serenity Spa"
        self.name_editing = False

        self._init_title()

    def _init_title(self):
        self.state = "title"

    def _start_new_game(self):
        self.game = GameState(parlor_name=self.name_input)
        self.game.init_defaults()
        # Give player a starting employee
        starter = Employee.generate(0, 1)
        starter.skills[Skill.SWEDISH] = 3
        starter.salary = 40
        starter.name = "Pat Rivera"
        starter.traits = ["Friendly", "Gentle"]
        self.game.employees.append(starter)
        self.state = "playing"
        self.screen_name = "dashboard"
        self.hire_candidates = generate_hire_candidates(self.game)
        self.show_message("Welcome! Manage your parlor and grow your business!", TEXT_GREEN)

    def show_message(self, msg, color=TEXT_GREEN):
        self.message = msg
        self.message_timer = 180  # frames
        self.message_color = color

    def run(self):
        while self.running:
            dt = self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._handle_click(mouse_pos)
                    elif event.button == 4:
                        self.scroll_offset = max(0, self.scroll_offset - 30)
                    elif event.button == 5:
                        self.scroll_offset += 30
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self.screen.fill(BG_DARK)

            if self.state == "title":
                self._draw_title(mouse_pos)
            elif self.state == "playing":
                self._draw_game(mouse_pos)
            elif self.state == "game_over":
                self._draw_game_over(mouse_pos)

            if self.message_timer > 0:
                self.message_timer -= 1
                self._draw_message()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Title Screen ──────────────────────────────────────────────────

    def _draw_title(self, mouse_pos):
        font_big = self.fonts.get(52)
        font_med = self.fonts.get(24)
        font_sm = self.fonts.get(18)

        # Title
        title = font_big.render("Massage Parlor Tycoon", True, ACCENT_BRIGHT)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, y=120))

        subtitle = font_med.render("Build your relaxation empire!", True, TEXT_LIGHT)
        self.screen.blit(subtitle, subtitle.get_rect(centerx=SCREEN_W // 2, y=190))

        # Name input
        label = font_sm.render("Name your parlor:", True, TEXT_DIM)
        self.screen.blit(label, label.get_rect(centerx=SCREEN_W // 2, y=300))

        name_rect = pygame.Rect(SCREEN_W // 2 - 150, 330, 300, 40)
        border_color = ACCENT if self.name_editing else BORDER
        pygame.draw.rect(self.screen, BG_PANEL, name_rect, border_radius=4)
        pygame.draw.rect(self.screen, border_color, name_rect, 2, border_radius=4)
        name_surf = font_med.render(self.name_input, True, TEXT_WHITE)
        self.screen.blit(name_surf, (name_rect.x + 10, name_rect.y + 8))
        if self.name_editing:
            cursor_x = name_rect.x + 10 + name_surf.get_width() + 2
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.line(self.screen, TEXT_WHITE, (cursor_x, name_rect.y + 8),
                                 (cursor_x, name_rect.y + 32), 2)

        # Start button
        self._title_start_btn = Button(SCREEN_W // 2 - 100, 420, 200, 50,
                                       "Start Game", BG_SUCCESS, (60, 130, 80), font_size=22)
        self._title_start_btn.update(mouse_pos)
        self._title_start_btn.draw(self.screen, self.fonts)

        # Instructions
        instructions = [
            "Hire therapists, unlock services, upgrade your parlor",
            "Manage prices to balance profit and client satisfaction",
            "Build reputation to attract more and wealthier clients",
            "Don't go bankrupt!",
        ]
        for i, line in enumerate(instructions):
            surf = font_sm.render(line, True, TEXT_DIM)
            self.screen.blit(surf, surf.get_rect(centerx=SCREEN_W // 2, y=520 + i * 28))

        # Controls hint
        controls = font_sm.render("Controls: Mouse click to interact | Scroll to navigate lists", True, TEXT_DIM)
        self.screen.blit(controls, controls.get_rect(centerx=SCREEN_W // 2, y=680))

    # ── Main Game Screen ──────────────────────────────────────────────

    def _draw_game(self, mouse_pos):
        self._draw_top_bar()
        self._draw_nav_bar(mouse_pos)

        content_rect = pygame.Rect(0, 100, SCREEN_W, SCREEN_H - 100)
        # Draw current screen
        if self.show_day_report and self.last_day_result:
            self._draw_day_report(mouse_pos)
        elif self.screen_name == "dashboard":
            self._draw_dashboard(mouse_pos)
        elif self.screen_name == "employees":
            self._draw_employees(mouse_pos)
        elif self.screen_name == "hiring":
            self._draw_hiring(mouse_pos)
        elif self.screen_name == "services":
            self._draw_services(mouse_pos)
        elif self.screen_name == "rooms":
            self._draw_rooms(mouse_pos)
        elif self.screen_name == "upgrades":
            self._draw_upgrades(mouse_pos)
        elif self.screen_name == "finances":
            self._draw_finances(mouse_pos)

    def _draw_top_bar(self):
        pygame.draw.rect(self.screen, BG_HEADER, (0, 0, SCREEN_W, 50))
        font = self.fonts.get(16)
        font_name = self.fonts.get(20)

        name_surf = font_name.render(self.game.parlor_name, True, ACCENT_BRIGHT)
        self.screen.blit(name_surf, (15, 14))

        # Stats
        stats = [
            (f"Day {self.game.day}", TEXT_WHITE),
            (f"${self.game.money:,}", TEXT_GREEN if self.game.money >= 0 else TEXT_RED),
            (f"Rep: {self.game.reputation}/100", TEXT_GOLD),
            (f"Staff: {len(self.game.employees)}", TEXT_BLUE),
            (f"Rooms: {len(self.game.rooms)}", TEXT_LIGHT),
        ]
        x = SCREEN_W - 15
        for text, color in reversed(stats):
            surf = font.render(text, True, color)
            x -= surf.get_width() + 20
            self.screen.blit(surf, (x, 17))

    def _draw_nav_bar(self, mouse_pos):
        pygame.draw.rect(self.screen, BG_PANEL, (0, 50, SCREEN_W, 50))
        nav_items = [
            ("Dashboard", "dashboard"), ("Employees", "employees"),
            ("Hire", "hiring"), ("Services", "services"),
            ("Rooms", "rooms"), ("Upgrades", "upgrades"),
            ("Finances", "finances"),
        ]
        self._nav_buttons = []
        btn_w = 130
        start_x = 10
        for i, (label, screen) in enumerate(nav_items):
            color = ACCENT if self.screen_name == screen else BG_BUTTON
            btn = Button(start_x + i * (btn_w + 5), 55, btn_w, 38, label,
                         color=color, font_size=15)
            btn.update(mouse_pos)
            btn.draw(self.screen, self.fonts)
            self._nav_buttons.append((btn, screen))

        # Next Day button
        self._next_day_btn = Button(SCREEN_W - 140, 55, 130, 38, ">> Next Day",
                                    BG_SUCCESS, (60, 130, 80), font_size=15)
        self._next_day_btn.update(mouse_pos)
        self._next_day_btn.draw(self.screen, self.fonts)

    # ── Dashboard ─────────────────────────────────────────────────────

    def _draw_dashboard(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Dashboard", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        # Quick stats cards
        cards = [
            ("Money", f"${self.game.money:,}", TEXT_GREEN if self.game.money >= 0 else TEXT_RED),
            ("Reputation", f"{self.game.reputation}/100", TEXT_GOLD),
            ("Employees", str(len(self.game.employees)), TEXT_BLUE),
            ("Rooms", str(len(self.game.rooms)), TEXT_LIGHT),
            ("Services", str(len(self.game.unlocked_services)), ACCENT_BRIGHT),
            ("Daily Costs", f"${self.game.daily_salary_cost + self.game.daily_overhead}", TEXT_RED),
        ]
        card_w = 150
        card_h = 80
        for i, (label, value, color) in enumerate(cards):
            cx = 20 + (i % 6) * (card_w + 12)
            cy = y
            pygame.draw.rect(self.screen, BG_PANEL, (cx, cy, card_w, card_h), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (cx, cy, card_w, card_h), 1, border_radius=8)
            label_surf = font_sm.render(label, True, TEXT_DIM)
            self.screen.blit(label_surf, label_surf.get_rect(centerx=cx + card_w // 2, y=cy + 10))
            val_surf = font.render(value, True, color)
            self.screen.blit(val_surf, val_surf.get_rect(centerx=cx + card_w // 2, y=cy + 40))
        y += card_h + 20

        # Employee summary
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 200), border_radius=8)
        header = font.render("Employee Overview", True, ACCENT_BRIGHT)
        self.screen.blit(header, (35, y + 10))
        ey = y + 40
        if not self.game.employees:
            msg = font_sm.render("No employees yet! Go to Hire tab to recruit.", True, TEXT_DIM)
            self.screen.blit(msg, (35, ey))
        else:
            for emp in self.game.employees[:5]:
                morale_color = TEXT_GREEN if emp.morale >= 60 else TEXT_RED if emp.morale < 40 else TEXT_GOLD
                line = f"{emp.name}  |  Morale: {emp.morale}%  |  Salary: ${emp.salary}/day  |  Skills: {emp.skill_summary}"
                surf = font_sm.render(line, True, TEXT_LIGHT)
                self.screen.blit(surf, (35, ey))
                ey += 24
            if len(self.game.employees) > 5:
                more = font_sm.render(f"...and {len(self.game.employees) - 5} more (see Employees tab)", True, TEXT_DIM)
                self.screen.blit(more, (35, ey))
        y += 215

        # Recent history
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 200), border_radius=8)
        header = font.render("Recent Days", True, ACCENT_BRIGHT)
        self.screen.blit(header, (35, y + 10))
        hy = y + 40
        recent = self.game.day_results[-5:] if self.game.day_results else []
        if not recent:
            msg = font_sm.render("No history yet. Click 'Next Day' to begin!", True, TEXT_DIM)
            self.screen.blit(msg, (35, hy))
        else:
            for dr in reversed(recent):
                profit_color = TEXT_GREEN if dr.profit >= 0 else TEXT_RED
                line = (f"Day {dr.day}: Served {dr.clients_served} clients, "
                        f"Lost {dr.clients_lost} | Revenue: ${dr.revenue} | "
                        f"Profit: ${dr.profit:+d}")
                surf = font_sm.render(line, True, TEXT_LIGHT)
                self.screen.blit(surf, (35, hy))
                hy += 24

        # Totals
        y += 215
        totals = font.render(
            f"Lifetime: {self.game.total_clients_served} clients served | "
            f"${self.game.total_revenue:,} total revenue",
            True, TEXT_DIM
        )
        self.screen.blit(totals, (20, y))

    # ── Employees ─────────────────────────────────────────────────────

    def _draw_employees(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Employees", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        self._fire_buttons = []

        if not self.game.employees:
            msg = font.render("No employees. Visit the Hire tab!", True, TEXT_DIM)
            self.screen.blit(msg, (20, y))
            return

        for i, emp in enumerate(self.game.employees):
            if y - self.scroll_offset > SCREEN_H:
                break
            if y - self.scroll_offset < 90:
                y += 130
                continue

            draw_y = y - self.scroll_offset
            pygame.draw.rect(self.screen, BG_PANEL, (20, draw_y, SCREEN_W - 40, 120), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (20, draw_y, SCREEN_W - 40, 120), 1, border_radius=8)

            name_surf = font.render(emp.name, True, TEXT_WHITE)
            self.screen.blit(name_surf, (35, draw_y + 10))

            salary_surf = font_sm.render(f"Salary: ${emp.salary}/day", True, TEXT_GOLD)
            self.screen.blit(salary_surf, (35, draw_y + 35))

            morale_color = TEXT_GREEN if emp.morale >= 60 else TEXT_RED if emp.morale < 40 else TEXT_GOLD
            morale_surf = font_sm.render(f"Morale: {emp.morale}%", True, morale_color)
            self.screen.blit(morale_surf, (200, draw_y + 35))

            exp_surf = font_sm.render(f"Experience: {emp.experience} sessions", True, TEXT_BLUE)
            self.screen.blit(exp_surf, (350, draw_y + 35))

            skills_surf = font_sm.render(f"Skills: {emp.skill_summary}", True, TEXT_LIGHT)
            self.screen.blit(skills_surf, (35, draw_y + 60))

            traits_surf = font_sm.render(f"Traits: {', '.join(emp.traits)}", True, TEXT_DIM)
            self.screen.blit(traits_surf, (35, draw_y + 82))

            # Fire button
            fire_btn = Button(SCREEN_W - 130, draw_y + 10, 90, 30, "Fire",
                              BG_DANGER, (170, 60, 60), font_size=14)
            fire_btn.update(mouse_pos)
            fire_btn.draw(self.screen, self.fonts)
            self._fire_buttons.append((fire_btn, i))

            # Raise salary button
            raise_btn = Button(SCREEN_W - 130, draw_y + 48, 90, 30, "Raise +$5",
                               BG_BUTTON, font_size=14)
            raise_btn.update(mouse_pos)
            raise_btn.draw(self.screen, self.fonts)
            self._fire_buttons.append((raise_btn, -(i + 100)))  # negative = raise

            y += 130

    # ── Hiring ────────────────────────────────────────────────────────

    def _draw_hiring(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Hire New Employees", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 10

        cost_note = font_sm.render("(Higher reputation attracts better candidates)", True, TEXT_DIM)
        self.screen.blit(cost_note, (20, y + 30)); y += 65

        self._hire_buttons = []

        for i, emp in enumerate(self.hire_candidates):
            draw_y = y
            pygame.draw.rect(self.screen, BG_PANEL, (20, draw_y, SCREEN_W - 40, 130), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (20, draw_y, SCREEN_W - 40, 130), 1, border_radius=8)

            name_surf = font.render(emp.name, True, TEXT_WHITE)
            self.screen.blit(name_surf, (35, draw_y + 10))

            salary_surf = font_sm.render(f"Wants: ${emp.salary}/day", True, TEXT_GOLD)
            self.screen.blit(salary_surf, (35, draw_y + 38))

            skills_surf = font_sm.render(f"Skills: {emp.skill_summary}", True, TEXT_LIGHT)
            self.screen.blit(skills_surf, (35, draw_y + 62))

            traits_surf = font_sm.render(f"Traits: {', '.join(emp.traits)}", True, TEXT_DIM)
            self.screen.blit(traits_surf, (35, draw_y + 86))

            hire_btn = Button(SCREEN_W - 130, draw_y + 15, 90, 35, "Hire",
                              BG_SUCCESS, (60, 130, 80), font_size=16)
            hire_btn.update(mouse_pos)
            hire_btn.draw(self.screen, self.fonts)
            self._hire_buttons.append((hire_btn, i))

            y += 145

        # Refresh candidates button
        y += 10
        self._refresh_btn = Button(20, y, 200, 40, "Refresh Candidates ($50)",
                                   BG_BUTTON, font_size=16,
                                   enabled=self.game.money >= 50)
        self._refresh_btn.update(mouse_pos)
        self._refresh_btn.draw(self.screen, self.fonts)

    # ── Services ──────────────────────────────────────────────────────

    def _draw_services(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Services & Pricing", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        self._service_buttons = []

        for skill, offering in self.game.services.items():
            if y - self.scroll_offset > SCREEN_H:
                break
            if y - self.scroll_offset < 90:
                y += 85
                continue

            draw_y = y - self.scroll_offset
            info = SERVICE_CATALOG[skill]
            color = BG_PANEL if offering.unlocked else (35, 30, 40)
            pygame.draw.rect(self.screen, color, (20, draw_y, SCREEN_W - 40, 75), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (20, draw_y, SCREEN_W - 40, 75), 1, border_radius=8)

            status = "" if offering.unlocked else " [LOCKED]"
            name_surf = font.render(f"{skill.value}{status}", True,
                                    TEXT_WHITE if offering.unlocked else TEXT_DIM)
            self.screen.blit(name_surf, (35, draw_y + 8))

            desc = font_sm.render(info["description"], True, TEXT_DIM)
            self.screen.blit(desc, (35, draw_y + 32))

            dur = font_sm.render(f"{info['duration']}min", True, TEXT_LIGHT)
            self.screen.blit(dur, (35, draw_y + 52))

            if offering.unlocked:
                price_surf = font.render(f"${offering.price}", True, TEXT_GREEN)
                self.screen.blit(price_surf, (500, draw_y + 10))

                pop_surf = font_sm.render(f"Popularity: {offering.popularity}%", True, TEXT_BLUE)
                self.screen.blit(pop_surf, (500, draw_y + 38))

                # Price adjustment buttons
                minus_btn = Button(SCREEN_W - 220, draw_y + 10, 40, 30, "-$5", font_size=14)
                plus_btn = Button(SCREEN_W - 170, draw_y + 10, 40, 30, "+$5", font_size=14)
                minus10_btn = Button(SCREEN_W - 120, draw_y + 10, 45, 30, "-$10", font_size=14)
                plus10_btn = Button(SCREEN_W - 68, draw_y + 10, 45, 30, "+$10", font_size=14)
                for btn in [minus_btn, plus_btn, minus10_btn, plus10_btn]:
                    btn.update(mouse_pos)
                    btn.draw(self.screen, self.fonts)
                self._service_buttons.append((minus_btn, skill, -5))
                self._service_buttons.append((plus_btn, skill, 5))
                self._service_buttons.append((minus10_btn, skill, -10))
                self._service_buttons.append((plus10_btn, skill, 10))
            else:
                cost = info["unlock_cost"]
                unlock_btn = Button(SCREEN_W - 180, draw_y + 15, 150, 35,
                                    f"Unlock (${cost})", BG_SUCCESS, (60, 130, 80),
                                    font_size=14, enabled=self.game.money >= cost)
                unlock_btn.update(mouse_pos)
                unlock_btn.draw(self.screen, self.fonts)
                self._service_buttons.append((unlock_btn, skill, 0))  # 0 = unlock

            y += 85

    # ── Rooms ─────────────────────────────────────────────────────────

    def _draw_rooms(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Rooms", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        # Current rooms
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 30 + len(self.game.rooms) * 28),
                         border_radius=8)
        header = font.render("Current Rooms:", True, ACCENT_BRIGHT)
        self.screen.blit(header, (35, y + 5))
        ry = y + 32
        room_counts = {}
        for room in self.game.rooms:
            room_counts[room.room_type] = room_counts.get(room.room_type, 0) + 1
        for rt, count in room_counts.items():
            info = ROOM_INFO[rt]
            line = f"{count}x {rt.value} (Quality: {info['quality']}x) - {info['description']}"
            surf = font_sm.render(line, True, TEXT_LIGHT)
            self.screen.blit(surf, (35, ry))
            ry += 28
        y = ry + 20

        # Buy rooms
        header2 = font.render("Buy New Room:", True, TEXT_WHITE)
        self.screen.blit(header2, (20, y)); y += 35

        self._room_buttons = []
        for rt in RoomType:
            info = ROOM_INFO[rt]
            cost = info["cost"]
            pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 60), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (20, y, SCREEN_W - 40, 60), 1, border_radius=8)

            name_surf = font.render(f"{rt.value}", True, TEXT_WHITE)
            self.screen.blit(name_surf, (35, y + 8))

            desc_surf = font_sm.render(f"{info['description']} | Quality: {info['quality']}x", True, TEXT_DIM)
            self.screen.blit(desc_surf, (35, y + 32))

            buy_btn = Button(SCREEN_W - 170, y + 12, 140, 35, f"Buy (${cost:,})",
                             BG_SUCCESS, (60, 130, 80), font_size=15,
                             enabled=self.game.money >= cost)
            buy_btn.update(mouse_pos)
            buy_btn.draw(self.screen, self.fonts)
            self._room_buttons.append((buy_btn, rt))

            y += 70

    # ── Upgrades ──────────────────────────────────────────────────────

    def _draw_upgrades(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Upgrades", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        self._upgrade_buttons = []

        for upgrade_name, current_level in self.game.upgrades.items():
            max_level = 3
            descriptions = UPGRADE_DESCRIPTIONS.get(upgrade_name, [""] * 4)

            pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 100), border_radius=8)
            pygame.draw.rect(self.screen, BORDER, (20, y, SCREEN_W - 40, 100), 1, border_radius=8)

            name_surf = font.render(upgrade_name.title(), True, TEXT_WHITE)
            self.screen.blit(name_surf, (35, y + 10))

            # Level indicators
            for lvl in range(max_level + 1):
                color = ACCENT if lvl <= current_level else (50, 45, 55)
                pygame.draw.rect(self.screen, color, (250 + lvl * 30, y + 14, 22, 16), border_radius=3)

            current_desc = descriptions[min(current_level, len(descriptions) - 1)]
            desc_surf = font_sm.render(f"Current: {current_desc}", True, TEXT_LIGHT)
            self.screen.blit(desc_surf, (35, y + 40))

            if current_level < max_level:
                cost = get_upgrade_cost(upgrade_name, current_level)
                next_desc = descriptions[min(current_level + 1, len(descriptions) - 1)]
                next_surf = font_sm.render(f"Next: {next_desc}", True, TEXT_DIM)
                self.screen.blit(next_surf, (35, y + 62))

                up_btn = Button(SCREEN_W - 180, y + 15, 150, 35,
                                f"Upgrade (${cost:,})", BG_SUCCESS, (60, 130, 80),
                                font_size=14, enabled=self.game.money >= cost)
                up_btn.update(mouse_pos)
                up_btn.draw(self.screen, self.fonts)
                self._upgrade_buttons.append((up_btn, upgrade_name))
            else:
                max_surf = font_sm.render("MAX LEVEL", True, TEXT_GOLD)
                self.screen.blit(max_surf, (SCREEN_W - 130, y + 25))

            y += 115

        # Advertising
        y += 10
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 80), border_radius=8)
        pygame.draw.rect(self.screen, BORDER, (20, y, SCREEN_W - 40, 80), 1, border_radius=8)

        ad_name = font.render("Advertising Level", True, TEXT_WHITE)
        self.screen.blit(ad_name, (35, y + 10))

        for lvl in range(6):
            color = ACCENT if lvl <= self.game.advertising_level else (50, 45, 55)
            pygame.draw.rect(self.screen, color, (250 + lvl * 30, y + 14, 22, 16), border_radius=3)

        ad_cost = get_advertising_cost(self.game.advertising_level)
        cost_surf = font_sm.render(f"Daily cost: ${ad_cost}", True, TEXT_GOLD)
        self.screen.blit(cost_surf, (35, y + 40))

        if self.game.advertising_level < 5:
            plus_btn = Button(SCREEN_W - 130, y + 10, 50, 28, "+", font_size=16)
            plus_btn.update(mouse_pos)
            plus_btn.draw(self.screen, self.fonts)
            self._upgrade_buttons.append((plus_btn, "ad_up"))

        if self.game.advertising_level > 0:
            minus_btn = Button(SCREEN_W - 70, y + 10, 50, 28, "-", font_size=16)
            minus_btn.update(mouse_pos)
            minus_btn.draw(self.screen, self.fonts)
            self._upgrade_buttons.append((minus_btn, "ad_down"))

    # ── Finances ──────────────────────────────────────────────────────

    def _draw_finances(self, mouse_pos):
        y = 110
        font_title = self.fonts.get(28)
        font = self.fonts.get(18)
        font_sm = self.fonts.get(15)

        title = font_title.render("Financial Overview", True, TEXT_WHITE)
        self.screen.blit(title, (20, y)); y += 45

        # Summary panel
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 140), border_radius=8)
        items = [
            ("Current Balance", f"${self.game.money:,}",
             TEXT_GREEN if self.game.money >= 0 else TEXT_RED),
            ("Daily Salaries", f"-${self.game.daily_salary_cost}", TEXT_RED),
            ("Daily Overhead", f"-${self.game.daily_overhead}", TEXT_RED),
            ("Total Daily Costs", f"-${self.game.daily_salary_cost + self.game.daily_overhead}", TEXT_RED),
            ("Lifetime Revenue", f"${self.game.total_revenue:,}", TEXT_GREEN),
        ]
        fy = y + 10
        for label, value, color in items:
            label_surf = font_sm.render(label, True, TEXT_DIM)
            val_surf = font_sm.render(value, True, color)
            self.screen.blit(label_surf, (35, fy))
            self.screen.blit(val_surf, (300, fy))
            fy += 24
        y += 155

        # Day-by-day chart (simple text table)
        pygame.draw.rect(self.screen, BG_PANEL, (20, y, SCREEN_W - 40, 380), border_radius=8)
        header = font.render("Daily History (last 12 days)", True, ACCENT_BRIGHT)
        self.screen.blit(header, (35, y + 10))

        # Table header
        hy = y + 42
        cols = ["Day", "Clients", "Lost", "Revenue", "Tips", "Expenses", "Profit"]
        col_x = [35, 100, 180, 260, 370, 470, 590]
        for ci, col in enumerate(cols):
            surf = font_sm.render(col, True, TEXT_DIM)
            self.screen.blit(surf, (col_x[ci], hy))
        hy += 24
        pygame.draw.line(self.screen, BORDER, (35, hy), (SCREEN_W - 55, hy))
        hy += 5

        recent = self.game.day_results[-12:]
        for dr in reversed(recent):
            profit_color = TEXT_GREEN if dr.profit >= 0 else TEXT_RED
            row = [
                (str(dr.day), TEXT_LIGHT),
                (str(dr.clients_served), TEXT_WHITE),
                (str(dr.clients_lost), TEXT_RED if dr.clients_lost > 0 else TEXT_DIM),
                (f"${dr.revenue}", TEXT_GREEN),
                (f"${dr.tips}", TEXT_GOLD),
                (f"${dr.expenses}", TEXT_RED),
                (f"${dr.profit:+d}", profit_color),
            ]
            for ci, (val, color) in enumerate(row):
                surf = font_sm.render(val, True, color)
                self.screen.blit(surf, (col_x[ci], hy))
            hy += 24

    # ── Day Report ────────────────────────────────────────────────────

    def _draw_day_report(self, mouse_pos):
        dr = self.last_day_result
        font_title = self.fonts.get(28)
        font = self.fonts.get(20)
        font_sm = self.fonts.get(16)

        # Overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Report panel
        panel_w, panel_h = 600, 500
        px = (SCREEN_W - panel_w) // 2
        py = (SCREEN_H - panel_h) // 2
        pygame.draw.rect(self.screen, BG_PANEL, (px, py, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(self.screen, ACCENT, (px, py, panel_w, panel_h), 2, border_radius=12)

        title = font_title.render(f"Day {dr.day} Report", True, TEXT_WHITE)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, y=py + 20))

        y = py + 65
        stats = [
            ("Clients Served", str(dr.clients_served), TEXT_GREEN),
            ("Clients Lost", str(dr.clients_lost), TEXT_RED if dr.clients_lost > 0 else TEXT_DIM),
            ("Revenue", f"${dr.revenue}", TEXT_GREEN),
            ("Tips", f"${dr.tips}", TEXT_GOLD),
            ("Expenses", f"${dr.expenses}", TEXT_RED),
            ("", "", TEXT_WHITE),
            ("Net Profit", f"${dr.profit:+d}", TEXT_GREEN if dr.profit >= 0 else TEXT_RED),
        ]
        for label, value, color in stats:
            if label:
                label_surf = font_sm.render(label, True, TEXT_LIGHT)
                val_surf = font.render(value, True, color)
                self.screen.blit(label_surf, (px + 40, y))
                self.screen.blit(val_surf, (px + panel_w - 40 - val_surf.get_width(), y))
            y += 30

        # Events
        if dr.events:
            y += 10
            event_header = font_sm.render("Events:", True, ACCENT_BRIGHT)
            self.screen.blit(event_header, (px + 40, y))
            y += 25
            for ev in dr.events[:5]:
                ev_surf = font_sm.render(f"  {ev}", True, TEXT_LIGHT)
                self.screen.blit(ev_surf, (px + 40, y))
                y += 22

        # Close button
        self._report_close_btn = Button(px + panel_w // 2 - 60, py + panel_h - 55,
                                        120, 40, "Continue", BG_SUCCESS, (60, 130, 80))
        self._report_close_btn.update(mouse_pos)
        self._report_close_btn.draw(self.screen, self.fonts)

    # ── Game Over ─────────────────────────────────────────────────────

    def _draw_game_over(self, mouse_pos):
        font_big = self.fonts.get(48)
        font_med = self.fonts.get(22)
        font_sm = self.fonts.get(18)

        title = font_big.render("GAME OVER", True, TEXT_RED)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, y=200))

        reason = font_med.render(self.game.game_over_reason, True, TEXT_LIGHT)
        self.screen.blit(reason, reason.get_rect(centerx=SCREEN_W // 2, y=280))

        stats = [
            f"Days survived: {self.game.day - 1}",
            f"Total clients served: {self.game.total_clients_served}",
            f"Total revenue earned: ${self.game.total_revenue:,}",
            f"Final reputation: {self.game.reputation}/100",
        ]
        for i, line in enumerate(stats):
            surf = font_sm.render(line, True, TEXT_DIM)
            self.screen.blit(surf, surf.get_rect(centerx=SCREEN_W // 2, y=340 + i * 30))

        self._restart_btn = Button(SCREEN_W // 2 - 80, 500, 160, 50, "Play Again",
                                   BG_SUCCESS, (60, 130, 80), font_size=22)
        self._restart_btn.update(mouse_pos)
        self._restart_btn.draw(self.screen, self.fonts)

    # ── Message ───────────────────────────────────────────────────────

    def _draw_message(self):
        font = self.fonts.get(16)
        alpha = min(255, self.message_timer * 3)
        surf = font.render(self.message, True, self.message_color)
        msg_rect = surf.get_rect(centerx=SCREEN_W // 2, y=SCREEN_H - 40)
        bg = pygame.Surface((msg_rect.w + 20, msg_rect.h + 10), pygame.SRCALPHA)
        bg.fill((30, 25, 35, alpha))
        self.screen.blit(bg, (msg_rect.x - 10, msg_rect.y - 5))
        self.screen.blit(surf, msg_rect)

    # ── Input Handling ────────────────────────────────────────────────

    def _handle_click(self, pos):
        if self.state == "title":
            self._handle_title_click(pos)
        elif self.state == "playing":
            self._handle_game_click(pos)
        elif self.state == "game_over":
            if hasattr(self, '_restart_btn') and self._restart_btn.clicked(pos):
                self.name_input = "Serenity Spa"
                self._init_title()

    def _handle_title_click(self, pos):
        name_rect = pygame.Rect(SCREEN_W // 2 - 150, 330, 300, 40)
        self.name_editing = name_rect.collidepoint(pos)

        if hasattr(self, '_title_start_btn') and self._title_start_btn.clicked(pos):
            if self.name_input.strip():
                self._start_new_game()

    def _handle_game_click(self, pos):
        # Day report close
        if self.show_day_report:
            if hasattr(self, '_report_close_btn') and self._report_close_btn.clicked(pos):
                self.show_day_report = False
                if self.game.game_over:
                    self.state = "game_over"
            return

        # Nav buttons
        if hasattr(self, '_nav_buttons'):
            for btn, screen in self._nav_buttons:
                if btn.clicked(pos):
                    self.screen_name = screen
                    self.scroll_offset = 0
                    return

        # Next day
        if hasattr(self, '_next_day_btn') and self._next_day_btn.clicked(pos):
            self.last_day_result = simulate_day(self.game)
            self.show_day_report = True
            self.hire_candidates = generate_hire_candidates(self.game)
            return

        # Screen-specific clicks
        if self.screen_name == "employees":
            self._handle_employee_clicks(pos)
        elif self.screen_name == "hiring":
            self._handle_hiring_clicks(pos)
        elif self.screen_name == "services":
            self._handle_service_clicks(pos)
        elif self.screen_name == "rooms":
            self._handle_room_clicks(pos)
        elif self.screen_name == "upgrades":
            self._handle_upgrade_clicks(pos)

    def _handle_employee_clicks(self, pos):
        if not hasattr(self, '_fire_buttons'):
            return
        for btn, idx in self._fire_buttons:
            if btn.clicked(pos):
                if idx >= 0:
                    emp = self.game.employees[idx]
                    self.game.employees.pop(idx)
                    self.show_message(f"Fired {emp.name}.", TEXT_RED)
                else:
                    real_idx = -(idx + 100)
                    if real_idx < len(self.game.employees):
                        emp = self.game.employees[real_idx]
                        emp.salary += 5
                        emp.morale = min(100, emp.morale + 10)
                        self.show_message(f"Gave {emp.name} a raise! Morale improved.", TEXT_GREEN)
                return

    def _handle_hiring_clicks(self, pos):
        if hasattr(self, '_hire_buttons'):
            for btn, idx in self._hire_buttons:
                if btn.clicked(pos) and idx < len(self.hire_candidates):
                    emp = self.hire_candidates[idx]
                    self.game.employees.append(emp)
                    self.hire_candidates.pop(idx)
                    self.show_message(f"Hired {emp.name}! (${emp.salary}/day)", TEXT_GREEN)
                    return

        if hasattr(self, '_refresh_btn') and self._refresh_btn.clicked(pos):
            if self.game.money >= 50:
                self.game.money -= 50
                self.hire_candidates = generate_hire_candidates(self.game)
                self.show_message("New candidates available! (-$50)", TEXT_BLUE)

    def _handle_service_clicks(self, pos):
        if not hasattr(self, '_service_buttons'):
            return
        for btn, skill, delta in self._service_buttons:
            if btn.clicked(pos):
                offering = self.game.services[skill]
                if delta == 0:  # unlock
                    cost = SERVICE_CATALOG[skill]["unlock_cost"]
                    if self.game.money >= cost:
                        self.game.money -= cost
                        offering.unlocked = True
                        self.show_message(f"Unlocked {skill.value}! (-${cost})", TEXT_GREEN)
                else:
                    offering.price = max(10, offering.price + delta)
                    self.show_message(f"{skill.value} price: ${offering.price}", TEXT_LIGHT)
                return

    def _handle_room_clicks(self, pos):
        if not hasattr(self, '_room_buttons'):
            return
        for btn, rt in self._room_buttons:
            if btn.clicked(pos):
                cost = ROOM_INFO[rt]["cost"]
                if self.game.money >= cost:
                    self.game.money -= cost
                    self.game.rooms.append(Room(rt))
                    self.show_message(f"Added {rt.value}! (-${cost:,})", TEXT_GREEN)
                return

    def _handle_upgrade_clicks(self, pos):
        if not hasattr(self, '_upgrade_buttons'):
            return
        for btn, name in self._upgrade_buttons:
            if btn.clicked(pos):
                if name == "ad_up":
                    self.game.advertising_level = min(5, self.game.advertising_level + 1)
                    self.show_message(f"Advertising level: {self.game.advertising_level}", TEXT_BLUE)
                elif name == "ad_down":
                    self.game.advertising_level = max(0, self.game.advertising_level - 1)
                    self.show_message(f"Advertising level: {self.game.advertising_level}", TEXT_BLUE)
                else:
                    current = self.game.upgrades[name]
                    cost = get_upgrade_cost(name, current)
                    if self.game.money >= cost and current < 3:
                        self.game.money -= cost
                        self.game.upgrades[name] = current + 1
                        self.show_message(f"Upgraded {name}! (-${cost:,})", TEXT_GREEN)
                return

    def _handle_key(self, event):
        if self.state == "title" and self.name_editing:
            if event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.name_editing = False
            elif len(self.name_input) < 30 and event.unicode.isprintable():
                self.name_input += event.unicode
        elif self.state == "playing":
            if event.key == pygame.K_SPACE:
                if self.show_day_report:
                    self.show_day_report = False
                    if self.game.game_over:
                        self.state = "game_over"
                else:
                    self.last_day_result = simulate_day(self.game)
                    self.show_day_report = True
                    self.hire_candidates = generate_hire_candidates(self.game)
