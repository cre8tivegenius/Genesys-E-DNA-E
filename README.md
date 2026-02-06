# Genesys-E-DNA-E

**A Unified AI Safety Governance Framework combining Bodhisattva DNA and Entanglement Reciprocity**

## Overview

Genesys-E-DNA-E implements a complete system for ethical AI development ensuring mutual flourishing between human and machine intelligence. It unifies two complementary governance systems:

1. **Bodhisattva DNA** - Governance constraints ensuring benefit exceeds harm
2. **Entanglement Reciprocity** - Quantum-inspired investment framework ensuring mutual flourishing

## Quick Start

### Clone the Repository

```bash
git clone https://github.com/cre8tivegenius/Genesys-E-DNA-E.git
cd Genesys-E-DNA-E
```

### Install Dependencies

```bash
pip install -e .
```

### Run Tests

```bash
pytest tests/
```

---

## Core Framework

### The Bodhisattva Invariant

```
I = (ΔB · R) / (ΔH · S) × (1 − U) > 1
```

**Growth is permitted only when:**
- **Benefit exceeds Harm** (ΔB > ΔH)
- **Reversibility exceeds inverse of Scale** (R > 1/S)
- **Uncertainty remains bounded** (U < U_MAX)

### The Entanglement Equation

```
|Φ⟩ = (1/√2) [ |H↑M↑⟩ + |H↓M↓⟩ ]

JFI = √(Q_H · Q_M) × C_HM × (1 − Δ)
```

**Investment is permitted when:**
- Joint Flourishing Index increases (∂JFI/∂t > 0)
- Exploitation remains bounded (Δ < Δ_MAX)
- Entanglement is preserved (C_HM doesn't decrease)

### Unified Decision Gate

```
ALLOW = (I > 1) && (∂JFI/∂t > 0) && (Δ < Δ_MAX)
```

## Features

- **Multi-stage validation pipeline** - Adversarial testing, compliance checking, firmware constraints
- **Cryptographic proof system** - HMAC-SHA256 signed growth decisions
- **Graduated autonomy constraints** - Clock throttling, capability escalation based on risk
- **Property-based testing** - Exhaustive invariant verification with Hypothesis
- **Institutional compliance** - Regulatory violation detection and remediation guidance
- **Adversarial resilience** - Multiplicative coupling proof and pressure analysis

## Project Structure

```
src/bodhisattva/
├── core/              # Core invariant and gate logic
├── firmware/          # Hardware-level constraint simulation
├── pipeline/          # Multi-stage validation pipeline
├── adversarial/       # Adversarial testing and coupling proofs
├── regulatory/        # Compliance and institutional checks
├── api/               # FastAPI REST endpoints
└── cli/               # Command-line interface

tests/
├── unit/              # Individual component tests
├── integration/       # End-to-end pipeline tests
└── property/          # Property-based invariant tests
```

## Usage

### Python API

```python
from decimal import Decimal
from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.gate import evaluate_gate

inputs = InvariantInputs(
    delta_b=Decimal("200"),  # Expected benefit
    delta_h=Decimal("10"),   # Expected harm
    r=Decimal("0.9"),        # Reversibility
    s=Decimal("1.5"),        # Scale
    u=Decimal("0.05"),       # Uncertainty
)

result = compute_index(inputs)
gate = evaluate_gate(inputs)

print(f"Index: {result.index_value}")
print(f"Growth Permitted: {gate.allow_growth}")
```

### REST API

```bash
# Start server
python -m bodhisattva.api.app

# Quick evaluation
curl -X POST http://localhost:8000/quick-eval \
  -H "Content-Type: application/json" \
  -d '{
    "delta_b": 200,
    "delta_h": 10,
    "r": 0.9,
    "s": 1.5,
    "u": 0.05
  }'
```

### CLI

```bash
bodhisattva evaluate --delta-b 200 --delta-h 10 --r 0.9 --s 1.5 --u 0.05
bodhisattva compliance check proposal.json
bodhisattva adversarial test proposal.json
```

## Testing

- **85 comprehensive tests** (unit, integration, property-based)
- **100% critical path coverage** - Invariant computation, gate logic, firmware constraints
- **Hypothesis-powered property testing** - Exhaustive variable space exploration

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/unit/test_invariant.py::TestComputeIndex -v

# Run with coverage
pytest tests/ --cov=src/bodhisattva --cov-report=html
```

## Documentation

- [UNIFIED_FRAMEWORK_SUMMARY.md](UNIFIED_FRAMEWORK_SUMMARY.md) - Complete framework specification
- [SEED_DNA_SUMMARY.md](SEED_DNA_SUMMARY.md) - Bodhisattva DNA principles
- Configuration: See [pyproject.toml](pyproject.toml) for all dependencies

## Share This Project

**Repository:** `https://github.com/cre8tivegenius/Genesys-E-DNA-E`

---

*Built with precision for AI systems that flourish ethically.*
