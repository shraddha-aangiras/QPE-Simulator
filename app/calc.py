import numpy as np
from app.style import USE_RADIANS

def qpe_p(n, x, phase):
    """Calculates ideal probability of measuring state |x> given n qubits and phase."""
    # (No changes to this function)
    if abs(phase - x/(2**n)) < 1e-9: return 1.0
    num = np.sin(np.pi * (2**n * phase - x)) ** 2
    denom = np.sin(np.pi * (phase - x/(2**n))) ** 2
    if abs(denom) < 1e-15: return 1.0
    return 1/(2**(n*2)) * num / denom

def get_circular_stats(counts, n_qubits):
    """
    Calculates both the Circular Mean (Estimate) and Circular Std Dev (Spread).
    """
    total = np.sum(counts)
    if total == 0: 
        return 0.0, 1.0

    N = 2**n_qubits

    # Map discrete states 0..N-1 to angles 0..2pi
    angles = np.linspace(0, 2*np.pi, N, endpoint=False)
    
    # Calculate Mean Resultant Vector (R)
    sin_sum = np.sum(counts * np.sin(angles))
    cos_sum = np.sum(counts * np.cos(angles))
    
    # R_len is the length of the average vector
    # 1.0 = All points are identical
    # 0.0 = Points are uniformly distributed around circle
    R_len = np.sqrt(sin_sum**2 + cos_sum**2) / total

    mean_angle = np.arctan2(sin_sum, cos_sum)
    
    if mean_angle < 0:
        mean_angle += 2 * np.pi
    mean_est = mean_angle / (2 * np.pi)
    
    # Circular Std Dev
    R_len = np.clip(R_len, 1e-9, 1.0)
    std_dev_rad = np.sqrt(-2 * np.log(R_len))
    std_dev_fraction = std_dev_rad / (2*np.pi)
    
    return mean_est, std_dev_fraction

def get_qpe_data(n_qubits, phase_val, shots, mean_photons=1, use_poisson=False):
    """
    Simulates a quantum optical experiment.
    """
    if USE_RADIANS:
        norm_phase = phase_val / (2 * np.pi)
    else:
        norm_phase = phase_val

    N = 2**n_qubits
    prob_arr = np.zeros(N)
    
    # Ideal Probabilities
    for x in range(N):
        prob_arr[x] = qpe_p(n_qubits, x, norm_phase)
    
    if np.sum(prob_arr) > 0: prob_arr /= np.sum(prob_arr)

    total_expected = int(shots * mean_photons)
    
    if use_poisson:
        counts = np.random.poisson(prob_arr * total_expected)
    else:
        counts = np.random.multinomial(total_expected, prob_arr)
    
    mean_est, std_dev = get_circular_stats(counts, n_qubits)

    if np.sum(counts) == 0:
        mean_est = 0

    total_shots = np.sum(counts)
    if total_shots > 0:
        std_error = std_dev / np.sqrt(total_shots)
    else:
        std_error = 1.0
    
    return {
        "x": np.arange(N),
        "counts": counts,
        "phase_est": mean_est, 
        "std_dev_fraction": std_dev,
        "std_error": std_error,
        "N": N
    }

def get_ideal_probs(n_qubits, phase_val):
    """Helper to pre-calculate probabilities for the animation loop."""
    if USE_RADIANS:
        norm_phase = phase_val / (2 * np.pi)
    else:
        norm_phase = phase_val

    N = 2**n_qubits
    prob_arr = np.zeros(N)
    
    for x in range(N):
        prob_arr[x] = qpe_p(n_qubits, x, norm_phase)
    
    if np.sum(prob_arr) > 0: 
        prob_arr /= np.sum(prob_arr)
        
    return prob_arr

def get_theoretical_curve(n, phase_val, shots, points=400):
    """
    Generates x and y arrays for the theoretical probability curve.
    x is scaled to [0, N], y is scaled to total counts.
    """
    N = 2**n
    x_smooth = np.linspace(0, N, points)

    if USE_RADIANS:
        norm_phase = phase_val / (2 * np.pi)
    else:
        norm_phase = phase_val

    # Avoid division by zero
    delta = norm_phase - (x_smooth / N)
    
    num = np.sin(np.pi * N * delta) ** 2
    denom = np.sin(np.pi * delta) ** 2
    
    # Handle singularities [when delta is an int ie perfect match]
    with np.errstate(divide='ignore', invalid='ignore'):
        y_probs = (1 / (N**2)) * (num / denom)
    
    # Fix NaNs (where num and denom are both 0 -> limit is 1.0)
    y_probs[np.isnan(y_probs)] = 1.0
    
    # Scale probabilities to match the histogram counts
    y_counts = y_probs * shots
    
    return x_smooth, y_counts