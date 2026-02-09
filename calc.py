import numpy as np

def qpe_p(n, x, phase):
    """Calculates ideal probability of measuring state |x> given n qubits and phase."""
    if abs(phase - x/(2**n)) < 1e-9: return 1.0
    num = np.sin(np.pi * (2**n * phase - x)) ** 2
    denom = np.sin(np.pi * (phase - x/(2**n))) ** 2
    if abs(denom) < 1e-15: return 1.0
    return 1/(2**(n*2)) * num / denom

def get_qpe_data(n_qubits, phase_val, shots, mean_photons=1, use_poisson=False):
    """
    Simulates a quantum optical experiment.
    """
    N = 2**n_qubits
    prob_arr = np.zeros(N)
    
    # Ideal Probabilities
    for x in range(N):
        prob_arr[x] = qpe_p(n_qubits, x, phase_val)
    
    # Normalize 
    if np.sum(prob_arr) > 0: prob_arr /= np.sum(prob_arr)

    total_expected = int(shots * mean_photons)
    
    if use_poisson:
        # Counts fluctuate (Poissonian shot noise)
        counts = np.random.poisson(prob_arr * total_expected)
    else:
        # Exact sum
        counts = np.random.multinomial(total_expected, prob_arr)
    
    if np.sum(counts) > 0:
        max_idx = np.argmax(counts)
    else:
        max_idx = 0
        
    return {
        "x": np.arange(N),
        "counts": counts,
        "phase_est": max_idx / N,
        "N": N
    }