from nexusmind.brain.brain import Brain


def create_and_get_brain_id():
    """
    Creates a new Brain instance with default test values, saves it,
    and returns its brain_id.
    """
    # These are placeholder values for testing purposes.
    # You might need to adjust them based on your application's needs.
    test_brain = Brain(
        name="My Test Brain",
        llm_model_name="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=256,
    )
    test_brain.save()
    print(f"Brain created and saved. ID: {test_brain.brain_id}")
    return test_brain.brain_id


if __name__ == "__main__":
    create_and_get_brain_id()
