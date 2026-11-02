"""TypeSafe SDK quickstart against the local JevCommunity server."""
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

STATE = (
    "Our API integration started returning 500 errors on every request about "
    "20 minutes ago, and we cannot process any customer orders until this is fixed."
)

QUESTIONS = {
    "department": Choice(
        instructions="Which team should handle this",
        criteria={
            "billing": "Payment or subscription issues",
            "technical": "Bugs or integration problems",
            "sales": "Pricing or account questions",
        },
    ),
    "frustration": Score(
        instructions="How frustrated the customer appears",
        criteria=[
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language",
        ],
    ),
    "is_urgent": Noul(
        instructions="The message conveys urgency or time-sensitivity",
    ),
}


def main() -> None:
    client = TypeSafeClient(
        api_key="local",
        base_url="http://127.0.0.1:8008",
        model="jev-latest",
    )
    response = client.system_one(state=STATE, questions=QUESTIONS)
    print("department:", response.answers["department"].choice,
          "confidence:", response.answers["department"].confidence)
    print("frustration:", response.answers["frustration"].score,
          "confidence:", response.answers["frustration"].confidence)
    print("is_urgent:", response.answers["is_urgent"].noul)


if __name__ == "__main__":
    main()
