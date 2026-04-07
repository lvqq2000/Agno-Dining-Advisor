import enum


class TemplateType(str, enum.Enum):
    RECOMMENDATION_WITH_CAG = "recommendation_with_cag"
    RANDOM_RECOMMENDATION = "random_recommendation"