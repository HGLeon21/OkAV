"""Data models for Massage Parlor Tycoon."""
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Skill(Enum):
    SWEDISH = "Swedish"
    DEEP_TISSUE = "Deep Tissue"
    HOT_STONE = "Hot Stone"
    AROMATHERAPY = "Aromatherapy"
    SPORTS = "Sports"
    REFLEXOLOGY = "Reflexology"
    SHIATSU = "Shiatsu"
    THAI = "Thai"


class RoomType(Enum):
    BASIC = "Basic Room"
    STANDARD = "Standard Room"
    DELUXE = "Deluxe Suite"
    VIP = "VIP Suite"


ROOM_INFO = {
    RoomType.BASIC: {"cost": 500, "quality": 1.0, "description": "Simple room with a massage table"},
    RoomType.STANDARD: {"cost": 2000, "quality": 1.3, "description": "Comfortable room with ambient lighting"},
    RoomType.DELUXE: {"cost": 5000, "quality": 1.6, "description": "Luxurious suite with premium amenities"},
    RoomType.VIP: {"cost": 12000, "quality": 2.0, "description": "Top-tier suite with full spa experience"},
}

SERVICE_CATALOG = {
    Skill.SWEDISH: {
        "base_price": 60, "duration": 60, "unlock_cost": 0,
        "description": "Classic relaxation massage",
    },
    Skill.DEEP_TISSUE: {
        "base_price": 80, "duration": 60, "unlock_cost": 500,
        "description": "Targets deep muscle layers",
    },
    Skill.HOT_STONE: {
        "base_price": 100, "duration": 75, "unlock_cost": 1500,
        "description": "Heated stones for deep relaxation",
    },
    Skill.AROMATHERAPY: {
        "base_price": 90, "duration": 60, "unlock_cost": 1000,
        "description": "Essential oils enhance the experience",
    },
    Skill.SPORTS: {
        "base_price": 85, "duration": 45, "unlock_cost": 800,
        "description": "Focused on athletic recovery",
    },
    Skill.REFLEXOLOGY: {
        "base_price": 70, "duration": 45, "unlock_cost": 600,
        "description": "Pressure points on hands and feet",
    },
    Skill.SHIATSU: {
        "base_price": 95, "duration": 60, "unlock_cost": 2000,
        "description": "Japanese finger pressure technique",
    },
    Skill.THAI: {
        "base_price": 110, "duration": 90, "unlock_cost": 3000,
        "description": "Stretching and deep pressure",
    },
}

FIRST_NAMES = [
    "Alex", "Jordan", "Sam", "Riley", "Casey", "Morgan", "Taylor", "Avery",
    "Quinn", "Reese", "Kai", "Skyler", "Emery", "Rowan", "Sage", "Blake",
    "Charlie", "Dakota", "Finley", "Harper", "Jamie", "Logan", "Nico", "Peyton",
    "Dana", "Ellis", "Frankie", "Hayden", "Jesse", "Kendall", "Lane", "Marley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Lee", "Garcia", "Kim", "Patel", "Chen", "Williams",
    "Brown", "Jones", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Clark", "Lewis", "Hall",
    "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams",
]

TRAITS = [
    "Friendly", "Quiet", "Energetic", "Patient", "Perfectionist",
    "Fast Learner", "Experienced", "Gentle", "Strong Hands", "Intuitive",
    "Punctual", "Charismatic", "Meticulous", "Soothing Voice", "Adaptable",
]


