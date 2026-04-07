import enum


class TemplateType(str, enum.Enum):
    RECOMMENDATION_WITH_CAG = "recommendation_with_cag"
    RANDOM_RECOMMENDATION = "random_recommendation"
    RECOMMENDATION_WITH_SELECTION = "recommendation_with_selection"
    RECOMMENDATION_WITH_CAG_AND_RAG = "recommendation_with_cag_and_rag"


class Cuisine(str, enum.Enum):
    ANY = "any"
    JAPANESE = "japanese"
    ITALIAN = "italian"
    FRENCH = "french"
    CHINESE = "chinese"

    @classmethod
    def values(cls):
        return [c.value for c in cls]


class DietaryRequirement(str, enum.Enum):
    NONE = "none"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten-free"

    @classmethod
    def values(cls):
        return [d.value for d in cls]