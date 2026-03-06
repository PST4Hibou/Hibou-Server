from src.acoustic_analysis.strategies.te_manu.storage import History, Options, Data
from src.logger import logger

from src.acoustic_analysis.strategies.te_manu.tdoa import to_angle

import numpy as np
import math


"""
def fuse(data: Data, history: History) -> float:
    "]""
    This function assumes that at least one prediction states the presence of a drone, and that the angles history has
    been updated with the latest data. This means that there's no duplicated TS at least.
    Args:
        data (Data): Global information about the setup.
        history (History): Updated storage of the past & current information about the drone presence and angles.

    Returns:
        float: The fused angle estimation for the current time step.

    "]""
    current_angle = float(history.angles_history[-1])

    if np.isnan(current_angle):
        logger.warning(
            f"fuse() returned NaN. angles_history: {history.angles_history[-5:]}, "
            f"confidence history: {getattr(history, 'confidence_history', 'N/A')}"
        )
        return float(history.output_history[-1] if history.output_history else math.nan)

    if len(history.output_history) == 0:
        return current_angle

    # Calculate directional confidence: weight by how well each mic is oriented toward the detected angle
    directional_confidence = 0.0
    for i in range(history.channels):
        if history.prediction_history[i][-1]:  # If this mic detected a drone
            mic_orientation = data.mic_infos[i].orientation

            # Calculate angular difference between mic orientation and detected angle
            angle_diff = abs(current_angle - mic_orientation)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            # Cardioid-like pattern: mics pointing toward the source contribute more
            # cos(0°) = 1 (perfect alignment), cos(90°) = 0, cos(180°) = -1
            # We may consider reducing the weight instead of just dumping it using a negative value.
            alignment = np.cos(np.deg2rad(angle_diff))

            # Only positive contributions (mics pointing away don't help)
            if alignment > 0:
                directional_confidence += alignment

    # We consider the number of detecting mics to further modulate the confidence factor.
    num_detecting = sum(hist[-1] for hist in history.prediction_history)
    if num_detecting > 0:
        confidence_factor = directional_confidence / num_detecting
    else:
        confidence_factor = 0.0

    previous_angle = float(history.output_history[-1])
    if np.isnan(previous_angle):
        logger.warning(
            f"fuse() previous_angle is NaN. output_history: {history.output_history}, "
            f"confidence history: {getattr(history, 'confidence_history', 'N/A')}"
        )

    angle_diff = current_angle - previous_angle
    time_diff = history.time_history[-1] - history.time_history[-2]

    # Handle angle wrapping
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    # dt cannot be zero because we only update the history when we have a new TS.
    # But just in case...
    dt = time_diff / Options.TIME_SCALE
    # Just try to avoid any numerical instability & state corruption, but this should not happen in practice.
    if dt <= 1e-6:
        return previous_angle

    if len(history.recent_speeds) >= 5:
        max_observed_speed = np.percentile(history.recent_speeds, 90)
        adaptive_speed = max(Options.MIN_ALLOWED_SPEED, max_observed_speed)
        avg_speed = np.mean(history.recent_speeds)
    else:
        adaptive_speed = Options.MAX_ANGULAR_SPEED  # fallback
        avg_speed = Options.MAX_ANGULAR_SPEED  # fallback for tau

    v_ref = 100.0  # May require changes.
    adaptive_tau = Options.TAU * (v_ref / (v_ref + avg_speed))
    adaptive_tau = np.clip(adaptive_tau, 0.05, 1.0)  # reasonable bounds

    base_alpha = 1 - np.exp(-dt / adaptive_tau)
    # May also try out with alpha = base_alpha * confidence_factor
    alpha = base_alpha * (0.5 + 0.5 * confidence_factor)

    max_allowed_change = max(Options.MIN_ALLOWED_CHANGE, adaptive_speed * dt)
    dynamic_max_change = max_allowed_change * (1.0 + (1.0 - confidence_factor))

    if abs(angle_diff) > dynamic_max_change:
        # Too bad, reject.
        return previous_angle

    history.recent_speeds.append(float(abs(angle_diff) / dt))

    smoothed_angle = previous_angle + alpha * angle_diff
    smoothed_angle = smoothed_angle % 360

    return float(smoothed_angle)
"""

