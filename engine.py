"""Game engine: day simulation, events, and business logic."""
import random
from models import (
    Client, DayResult, Employee, GameState, Room, RoomType,
    Skill, SERVICE_CATALOG, ROOM_INFO, TRAITS,
)


RANDOM_EVENTS = [
    {
        "name": "Health Inspector Visit",
        "chance": 0.05,
        "effect": lambda gs, dr: _inspector_event(gs, dr),
    },
    {
        "name": "Celebrity Client",
        "chance": 0.03,
        "effect": lambda gs, dr: _celebrity_event(gs, dr),
    },
    {
        "name": "Equipment Malfunction",
        "chance": 0.06,
        "effect": lambda gs, dr: _equipment_break(gs, dr),
    },
    {
        "name": "Great Online Review",
        "chance": 0.08,
        "effect": lambda gs, dr: _good_review(gs, dr),
    },
    {
        "name": "Bad Online Review",
        "chance": 0.05,
        "effect": lambda gs, dr: _bad_review(gs, dr),
    },
    {
        "name": "Staff Conflict",
        "chance": 0.04,
        "effect": lambda gs, dr: _staff_conflict(gs, dr),
    },
    {
        "name": "Supply Discount",
        "chance": 0.06,
        "effect": lambda gs, dr: _supply_discount(gs, dr),
    },
    {
        "name": "Local Festival Boost",
        "chance": 0.04,
        "effect": lambda gs, dr: _festival_boost(gs, dr),
    },
]


def _inspector_event(gs, dr):
    if gs.upgrades.get("ambiance", 0) >= 2:
        dr.events.append("Health Inspector: PASSED! +5 reputation")
        gs.reputation = min(100, gs.reputation + 5)
    else:
        fine = 200
        dr.events.append(f"Health Inspector: Minor violations. -${fine}, -3 reputation")
        dr.expenses += fine
        gs.reputation = max(0, gs.reputation - 3)


def _celebrity_event(gs, dr):
    bonus = 300
    dr.events.append(f"A celebrity visited! +${bonus} tip, +8 reputation")
    dr.tips += bonus
    gs.reputation = min(100, gs.reputation + 8)


def _equipment_break(gs, dr):
    cost = 150
    dr.events.append(f"Equipment broke down! -${cost} for repairs")
    dr.expenses += cost


def _good_review(gs, dr):
    boost = random.randint(3, 7)
    dr.events.append(f"Great online review! +{boost} reputation")
    gs.reputation = min(100, gs.reputation + boost)


def _bad_review(gs, dr):
    loss = random.randint(2, 5)
    dr.events.append(f"Negative online review! -{loss} reputation")
    gs.reputation = max(0, gs.reputation - loss)


def _staff_conflict(gs, dr):
    if gs.employees:
        emp = random.choice(gs.employees)
        emp.morale = max(0, emp.morale - 15)
        dr.events.append(f"Staff conflict! {emp.name}'s morale dropped.")


def _supply_discount(gs, dr):
    savings = 100
    dr.events.append(f"Supply discount! Saved ${savings} today.")
    dr.expenses = max(0, dr.expenses - savings)


def _festival_boost(gs, dr):
    dr.events.append("Local festival brings extra foot traffic! +3 bonus clients.")


def calculate_service_quality(employee: Employee, skill: Skill, room: Room, gs: GameState) -> float:
    base = employee.skills.get(skill, 1) / 5.0
    trait_mult = employee.trait_bonus()
    room_mult = room.quality
    equip_bonus = 1.0 + gs.upgrades.get("equipment", 0) * 0.15
    ambiance_bonus = 1.0 + gs.upgrades.get("ambiance", 0) * 0.1
    morale_mult = 0.5 + (employee.morale / 200.0)
    quality = base * trait_mult * room_mult * equip_bonus * ambiance_bonus * morale_mult
    return min(1.0, max(0.1, quality))


def calculate_satisfaction(quality: float, price: int, budget: int, pickiness: int) -> int:
    price_factor = 1.0
    if price > budget:
        overpay = (price - budget) / budget
        price_factor = max(0.3, 1.0 - overpay * 2)
    elif price < budget * 0.7:
        price_factor = 1.1

    quality_weight = pickiness / 100.0
    price_weight = 1.0 - quality_weight
    score = (quality * quality_weight + price_factor * price_weight) * 100
    return int(min(100, max(0, score)))


def find_best_assignment(client: Client, gs: GameState, current_minute: int):
    best_employee = None
    best_room = None
    best_quality = 0

    available_employees = [
        e for e in gs.employees
        if client.desired_service in e.skills and e.busy_until <= current_minute
    ]
    available_rooms = [r for r in gs.rooms if r.occupied_until <= current_minute]

    if not available_employees or not available_rooms:
        return None, None

    for emp in available_employees:
        for room in available_rooms:
            q = calculate_service_quality(emp, client.desired_service, room, gs)
            if q > best_quality:
                best_quality = q
                best_employee = emp
                best_room = room

    return best_employee, best_room


