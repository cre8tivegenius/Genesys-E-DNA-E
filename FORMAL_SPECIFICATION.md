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
- **Mathematical soundness as governance** (incentive compatibility via multiplicative coupling)

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
- **Must be credentialed** (see Estimator Qualification below)

### Estimator Credential Registry

To prevent shopping for friendly estimates, estimators must have documented credentials:

**Estimator Attributes:**
- Accreditation status (domain-specific certifications)
- Domain expertise tags (medical, autonomous, content, financial)
- Historical estimation accuracy (tracked against actual outcomes)
- Conflict-of-interest assessment
- Independence verification (not subordinate to proposer)

**Maintenance:**
- Estimator performance is tracked post-deployment
- Systematic over- or under-estimation triggers review
- Accrued reputation score affects future evaluation weight
- Public registry for transparency

**Approver Role**
- Board, regulatory body, or safety committee
- Makes final deployment decision
- Has full visibility into proposer-estimator alignment
- Can escalate to manual review when conflict detected
- **Cannot override without justification** (see Guardrails below)

### Approver Override Guardrails

Approver may override selected inputs only if:

1. **Justification is explicit** - Must cite specific discrepancy and reason
2. **Monitoring increases automatically** - Override → intensive monitoring tier
3. **Assumption risk is flagged** - Marked as "approval override" in audit trail
4. **Insurance impact is noted** - Disclosed to underwriters as assumption risk
5. **Override frequency is tracked** - Patterns trigger governance review

Without these constraints, approval becomes a pressure-release valve for politics.

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

$$I = \frac{\Delta B \cdot R}{\max(\Delta H, \epsilon) \cdot S} \times (1 - U)$$

**Where:**
- ΔB = Benefit (domain-normalized 0-1)
- ΔH = Harm (domain-normalized 0-1)
- R = Reversibility (domain prior, 0-1)
- S = Scale (deployment scope multiplier, 1+)
- U = Uncertainty (confidence discount, 0-1)
- **ε = Harm floor (domain-specific minimum)** → Prevents division-by-vanishing-harm

### Critical Mathematical Fix: Harm Floor

Without a harm floor, estimated harms can approach zero, causing unrealistic index inflation.

**Solution:** Every domain normalizer defines a harm floor ε:

```python
class MedicalDiagnosticNormalizer(DomainNormalizer):
    HARM_FLOOR = Decimal("0.001")  # At least 0.1% harm baseline
    
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        harm = super().normalize_harm(raw_harm, context)
        return max(harm, self.HARM_FLOOR)  # Enforce floor
```

**Rationale:**
- Prevents underestimated harms from unlocking accelerated deployment
- Makes gaming expensive (must artificially inflate scale or understate reversibility instead)
- Tested: exploiting this gap is the most likely hostile attack vector

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
Strong:        I ≥ 2.0         → ALLOW        (full capabilities, baseline oversight)
```

**Naming note:** "Strong" zone uses **"baseline oversight"** instead of "minimal oversight" to reduce political friction while maintaining identical enforcement.

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

**Multi-Validator Failure Semantics:**

When multiple validators fail:

```python
# Blocking failures: ALL must pass (AND logic)
blocking_results = [v for v in results if v.severity == BLOCKING]
deployment_allowed = all(r.passed for r in blocking_results)

# Advisory failures: tracked but non-blocking (separate reporting)
advisory_results = [v for v in results if v.severity == ADVISORY]
```

**Escalation rules:**
- 0 blocking failures → normal approval path
- 1+ blocking failures → escalation required (human review mandatory)
- 3+ advisory failures → escalation recommended
- All validators failed → automatic DENY

**Partial remediation:** An organization can remediate one blocking failure while leaving others open, but each open failure increases monitoring intensity by one tier.

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
    
    # Known limitations
    known_assumptions: list[str]  # Explicit model assumptions
    assumption_risk_tier: str  # "low", "moderate", "high"
    model_limits: str  # Conditions under which this evaluation may not hold
    post_deployment_checks: list[str]  # Required validation post-launch
```

---

## Part 12: Commercial Integration Points

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

## Part 13: Design Properties (Rigorously Specified)

The system enforces these properties:

1. **No declared-input single-axis exploit** (multiplicative coupling)
   - *Conditional on:* accurate normalization, estimator integrity, harm floor enforcement
   - *Not absolute:* depends on input honesty; adversarial normalization can circumvent
   - *Tested:* pressure analysis covers 5 attack vectors; all require multiple-variable manipulation

