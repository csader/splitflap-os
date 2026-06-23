"""Pure helpers for fine-tuning hardware commands."""


def build_tuning_adjust_commands(
    module_id,
    char_index,
    step_position,
    calibration_steps,
):
    """Return commands that save and immediately preview a tuned position.

    The preview command intentionally uses firmware ``g`` ("goto absolute
    motor step position"), not character-index navigation. Fine-tuning changes
    the physical step for the currently displayed character; asking firmware to
    go to the same character index again may be ignored because the logical flap
    index has not changed.
    """

    module_id = int(module_id)
    char_index = int(char_index)
    step_position = int(step_position)
    calibration_steps = int(calibration_steps)

    if module_id < 0 or module_id > 254:
        raise ValueError("Module ID must be between 0 and 254.")
    if char_index < 0 or char_index > 63:
        raise ValueError("Character index must be between 0 and 63.")
    if calibration_steps <= 0:
        raise ValueError("Calibration steps must be positive.")
    if step_position < 0:
        raise ValueError("Step position cannot be negative.")
    if step_position >= calibration_steps:
        raise ValueError(
            f"Step position must be less than calibration steps ({calibration_steps})."
        )

    return (
        f"m{module_id:02d}w{char_index}:{step_position}",
        f"m{module_id:02d}g{step_position}",
    )
