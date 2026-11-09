
from analytics.financial_assistant import ask_financial_assistant


questions = [
    "Which supplier has the highest unpaid exposure?",
    "Why should Berlin Components GmbH receive attention?",
    "What is the total overdue supplier amount?",
    "How much money is unpaid but not overdue?",
    "What is the total supplier invoice value?"
]

for question in questions:
    print("\n" + "=" * 60)
    print("QUESTION:", question)
    print("=" * 60)

    answer = ask_financial_assistant(question)

    print("\nMITTELSTAND AI:")
    print(answer)