"""
def fuse(data: Data, history: History) -> float:
    "@""
    Fuses angle estimation considering directional confidence from each microphone.
    "@""
    current_angle = float(history.angles_history[-1])

    if np.isnan(current_angle):
        logger.warning(
            f"fuse() current_angle is NaN. angles_history: {list(history.angles_history)[-5:]}, "
            f"confidence history: {getattr(history, 'confidence_history', 'N/A')}"
        )
        return float(history.output_history[-1] if history.output_history else math.nan)

    if len(history.output_history) == 0:
        return current_angle

    # --- Confidence factor (unchanged) ---
    directional_confidence = 0.0
    for i in range(history.channels):
        if history.prediction_history[i][-1]:
            mic_orientation = data.mic_infos[i].orientation
            angle_diff = abs(current_angle - mic_orientation)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            alignment = np.cos(np.deg2rad(angle_diff))
            if alignment > 0:
                directional_confidence += alignment

    num_detecting = sum(hist[-1] for hist in history.prediction_history)
    if num_detecting > 0:
        confidence_factor = directional_confidence / num_detecting
    else:
        confidence_factor = 0.0

    previous_angle = float(history.output_history[-1])
    # --- Handle NaN in previous estimate ---
    if np.isnan(previous_angle):
        logger.warning(
            f"fuse() previous_angle is NaN. Resetting to current_angle. "
            f"output_history: {list(history.output_history)[-5:]}, "
            f"confidence factor: {confidence_factor:.3f}"
        )
        return current_angle

    angle_diff = current_angle - previous_angle
    time_diff = history.time_history[-1] - history.time_history[-2]

    # Wrap angle difference
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    dt = time_diff / Options.TIME_SCALE
    if dt <= 1e-6:
        return previous_angle

    # --- Adaptive speed estimate ---
    if len(history.recent_speeds) >= 5:
        max_observed_speed = np.percentile(history.recent_speeds, 90)
        adaptive_speed = max(Options.MIN_ALLOWED_SPEED, max_observed_speed)
        avg_speed = np.mean(history.recent_speeds)
    else:
        adaptive_speed = Options.MAX_ANGULAR_SPEED
        avg_speed = Options.MAX_ANGULAR_SPEED

    v_ref = 100.0  # Tune as needed
    adaptive_tau = Options.TAU * (v_ref / (v_ref + avg_speed))
    adaptive_tau = np.clip(adaptive_tau, 0.05, 1.0)

    base_alpha = 1 - np.exp(-dt / adaptive_tau)
    alpha = base_alpha * (0.5 + 0.5 * confidence_factor)

    max_allowed_change = max(Options.MIN_ALLOWED_CHANGE, adaptive_speed * dt)
    dynamic_max_change = max_allowed_change * (1.0 + (1.0 - confidence_factor))

    if abs(angle_diff) > dynamic_max_change:
        # Outlier – reject
        return previous_angle

    # Accept measurement
    history.recent_speeds.append(float(abs(angle_diff) / dt))

    smoothed_angle = previous_angle + alpha * angle_diff
    smoothed_angle %= 360
    return float(smoothed_angle)
"""

"""
def fuse(data: Data, history: History) -> float:
    "@""
    Fuses angle estimation considering directional confidence from each microphone.
    "@""
    current_angle = float(history.angles_history[-1])

    if np.isnan(current_angle):
        logger.warning(
            f"fuse() current_angle is NaN. angles_history: {list(history.angles_history)[-5:]}, "
            f"confidence history: {getattr(history, 'confidence_history', 'N/A')}"
        )
        return float(history.output_history[-1] if history.output_history else math.nan)

    if len(history.output_history) == 0:
        return current_angle

    # Calculate directional confidence
    directional_confidence = 0.0
    for i in range(history.channels):
        if history.prediction_history[i][-1]:
            mic_orientation = data.mic_infos[i].orientation
            angle_diff = abs(current_angle - mic_orientation)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            alignment = np.cos(np.deg2rad(angle_diff))
            if alignment > 0:
                directional_confidence += alignment

    num_detecting = sum(hist[-1] for hist in history.prediction_history)
    if num_detecting > 0:
        confidence_factor = directional_confidence / num_detecting
    else:
        confidence_factor = 0.0

    # NEW: Reject measurements that are completely opposite to all detecting microphones
    if confidence_factor <= 0.01:  # effectively zero
        # The angle is inconsistent with all detecting microphones – likely a spurious estimate
        return history.output_history[-1] if history.output_history else current_angle

    previous_angle = float(history.output_history[-1])
    if np.isnan(previous_angle):
        logger.warning(
            f"fuse() previous_angle is NaN. Resetting to current_angle. "
            f"output_history: {list(history.output_history)[-5:]}, "
            f"confidence factor: {confidence_factor:.3f}"
        )
        return current_angle

    angle_diff = current_angle - previous_angle
    time_diff = history.time_history[-1] - history.time_history[-2]

    # Handle angle wrapping
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    dt = time_diff / Options.TIME_SCALE
    if dt <= 1e-6:
        return previous_angle

    # Adaptive speed estimate
    if len(history.recent_speeds) >= 5:
        max_observed_speed = np.percentile(history.recent_speeds, 90)
        adaptive_speed = max(Options.MIN_ALLOWED_SPEED, max_observed_speed)
        avg_speed = np.mean(history.recent_speeds)
    else:
        adaptive_speed = Options.MAX_ANGULAR_SPEED
        avg_speed = Options.MAX_ANGULAR_SPEED

    v_ref = 100.0
    adaptive_tau = Options.TAU * (v_ref / (v_ref + avg_speed))
    adaptive_tau = np.clip(adaptive_tau, 0.05, 1.0)

    base_alpha = 1 - np.exp(-dt / adaptive_tau)
    alpha = base_alpha * (0.5 + 0.5 * confidence_factor)

    max_allowed_change = max(Options.MIN_ALLOWED_CHANGE, adaptive_speed * dt)
    dynamic_max_change = max_allowed_change * (1.0 + (1.0 - confidence_factor))

    if abs(angle_diff) > dynamic_max_change:
        return previous_angle

    history.recent_speeds.append(float(abs(angle_diff) / dt))

    smoothed_angle = previous_angle + alpha * angle_diff
    smoothed_angle %= 360
    return float(smoothed_angle)
"""