@dataclass
class Employee:
    name: str
    skills: dict  # Skill -> proficiency (1-5)
    salary: int
    traits: list
    morale: int = 80  # 0-100
    experience: int = 0
    hired_day: int = 0
    busy_until: int = 0  # minute of day when free

    @staticmethod
    def generate(day: int = 0, tier: int = 1) -> "Employee":
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        num_skills = random.randint(1, min(3, tier + 1))
        available_skills = random.sample(list(Skill), num_skills)
        skills = {}
        for s in available_skills:
            skills[s] = random.randint(1, min(5, tier + 2))
        avg_skill = sum(skills.values()) / len(skills)
        salary = int(30 + avg_skill * 15 + random.randint(-5, 10))
        traits = random.sample(TRAITS, random.randint(1, 3))
        return Employee(
            name=name, skills=skills, salary=salary,
            traits=traits, hired_day=day,
        )

    @property
    def skill_summary(self) -> str:
        parts = []
        for s, level in self.skills.items():
            stars = "*" * level
            parts.append(f"{s.value}: {stars}")
        return ", ".join(parts)

    def trait_bonus(self) -> float:
        bonus = 1.0
        if "Perfectionist" in self.traits:
            bonus += 0.1
        if "Experienced" in self.traits:
            bonus += 0.1
        if "Strong Hands" in self.traits:
            bonus += 0.08
        if "Gentle" in self.traits:
            bonus += 0.05
        if "Intuitive" in self.traits:
            bonus += 0.07
        if "Charismatic" in self.traits:
            bonus += 0.05
        return bonus


@dataclass
class Room:
    room_type: RoomType
    occupied_until: int = 0  # minute of day when free

    @property
    def quality(self) -> float:
        return ROOM_INFO[self.room_type]["quality"]


@dataclass
class ServiceOffering:
    skill: Skill
    price: int
    unlocked: bool = False
    popularity: int = 50  # 0-100 demand level

    @property
    def info(self):
        return SERVICE_CATALOG[self.skill]


@dataclass
class Client:
    name: str
    desired_service: Skill
    budget: int
    patience: int  # 0-100
    pickiness: int  # 0-100: how much quality matters

    @staticmethod
    def generate(unlocked_services: list, reputation: int, day: int) -> "Client":
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        service = random.choice(unlocked_services)
        base = SERVICE_CATALOG[service]["base_price"]
        budget_mult = random.uniform(0.7, 1.8) + (reputation / 500)
        budget = int(base * budget_mult)
        patience = random.randint(30, 100)
        pickiness = random.randint(10, 90)
        return Client(
            name=name, desired_service=service,
            budget=budget, patience=patience, pickiness=pickiness,
        )


@dataclass
class DayResult:
    day: int = 0
    clients_served: int = 0
    clients_lost: int = 0
    revenue: int = 0
    expenses: int = 0
    tips: int = 0
    events: list = field(default_factory=list)

    @property
    def profit(self):
        return self.revenue + self.tips - self.expenses


@dataclass
class GameState:
    parlor_name: str = "Serenity Spa"
    money: int = 5000
    day: int = 1
    reputation: int = 50  # 0-100
    employees: list = field(default_factory=list)
    rooms: list = field(default_factory=list)
    services: dict = field(default_factory=dict)
    day_results: list = field(default_factory=list)
    upgrades: dict = field(default_factory=dict)
    advertising_level: int = 0  # 0-5
    total_clients_served: int = 0
    total_revenue: int = 0
    game_over: bool = False
    game_over_reason: str = ""

    def init_defaults(self):
        self.rooms = [Room(RoomType.BASIC), Room(RoomType.BASIC)]
        self.services = {}
        for skill in Skill:
            info = SERVICE_CATALOG[skill]
            unlocked = skill == Skill.SWEDISH
            self.services[skill] = ServiceOffering(
                skill=skill, price=info["base_price"], unlocked=unlocked,
            )
        self.upgrades = {
            "reception": 0,   # 0-3: affects client patience
            "ambiance": 0,    # 0-3: affects satisfaction
            "equipment": 0,   # 0-3: affects service quality
            "marketing": 0,   # 0-3: affects client volume
        }

    @property
    def unlocked_services(self) -> list:
        return [s.skill for s in self.services.values() if s.unlocked]

    @property
    def daily_salary_cost(self) -> int:
        return sum(e.salary for e in self.employees)

    @property
    def daily_overhead(self) -> int:
        room_cost = len(self.rooms) * 10
        ad_cost = self.advertising_level * 25
        return room_cost + ad_cost

    def max_clients_per_day(self) -> int:
        base = 5 + len(self.rooms) * 2
        marketing_bonus = self.upgrades.get("marketing", 0) * 3
        ad_bonus = self.advertising_level * 2
        rep_bonus = self.reputation // 20
        return base + marketing_bonus + ad_bonus + rep_bonus
