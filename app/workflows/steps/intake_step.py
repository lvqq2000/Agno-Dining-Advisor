from pydantic import BaseModel, ValidationError
from typing import Optional
from app.models.enums import Cuisine, DietaryRequirement


class IntakeModel(BaseModel):
    # Single free-text input from the frontend named 'feeling'
    feeling: str
    cuisine: Optional[str]
    dietary_requirement: Optional[str]


def intake_step(state):
    """Validate and normalise incoming form data.

    Expects state to contain a single free-text key 'feeling', along with
    optional cuisine and dietary_requirement. Normalises and sets fields on
    state and returns it.
    """
    # Only accept 'feeling' from the frontend
    feeling = state.get("feeling")
    cuisine = state.get("cuisine")
    dietary = state.get("dietary_requirement")

    try:
        model = IntakeModel(
            feeling=feeling,
            cuisine=cuisine,
            dietary_requirement=dietary,
        )
    except ValidationError as e:
        # attach error to state and return
        state["intake_error"] = e.json()
        return state

    # normalise enum-like fields using shared enums
    cuisine_val = (model.cuisine or Cuisine.ANY.value).lower()
    if cuisine_val not in Cuisine.values():
        cuisine_val = Cuisine.ANY.value

    dietary_val = (model.dietary_requirement or DietaryRequirement.NONE.value).lower()
    if dietary_val not in DietaryRequirement.values():
        dietary_val = DietaryRequirement.NONE.value

    # Normalise to store the canonical 'feeling' key in state
    state["feeling"] = model.feeling
    # Keep preferences key for compatibility but set to None
    state["preferences"] = None
    state["cuisine"] = cuisine_val
    state["dietary_requirement"] = dietary_val

    return state
