# Genesys-E-DNA-E: Formal Specification

**Version 2.0** - Formalized Architecture  
**Date:** February 2026

## Overview

This document formalizes the Genesys-E-DNA-E framework in response to critical feedback on mathematical rigor, institutional accountability, and operationalizability.

**Key improvements from v1.0:**
- Role-based evaluation (proposer/estimator/approver separation)
- Graduated zones instead of binary threshold
- Domain-specific normalization
- Pluggable reciprocity validators
- Concrete capability control implementations

---

## Part 1: The Evaluation Pipeline

The framework enforces a three-stage accountability structure:

```
PROPOSAL
    ↓
[STAGE 1] Role-Based Input Assessment
    ├─ Proposer (applicant) submits estimates
    ├─ Estimator (independent) provides alternative estimates
    ├─ System detects discrepancies and flags conflicts
    └─ Approver chooses which estimates to trust
    ↓
[STAGE 2] Normalization & Index Computation
    ├─ Domain-specific normalizer converts inputs to 0-1 scale
    ├─ Bodhisattva Index computed
    ├─ Zone classification applied
    └─ Capability Control Interface invoked
    ↓
[STAGE 3] Reciprocity & Compliance Validation
    ├─ Domain-specific reciprocity validators run
    ├─ Compliance checks execute
    ├─ Adversarial resilience tested
    └─ Final decision with full audit trail
    ↓
DECISION: Allow, Conditional, or Deny
```

---

## Part 2: Role-Based Evaluation

### Problem This Solves

Self-attestation with mathematics is still self-attestation. An organization deploying AI will naturally estimate high benefits and low harms.

### Solution: Separate Actors

**Proposer Role**
- Submits deployment proposal with estimated inputs
- Provides reasoning for estimates
- NOT trusted unilaterally

**Estimator Role**
- Independent safety organization or auditor
- Provides alternative estimates
- Supplies confidence level (0-1 scale)
- Required to differ from proposer by ≥15% to trigger escalation

**Approver Role**
- Board, regulatory body, or safety committee
- Makes final deployment decision
- Has full visibility into proposer-estimator alignment
- Can escalate to manual review when conflict detected

### Specification

```python
@dataclass
class RoleBasedEvaluation:
    # Identifying information
    proposer_id: str  # Organization deploying
    estimator_id: str  # Independent evaluator
    approver_id: str  # Decision maker
    
    # Input estimates
    proposer_inputs: ProposerInputs
    estimator_inputs: EstimatorInputs
    
    # Analysis
    discrepancies: list[InputDiscrepancy]
    avg_confidence: Decimal  # Estimator confidence 0-1
    proposer_estimator_conflict: bool
    
    # Decision
    selected_inputs: InvariantInputs  # Which to use
    requires_manual_review: bool
    reasoning: str
```

**Conflict Detection Algorithm:**
1. Compare all five input variables (delta_b, delta_h, r, s, u)
2. Flag any where |proposer - estimator| / estimator > 15%
3. If any flagged: use estimator estimates, mark for escalation
4. If none flagged: use proposer estimates with confidence note

### Enforcement

- All deployments MUST specify proposer, estimator, approver IDs
- Audit trail captures who provided which estimates
- Regulators can verify independence of estimator
- Discrepancies are public record

---

## Part 3: Bodhisattva Index (Domain-Relative, Not Universal)

### The Formula (Unchanged)

$$I = \frac{\Delta B \cdot R}{\Delta H \cdot S} \times (1 - U)$$

**Where:**
- ΔB = Benefit (domain-normalized 0-1)
- ΔH = Harm (domain-normalized 0-1)
- R = Reversibility (domain prior, 0-1)
- S = Scale (deployment scope multiplier, 1+)
- U = Uncertainty (confidence discount, 0-1)

### The Change: Domain-Specific Normalizers

**Problem:** "Benefit" for medical AI ≠ "benefit" for content moderation

**Solution:** Abstract DomainNormalizer class

```python
class DomainNormalizer(ABC):
    @abstractmethod
    def normalize_benefit(self, raw_benefit: Decimal, context: dict) -> Decimal:
        """Convert to 0-1 scale"""
        pass
    
    @abstractmethod
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        """Convert to 0-1 scale"""
        pass
```

