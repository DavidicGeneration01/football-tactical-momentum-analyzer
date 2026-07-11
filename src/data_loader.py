#Load match events, or make sample data when no CSV exists.

from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    DEFAULT_MIN_EVENTS,
    PITCH_LENGTH,
    PITCH_WIDTH,
    RANDOM_SEED,
    RAW_EVENTS_FILE,
    TEAMS,
)
from logger import get_logger

log = get_logger(__name__)

EVENT_TYPES = [
    "Pass",
    "Progressive Pass",
    "Dangerous Pass",
    "Cross",
    "Shot",
    "Shot on Target",
    "Goal",
    "Big Chance",
    "Successful Dribble",
    "Tackle",
    "Interception",
    "Corner",
    "Foul",
    "Yellow Card",
    "Red Card",
    "Turnover",
    "Offside",
]

# loose event mix, enough to make the fake matches feel believable
EVENT_WEIGHTS = [
    28, 9, 6, 5, 4, 2, 0.4, 1.2, 6, 8, 7, 2, 6, 1.2, 0.1, 8, 1.1,
]

FIRST_NAMES = [
    "Chidi", "Emeka", "Uche", "Ifeanyi", "Chinedu", "Obinna", "Kelechi",
    "Ikechukwu", "Tunde", "Segun", "Bayo", "Femi", "Kunle", "Wale", "Yemi",
    "Damilare", "Abdullahi", "Musa", "Ibrahim", "Sani", "Aliyu", "Suleiman",
    "Yusuf", "Godwin", "Success", "Victor", "Samuel", "Daniel", "Peter",
    "Emmanuel", "Joseph", "Divine", "Praise", "Chukwuemeka", "Olamide",
    "Rasheed", "Abubakar", "Chibuzor", "Ejike", "Adewale",
]
LAST_NAMES = [
    "Okoye", "Nwankwo", "Eze", "Okafor", "Adeyemi", "Adebayo", "Ogundele",
    "Bello", "Abubakar", "Mohammed", "Yakubu", "Danjuma", "Etim", "Effiong",
    "Okonkwo", "Nnamdi", "Chukwu", "Balogun", "Afolabi", "Oyelaran", "Sanni",
    "Garba", "Usman", "Lawal", "Onuoha", "Ndukwe", "Ogbeide", "Osazuwa",
    "Ibrahim", "Mustapha", "Egwuekwe", "Ojo", "Adisa", "Ekong", "Chukwuma",
]

POSITIONS = ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]


def _build_squad(team: str, rng: np.random.Generator) -> pd.DataFrame:
    names = rng.choice(FIRST_NAMES, size=16, replace=True)
    surnames = rng.choice(LAST_NAMES, size=16, replace=True)
    players = [f"{f} {s}" for f, s in zip(names, surnames)]
    positions = list(rng.choice(POSITIONS, size=16, replace=True))
    return pd.DataFrame(
        {
            "team": team,
            "player": players,
            "position": positions,
            "shirt_number": rng.choice(range(1, 30), size=16, replace=False),
        }
    )


def generate_synthetic_events(
    n_events: int = DEFAULT_MIN_EVENTS,
    n_matches: int = 6,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Make the fake match feed used when I do not have real data yet."""
    rng = np.random.default_rng(seed)
    per_match = max(n_events // n_matches, 400)

    all_rows = []
    match_id = 0

    for _ in range(n_matches):
        match_id += 1
        home, away = rng.choice(TEAMS, size=2, replace=False) if len(TEAMS) > 2 else TEAMS
        squads = {
            home: _build_squad(home, rng),
            away: _build_squad(away, rng),
        }

        for i in range(per_match):
            team = home if rng.random() < 0.52 else away
            opponent = away if team == home else home
            squad = squads[team]
            player_row = squad.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]

            event_type = rng.choice(EVENT_TYPES, p=np.array(EVENT_WEIGHTS) / sum(EVENT_WEIGHTS))
            minute = int(min(90, (i / per_match) * 90 + rng.normal(0, 1.5)))
            minute = max(0, minute)
            second = int(rng.integers(0, 60))

            # attacking stuff should happen closer to goal
            if event_type in ("Shot", "Shot on Target", "Goal", "Big Chance"):
                x = rng.uniform(88, 120)
                y = rng.normal(40, 14)
            elif event_type in ("Dangerous Pass", "Cross", "Corner"):
                x = rng.uniform(70, 118)
                y = rng.normal(40, 22)
            elif event_type in ("Tackle", "Interception", "Foul", "Turnover"):
                x = rng.uniform(10, 90)
                y = rng.normal(40, 20)
            else:
                x = rng.uniform(0, 120)
                y = rng.normal(40, 20)

            x = float(np.clip(x, 0, PITCH_LENGTH))
            y = float(np.clip(y, 0, PITCH_WIDTH))

            outcome = "Complete"
            if event_type in ("Pass", "Progressive Pass", "Dangerous Pass", "Cross"):
                outcome = "Complete" if rng.random() < 0.82 else "Incomplete"
            elif event_type in ("Shot", "Shot on Target", "Big Chance"):
                outcome = "On Target" if rng.random() < 0.4 else "Off Target"
            elif event_type == "Goal":
                outcome = "Goal"

            xg = 0.0
            if event_type in ("Shot", "Shot on Target", "Goal", "Big Chance"):
                dist_to_goal = np.hypot(PITCH_LENGTH - x, y - 40)
                xg = float(np.clip(0.5 - dist_to_goal / 90, 0.02, 0.85))
                if event_type == "Big Chance":
                    xg = float(np.clip(xg + 0.25, 0.05, 0.9))
                if event_type == "Goal":
                    xg = float(np.clip(xg + 0.1, 0.05, 0.95))

            all_rows.append(
                {
                    "match_id": match_id,
                    "home_team": home,
                    "away_team": away,
                    "team": team,
                    "opponent": opponent,
                    "player": player_row["player"],
                    "position": player_row["position"],
                    "shirt_number": player_row["shirt_number"],
                    "minute": minute,
                    "second": second,
                    "event_type": event_type,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "outcome": outcome,
                    "xg": round(xg, 3),
                }
            )

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["match_id", "minute", "second"]).reset_index(drop=True)
    df.insert(0, "event_id", range(1, len(df) + 1))
    log.info("Generated %d synthetic events across %d matches", len(df), n_matches)
    return df


def save_raw_events(df: pd.DataFrame, path=RAW_EVENTS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved raw events to %s (%d rows)", path, len(df))


def load_raw_data(path=RAW_EVENTS_FILE, generate_if_missing: bool = True) -> pd.DataFrame:
    if not path.exists():
        if not generate_if_missing:
            raise FileNotFoundError(f"No raw data found at {path}")
        log.warning("%s not found — generating synthetic dataset instead", path)
        df = generate_synthetic_events()
        save_raw_events(df, path)
        return df

    log.info("Loading raw events from %s", path)
    df = pd.read_csv(path)
    log.info("Loaded %d raw rows", len(df))
    return df


if __name__ == "__main__":
    events = generate_synthetic_events()
    save_raw_events(events)