def determine_groups(history: History):
    preds = [p[-1] for p in history.prediction_history]

    sets = []
    current = []

    i = 0
    while i < history.channels:
        if preds[i]:
            current.append(i)
        elif len(current) != 0:
            sets.append(current)
            current = []
        i += 1

    if preds[0] and 0 not in current and len(current) != 0:
        current.append(0)

    if len(current) != 0:
        sets.append(current)

    # Now we got to add the "edges".
    for group in sets:
        right, left = (group[-1] + 1) % history.channels, (
            group[0] - 1 + history.channels
        ) % history.channels

        if right not in group and right > group[-1]:
            group.append(right)
        if left not in group and left < group[0]:
            group.insert(0, left)

    return sets


def angle_diff(a: float, b: float):
    return np.arctan2(np.sin(a - b), np.cos(a - b))


def angle_estimator(
    tau: float, orientations: list[float], positions: list[np.ndarray]
) -> float:

    print("MIC Pos:", positions)
    print("MIC Orients:", orientations)

    baseline = positions[1] - positions[0]
    distance: float = np.linalg.norm(baseline)

    phi = np.arctan2(baseline[1], baseline[0])

    x = (Options.SPEED_OF_SOUND * tau) / distance
    x = np.clip(x, -1, 1)  # protect against numerical errors

    theta = np.arcsin(x)

    aoa1 = phi + theta
    aoa2 = phi + (np.pi - theta)

    aoa_candidates = [aoa1, aoa2]

    # convert orientations to radians
    orientations = np.radians(orientations)

    # choose angle closest to mic directions
    best = min(
        aoa_candidates,
        key=lambda a: sum(abs(angle_diff(a, o)) for o in orientations),
    )

    return np.degrees(best)


def angle_estimator(tau, orientations, positions, beam_width=30):
    """
    tau: TDOA between positions[0] and positions[1]
    positions: list of two np.array([x, y])
    orientations: list of two floats, pointing directions of the mics (degrees)
    beam_width: main lobe half-width (degrees)
    """
    p1, p2 = positions
    baseline = p2 - p1
    d = np.linalg.norm(baseline)
    phi = np.arctan2(baseline[1], baseline[0])

    x = np.clip(Options.SPEED_OF_SOUND * tau / d, -1, 1)
    theta = np.arcsin(x)

    # two candidate AoAs
    candidates = [phi + theta, phi + (np.pi - theta)]

    # convert to degrees and normalize [-180,180]
    candidates_deg = [(np.degrees(a) + 180) % 360 - 180 for a in candidates]
    print("Candidates:", candidates_deg)

    # select candidates within mic beam widths
    valid = []
    for a in candidates_deg:
        for o in orientations:
            if abs(((a - o + 180) % 360) - 180) <= beam_width:
                valid.append(a)
                break

    if not valid:
        # fallback if no candidate is inside beams
        aoa_deg = np.mean(orientations)
    else:
        # pick candidate closest to mean orientation
        aoa_deg = min(
            valid,
            key=lambda a: min(abs(((a - o + 180) % 360) - 180) for o in orientations),
        )

    return aoa_deg