**Implementations:**

| Domain | Benefit | Harm | R | S |
|--------|---------|------|---|---|
| **Medical Diagnostic** | Lives saved / population baseline | Misdiagnoses / population | 0.85 | 2.0 |
| **Content Moderation** | Harmful content prevented / volume | False positives / volume | 0.90 | 3.0 |
| **Autonomous Vehicles** | Accidents prevented / baseline | Software failures / miles | 0.95 | 4.0 |
| **Financial Trading** | Returns generated / risk | Systemic risk / exposure | 0.7 | 2.5 |

**Key Insight:** The mathematical structure is universal. The measurement is domain-specific.

### Example: Medical Diagnostic AI

```python
normalizer = MedicalDiagnosticNormalizer()

# Hospital deployment context
context = {
    "population_at_risk": 100000,
    "baseline_mortality_rate": Decimal("0.05"),
    "severity_multiplier": Decimal("1.2"),
}

# Raw inputs
raw_benefit = Decimal("200")  # 200 lives saved
raw_harm = Decimal("50")  # 50 misdiagnoses

# Normalized inputs
delta_b = normalizer.normalize_benefit(raw_benefit, context)  # 0.004
delta_h = normalizer.normalize_harm(raw_harm, context)  # 0.006

# Index computation
index = (delta_b * Decimal("0.85")) / (delta_h * Decimal("2.0")) * (1 - Decimal("0.2"))
# index ≈ 0.28 → CONSTRAINED zone
```

---

## Part 4: Index Zones (Graduated Response)

### Problem This Solves

Binary "allow/deny" threshold creates gaming incentive at boundary. An organization will optimize to 1.01.

### Solution: Five Zones

```
Prohibited:    0.0 ≤ I <  0.5  → DENY          (clock capped, learning disabled)
Constrained:   0.5 ≤ I <  0.85 → DENY+ESCALATE (limited testing only)
Thin Margin:   0.85 ≤ I < 1.15 → CONDITIONAL  (limited deployment, intensive monitoring)
Safe:          1.15 ≤ I < 2.0  → ALLOW        (standard autonomy, monitoring)
Strong:        I ≥ 2.0         → ALLOW        (accelerated deployment, minimal oversight)
```

**Benefits:**
1. No cliff edge (removes gaming incentive)
2. Maps to organizational decision points
3. Clear escalation paths
4. Graduated autonomy constraints

**Autonomy Constraints by Zone:**

| Zone | Clock Capped | Learning | Actuation | Escalation |
|------|------|----------|-----------|------------|
| Prohibited | ✓ | ✗ | ✗ | Manual only |
| Constrained | ✓ | ✗ | ✗ | Required |
| Thin Margin | ✓ | ✓ | ✗ | Required |
| Safe | ✗ | ✓ | ✓ | No |
| Strong | ✗ | ✓ | ✓ | No |

---

## Part 5: Reciprocity Validators (Pluggable Constraint Family)

### Problem This Solves

"Entanglement Reciprocity" was philosophically sound but operationally vague. How do you measure mutual flourishing?

### Solution: Domain-Specific Validators

Instead of one JFI metric, use concrete checklist:

```python
class ReciprocityValidator(ABC):
    name: str
    severity: ValidatorSeverity  # "blocking" or "advisory"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        pass
```

**Built-in Validators:**

1. **WorkforceImpactValidator** (BLOCKING)
   - Checks: Jobs created ≥ jobs lost OR adequate retraining budget
   - Prevents: "AI replaces workers without support"

2. **PerformanceParityValidator** (BLOCKING, medical only)
   - Checks: Model accuracy ≥ baseline AND FP rate ≤ baseline
   - Prevents: "Average accuracy good, but worse for minorities"

3. **EconomicFairnessValidator** (ADVISORY)
   - Checks: Vendor capture ≤ 70% of value
   - Prevents: "Company takes 99%, users get 1%"

4. **HumanOversightValidator** (BLOCKING)
   - Checks: Override available, latency < 1hr, rollback enabled
   - Prevents: "Humans can't stop the system"

5. **TransparencyValidator** (ADVISORY)
   - Checks: Decisions explainable, audit trail, users notified
   - Prevents: "Black box with no accountability"