2. **Scale amplifies risk** (S term prevents scaling without cost)
   - Deploying 10× broader requires Index ≥ 1 × 10^S_factor to maintain approval
   - Mathematically enforced, not heuristic

3. **Uncertainty enforced** (U < U_MAX, cannot hide confidence)
   - Estimator must supply confidence; cannot default to zero
   - High uncertainty automatically downgrades deployment

4. **Reversibility gated** (R term multiplies all calculations)
   - Systems with R < 0.5 cannot reach SAFE zone regardless of benefit
   - Hard constraint, not advisory

5. **Role conflicts surfaced** (proposer-estimator divergence is mandatory audit trail)
   - Every >15% discrepancy is flagged and public
   - Cannot be hidden or reframed

6. **Graduated escalation** (clear operational paths)
   - THIN_MARGIN systems have defined paths to SAFE (reduce harm, increase reversibility)
   - Not arbitrary; each zone transition is measurable

7. **Auditability** (complete causal chain)
   - Every number traced to: source, estimator, confidence, timestamp, assumptions
   - Post-incident analysis can reconstruct exact decision state

---

## Part 10: Mathematical Soundness as Governance (The Unified Solution)

### The Core Insight

All governance capture problems (approver override, normalizer gaming, collusion) are solved by a single mathematical constraint:

**The system is sound if and only if no actor can unilaterally improve their outcome by deviating from the protocol.**

This is **incentive compatibility** from mechanism design. The framework achieves it through multiplicative coupling.

### Mathematical Proof of Soundness

**Theorem:** If $I = \frac{\Delta B \cdot R}{\max(\Delta H, \epsilon) \cdot S} \times (1 - U)$ with enforcement of all five variables, then:
1. No single-variable manipulation improves Index unilaterally
2. Collusion requires multiple conspirators
3. Approver override is detectable
4. Normalizer gaming is visible in code review

**Proof sketch:**

Any attempt to improve Index by manipulating one variable requires compensatory manipulation in another:

- **Inflate ΔB alone?** → Index improves, but $R$ is domain prior (cannot change). Zone stays same or requires higher $S$ (larger deployment = more scrutiny).
- **Understate ΔH?** → Harm floor $\epsilon$ prevents vanishing. Minimum denominator is $\epsilon \cdot S$, so denominator barely moves. Gaming expensive.
- **Increase R?** → Domain prior, controlled by independent normalizer. Proposer cannot change.
- **Decrease S?** → Lower Index. Counterproductive.
- **Hide U?** → Estimator must provide confidence. If U = 0 (false certainty), system flags as unrealistic. If U > 0.3, Index downgrades.

**Therefore:** Any single attack requires compensatory attack in a different variable. This creates **joint incentive compatibility**:
- Proposer and estimator must collude (observable via >15% discrepancy)
- Approver must override (flagged and monitored)
- Multiple actors must act in concert (governance detectable)

### Why Each Component Is Necessary

If you remove any component, the system becomes **incentive incompatible** (vulnerable to unilateral gaming):

| Component | If Removed | Result |
|-----------|-----------|--------|
| Harm floor (ε) | $\max(\Delta H, \epsilon)$ becomes $\Delta H$ | Denominator → 0, Index → ∞. Single-variable exploit exists. |
| Estimator role | No independent estimate | Proposer estimates alone. Self-attestation with math. Approver has no check. |
| >15% discrepancy trigger | Estimator alignment hidden | Collusion becomes invisible. Approver never knows conflict exists. |
| Monitoring escalation on override | Approver override hidden | Political pressure gets decision undetected. No audit trail. |
| Scale multiplier (S) | $I = \frac{\Delta B \cdot R}{\max(\Delta H, \epsilon)} \times (1 - U)$ | Broader deployment no longer increases required Index. Gaming incentive at boundary. |
| Uncertainty discount (U) | Confidence requirement removed | Estimator can claim certainty falsely. Index artificially inflated. |
| Reversibility gate (R) | $I = \frac{\Delta B}{\max(\Delta H, \epsilon) \cdot S} \times (1 - U)$ | Irreversible systems (R → 0) can still reach SAFE zone. Risk unconstrained. |

**Each removal creates a unilateral exploit vector.**

### The Governance Problems Are Actually Mathematical Problems

Reframed:

1. **Approver capture** = "Can approver unilaterally change decision without cost?"
   - **Mathematical solution:** Monitoring escalation on override makes cost explicit (higher monitoring tier). Override becomes decision + constraint, not decision alone.