def simulate_day(gs: GameState) -> DayResult:
    result = DayResult(day=gs.day)
    result.expenses = gs.daily_salary_cost + gs.daily_overhead

    for emp in gs.employees:
        emp.busy_until = 0
    for room in gs.rooms:
        room.occupied_until = 0

    # Random events
    festival_bonus = 0
    for event in RANDOM_EVENTS:
        if random.random() < event["chance"]:
            event["effect"](gs, result)
            if "festival" in event["name"].lower():
                festival_bonus = 3

    # Generate clients
    num_clients = random.randint(
        max(1, gs.max_clients_per_day() // 2),
        gs.max_clients_per_day() + festival_bonus,
    )

    unlocked = gs.unlocked_services
    if not unlocked:
        result.events.append("No services available! No clients came.")
        return result

    if not gs.employees:
        result.events.append("No employees! All clients turned away.")
        result.clients_lost = num_clients
        gs.reputation = max(0, gs.reputation - 2)
        return result

    # Simulate each hour block (9 AM to 9 PM = 720 minutes)
    arrival_times = sorted([random.randint(0, 660) for _ in range(num_clients)])

    for arrival in arrival_times:
        client = Client.generate(unlocked, gs.reputation, gs.day)
        service_info = SERVICE_CATALOG[client.desired_service]
        offering = gs.services[client.desired_service]

        # Check if client can afford
        if offering.price > client.budget * 1.3:
            result.clients_lost += 1
            continue

        # Patience check based on reception upgrade
        patience_bonus = gs.upgrades.get("reception", 0) * 10
        effective_patience = client.patience + patience_bonus

        employee, room = find_best_assignment(client, gs, arrival)
        if employee is None or room is None:
            # Check if client will wait
            wait_employees = [
                e for e in gs.employees if client.desired_service in e.skills
            ]
            wait_rooms = gs.rooms
            if wait_employees and wait_rooms:
                earliest_emp = min(wait_employees, key=lambda e: e.busy_until)
                earliest_room = min(wait_rooms, key=lambda r: r.occupied_until)
                wait_time = max(earliest_emp.busy_until, earliest_room.occupied_until) - arrival
                if wait_time <= effective_patience:
                    actual_start = max(earliest_emp.busy_until, earliest_room.occupied_until)
                    employee = earliest_emp
                    room = earliest_room
                    arrival = actual_start

            if employee is None or room is None:
                result.clients_lost += 1
                continue

        # Service happens
        duration = service_info["duration"]
        employee.busy_until = arrival + duration
        room.occupied_until = arrival + duration
        employee.experience += 1

        quality = calculate_service_quality(employee, client.desired_service, room, gs)
        satisfaction = calculate_satisfaction(quality, offering.price, client.budget, client.pickiness)

        result.revenue += offering.price
        result.clients_served += 1

        # Tips based on satisfaction
        if satisfaction > 70:
            tip = int(offering.price * (satisfaction - 70) / 200)
            result.tips += tip

        # Reputation effect
        if satisfaction >= 80:
            gs.reputation = min(100, gs.reputation + 1)
        elif satisfaction < 40:
            gs.reputation = max(0, gs.reputation - 1)

        # Employee morale
        if satisfaction >= 70:
            employee.morale = min(100, employee.morale + 1)

        # Service popularity
        offering.popularity = min(100, offering.popularity + 1)

    # End of day morale decay for overworked employees
    for emp in gs.employees:
        if emp.busy_until > 600:
            emp.morale = max(0, emp.morale - 5)
        # Small daily morale recovery
        emp.morale = min(100, emp.morale + 2)

    # Natural reputation drift toward 50
    if gs.reputation > 60:
        gs.reputation = max(50, gs.reputation - 1)

    # Update finances
    gs.money += result.profit
    gs.total_clients_served += result.clients_served
    gs.total_revenue += result.revenue

    # Check game over
    if gs.money < -1000:
        gs.game_over = True
        gs.game_over_reason = "You went too deep into debt! The bank foreclosed your parlor."

    gs.day_results.append(result)
    gs.day += 1

    return result


def generate_hire_candidates(gs: GameState, count: int = 3) -> list:
    tier = 1 + gs.reputation // 30
    return [Employee.generate(gs.day, tier) for _ in range(count)]


def get_upgrade_cost(upgrade_name: str, current_level: int) -> int:
    base_costs = {
        "reception": 800,
        "ambiance": 1000,
        "equipment": 1200,
        "marketing": 600,
    }
    base = base_costs.get(upgrade_name, 1000)
    return base * (current_level + 1)


UPGRADE_DESCRIPTIONS = {
    "reception": [
        "Bare waiting area",
        "Comfortable seating & magazines",
        "Premium lounge with refreshments",
        "Luxurious reception with concierge",
    ],
    "ambiance": [
        "Basic decor",
        "Calming colors & soft music",
        "Aromatherapy diffusers & water features",
        "Full zen garden & premium sound system",
    ],
    "equipment": [
        "Standard tables",
        "Adjustable heated tables",
        "Premium hydraulic tables & tools",
        "State-of-the-art equipment suite",
    ],
    "marketing": [
        "Word of mouth only",
        "Local flyers & social media",
        "Website & online booking",
        "Full marketing team & brand presence",
    ],
}


def get_advertising_cost(level: int) -> int:
    return [0, 50, 120, 200, 350, 500][min(level, 5)]