def determine_angles(tdoa_matrix, groups: list[list[int]], data: Data):
    angles = []
    for group_indices in groups:
        # Get the TDOA values for this group
        if Options.OUTPUT:
            print("Group:", group_indices)

        # Because we need to elect a row of the TDOA matrix to work with. Using an element of the group is a natural
        # choice, but we can also consider other strategies (e.g., averaging the rows of the group).
        row = tdoa_matrix[group_indices[0]]
        # Gather the TDOA values corresponding to the group indices.
        possibles = np.array([row[k] for k in group_indices])
        # Elect the major as the one with the smallest absolute TDOA value, which is likely to be the most reliable.
        major_value = np.argmin(possibles)
        major = group_indices[major_value]
        gip = group_indices.index(major)

        if Options.OUTPUT:
            print("Row:", row)

        if Options.OUTPUT:
            print("Major:", major)
            print("Possibles:", possibles)

        if len(group_indices) == 1:
            if Options.OUTPUT:
                print("Path 0")

            left = right = major_value
            other = left_idx = right_idx = major
        elif len(group_indices) == 2:
            if Options.OUTPUT:
                print("Path 1")

            left, right = (
                (math.inf, group_indices[1])
                if group_indices[0] == major
                else (group_indices[0], math.inf)
            )
            other = left_idx = right_idx = (
                group_indices[1] if group_indices[0] == major else group_indices[0]
            )
        elif Options.IS_CIRCLE and len(group_indices) == len(tdoa_matrix):
            if Options.OUTPUT:
                print("Path 2")

            # When our mics are in circle, we need to perform a wrap-around to find the neighbors of the major,
            # but only if the group is the same size as the number of mics. Otherwise, we need another strategy.

            left_idx, right_idx = (major - 1 + len(tdoa_matrix)) % len(tdoa_matrix), (
                major + 1
            ) % len(tdoa_matrix)
            left, right = row[left_idx], row[right_idx]

            other = left_idx if left < right else right_idx
        else:
            if gip == 0 or gip == len(group_indices) - 1:
                # We need to check out for wrap-around in this case, but only if the group is not the entire set of
                # mics. Otherwise, we can just consider the neighbors in the group.
                if Options.IS_CIRCLE:
                    if Options.OUTPUT:
                        print("Path 3.0.0")

                    left_idx, right_idx = (major - 1 + len(tdoa_matrix)) % len(
                        tdoa_matrix
                    ), (major + 1) % len(tdoa_matrix)
                    left, right = row[left_idx], row[right_idx]

                    other = left_idx if left < right else right_idx
                else:
                    if Options.OUTPUT:
                        print("Path 3.0.1")

                    if major + 1 < len(tdoa_matrix):
                        right_idx = major + 1
                    else:
                        right_idx = gip

                    if major - 1 < 0:
                        left_idx = gip
                    else:
                        left_idx = major - 1

                    right = row[right_idx]
                    left = row[left_idx]

                    other = left_idx if left < right else right_idx

                    right = left = major_value
                    left_idx = right_idx = major
            else:
                if Options.OUTPUT:
                    print("Path 3.1")

                # We do not need to check out for wrap-around in this case, because the major is in the middle of the
                # group, so the neighbors are definitely the ones in the group.
                left_idx, right_idx = major - 1, major + 1
                left, right = row[left_idx], row[right_idx]

                other = left_idx if left < right else right_idx

        if Options.OUTPUT:
            print("Left:", left, "Right:", right)
            print("Left IDX:", left_idx, "Right IDX:", right_idx)
            print("Elected:", major, other)

        if major == other:
            angle = data.mic_infos[major].orientation
        else:
            if Options.OUTPUT:
                print("Path 4")

            # Now we can compute the angle between the major and the other, and then adjust it based on the TDOA sign.
            angle = angle_estimator(
                major_value - row[other],
                [data.mic_infos[major].orientation, data.mic_infos[other].orientation],
                [data.mic_pos[:, major], data.mic_pos[:, other]],
            )

            if Options.OUTPUT:
                print("Angle:", angle)

        angles.append(angle)

    return angles


def fuse(data: Data, history: History) -> float:
    tdoa_matrix = history.bulk_tdoa_history[-1]
    groups = determine_groups(history)

    if len(groups) == 0:
        return float(history.output_history[-1] if history.output_history else math.nan)

    if Options.OUTPUT:
        print("Groups:", groups)

    angles = determine_angles(tdoa_matrix, groups, data)
    print(angles)

    return angles[0] if len(angles) != 0 else math.nan