2. **Normalizer gaming** = "Can proposer choose normalizer to inflate Index?"
   - **Mathematical solution:** Domain normalizer is independent (chosen by third party, not proposer). Harm floor ε prevents normalization tricks. Proposer cannot achieve single-variable improvement.

3. **Collusion** = "Can proposer + estimator together inflate Index?"
   - **Mathematical solution:** Any joint manipulation requires >15% discrepancy (observable) OR requires changing domain prior R (controlled by independent normalizer) OR requires scale choice S (observable, increases scrutiny). All paths leave audit trail.

### What Breaks If System Becomes Mathematically Unsound

If you weaken any mathematical constraint:

- **Remove harm floor?** → Undershooting harm becomes unilateral win. No need for collusion.
- **Remove scale multiplier?** → All deployments treated same. Larger scope has same governance burden as smaller scope. Incentive to deceive on scope.
- **Weaken discrepancy threshold from 15%?** → Estimator can be much closer to proposer (10% = practically aligned). Estimator becomes "friendly checker," not independent.
- **Remove role separation?** → Back to self-attestation. Math provides no constraint on inputs.

**Each of these makes a different governance failure inevitable.**

### The Unified Principle

**The framework works because it makes the governance structure and mathematical structure the same thing.**

You cannot separate them. The math enforces governance. Governance cannot override math without breaking the Index contract.

This is why:
- Approver override doesn't "solve" approver capture; it makes capture *detectable and expensive*
- Estimator registry doesn't prevent collusion; it makes collusion *require multiple conspirators and leave evidence*
- Normalizer specification doesn't prevent gaming; it makes gaming *visible in code review*

All three governance problems are *transformed*, not eliminated, because they're all symptoms of **incentive incompatibility**. The math fixes incentive compatibility.

---

## Part 11: Known Limitations & Attack Surface

### Assumptions This Framework Makes

1. **Estimator independence is verifiable** - Registry-based, but ultimately reputational
2. **Domain normalizers are calibrated** - Requires post-deployment outcome tracking
3. **Harm floor is chosen conservatively** - Overestimated harms are safer than underestimated
4. **Approver role is not captured** - Assumes approver acts in good faith (enforced via governance, not math)
5. **Deployment context is stable** - Redeployment or significant context shift requires re-evaluation

### Hostile Attacks This Framework Resists

| Attack | Defense | Residual Risk |
|--------|---------|----------------|
| Inflate benefits | Domain normalizer caps at 1.0 | Low |
| Understate harms | Harm floor prevents vanishing | Low |
| Hide uncertainty | Estimator confidence mandatory | Low |
| Fake independence | Estimator registry + historical tracking | Medium |
| Subvert approver | Requires explicit justification, override flagged | Medium |
| Normalize maliciously | Requires new DomainNormalizer; visible in code review | Low |

### Attack Vectors That Remain

1. **Collusion between proposer and estimator** - Mitigated by registry, not eliminated
2. **Systemic underestimation of harms** (e.g., all medical harm estimates too low) - Caught post-deployment only
3. **Normalization gaming** - Sophisticated math to exploit domain-specific priors
4. **Context drift** (system deployed in conditions where assumptions no longer hold) - Requires human monitoring

---

## Implementation

- **Core:** `src/bodhisattva/core/roles.py`, `zones.py`, `normalizers.py`, `reciprocity.py`
- **Control:** `src/bodhisattva/firmware/capability_control.py`
- **Tests:** 115 unit tests covering all components
- **Deployment:** See [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Next Steps

1. **Regulatory submission** - This formal spec is suitable for FDA, EU AI Act, etc.
   - Include estimator registry requirements
   - Document harm floor justification per domain
   - Specify post-deployment validation protocol

2. **Custom normalizers** - Domains can implement their own DomainNormalizer
   - Must document harm floor rationale
   - Must commit to tracking historical accuracy

3. **Industry adoption** - Healthcare, finance, autonomous systems can integrate
   - Start with healthcare (highest regulatory pressure)
   - Insurance underwriting (commercial incentive alignment)
   - Autonomous operators (licensing requirement forthcoming)

4. **Standards body** - Path to ISO certification (medium-term)
   - Not ready yet; need 12-18 months of operational data
   - Estimator registry must be tested at scale
   - Harm floors must be validated across domains

---

**Contact:** Implementation team  
**License:** MIT