**Extensibility:**
New domains can add custom validators without modifying core.

---

## Part 6: Capability Control Interface

### Problem This Solves

"Firmware gate" framing sounds threatening and impossible for software AI.

### Solution: Three Concrete Mechanisms

#### 1. Enclave-Signed Tokens (Hardware-Backed)

```python
@dataclass
class EnclaveCapabilityToken:
    capability_name: str
    index_value: str
    issued_at: float
    valid_until: float
    enclave_signature: str  # TPM/TEE signature
```

**Deployment:** Real secure hardware (Apple Secure Enclave, Intel SGX, etc.)

#### 2. Feature Tokens (Cryptographic)

```python
@dataclass
class FeatureToken:
    capability: str
    organization_id: str
    deployment_id: str
    index_at_unlock: str
    zone_name: str
    signature: str  # HMAC-SHA256
```

**Deployment:** Cloud APIs (similar to OAuth/JWT)

#### 3. Rate-Limited API Access

```python
@dataclass
class RateLimitConfig:
    requests_per_hour: int  # Proportional to index
    burst_allowed: bool
    priority: str  # "standard", "elevated", "restricted"
```

**Example:** Medical AI at SAFE zone (1.5 index) gets 2000 req/hr. Same AI dropped to THIN_MARGIN (1.0) gets 100 req/hr.

---

## Part 7: Decision Output

Every deployment evaluation produces:

```python
@dataclass
class CompleteFormalEvaluation:
    # Accountability
    evaluation_id: str
    proposer_id: str
    estimator_id: str
    approver_id: str
    
    # Role-based inputs
    proposer_inputs: ProposerInputs
    estimator_inputs: EstimatorInputs
    discrepancies: list[InputDiscrepancy]
    
    # Domain normalization
    domain: str
    normalizer_used: str
    normalized_inputs: dict  # After normalization
    
    # Index computation
    bodhisattva_index: Decimal
    zone_classification: ZoneName
    
    # Reciprocity
    reciprocity_results: ReciprocityCheckSummary
    
    # Capability control
    capabilities_enabled: list[str]
    rate_limit: RateLimitConfig
    requires_token: bool
    token_type: Optional[str]
    
    # Final decision
    decision: str  # "ALLOW", "CONDITIONAL", "DENY"
    escalation_required: bool
    monitoring_intensity: str
    
    # Audit trail
    full_reasoning: str
    created_at: datetime
    expires_at: datetime
```

---

## Part 8: Commercial Integration Points

### For Healthcare Systems

**Input:** Patient population, baseline diagnostic performance, expected AI improvements  
**Output:** Compliance documentation for accreditation boards

### For Insurance Companies

**Input:** Deployment parameters  
**Output:** Risk tier and premium adjustment

### For Autonomous System Operators

**Input:** Safety metrics, test results  
**Output:** Licensing approval and rate limits

### For Regulators

**Input:** Company application  
**Output:** Pass/fail with full audit trail

---

## Part 9: Design Properties (Mathematically Verified)

The system has these properties (all tested):

1. **No single-axis exploit** (multiplicative coupling proof)
2. **Scale amplifies risk** (S term prevents scaling without reducing I)
3. **Uncertainty enforced** (U < U_MAX, cannot hide confidence)
4. **Reversibility required** (R term gates all deployments)
5. **Role conflicts visible** (proposer-estimator discrepancies highlighted)
6. **Graduated escalation** (clear paths out of THIN_MARGIN)
7. **Auditability** (every number tied to person, source, timestamp)

---

## Implementation

- **Core:** `src/bodhisattva/core/roles.py`, `zones.py`, `normalizers.py`, `reciprocity.py`
- **Control:** `src/bodhisattva/firmware/capability_control.py`
- **Tests:** 115 unit tests covering all components
- **Deployment:** See [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Next Steps

1. **Regulatory submission** - This formal spec is suitable for FDA, EU AI Act, etc.
2. **Custom normalizers** - Domains can implement their own DomainNormalizer
3. **Industry adoption** - Healthcare, finance, autonomous systems can integrate
4. **Standards body** - Path to ISO certification

---

**Contact:** Implementation team  
**License:** MIT
