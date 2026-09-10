# Deep Research: AI-Driven Development Lifecycle (ADLC)

## Research Date
2026-09-10

## Research Methodology
- 3 web searches conducted on agentic AI in SDLC, SE 3.0 autonomous coding, and multi-agent orchestration frameworks
- Academic papers (arXiv), industry data (AIDev dataset), and open-source ecosystem analysis

---

## 1. Agentic AI in the Software Development Lifecycle — Academic State of the Art

### Key Source
Gao, Z., Zhang, Z., Jiang, L., et al. (2026). "Agentic AI for Software Development: Architectures, Frameworks, and Challenges." arXiv:2604.26275

### Findings
- Proposes a **six-layer reference architecture** for LLM-driven software development:
  1. **Application Layer** — use-case-specific modules (coding, testing, requirements)
  2. **Orchestration Layer** — multi-agent coordination and workflow management
  3. **Agentic Layer** — autonomous decision-making and planning capabilities
  4. **Tool Integration Layer** — APIs, IDEs, version control, CI/CD access
  5. **Knowledge Layer** — codebases, documentation, best practices, domain knowledge
  6. **Infrastructure Layer** — compute, storage, model hosting

- Performance on **SWE-bench** benchmark:
  - Best models resolve **60–70%+ of real-world GitHub issues**
  - Paradigm shift: "generation → repair → evolution" cycles replacing linear development

### Alignment with ADLC
The ADLC course directly mirrors this architecture:
- Phase 00–02 (Specification) → Application Layer
- Phase 06–08 (Orchestration) → Orchestration + Agentic Layers
- Phase 10 (Context Optimization) → Knowledge Layer
- Phase 14 (Orchestration) → Orchestration Layer full stack

The ADLC course goes further by adding **pre-development phases** (strategy, competition, pricing) that the academic architecture doesn't address — a practical advantage for real-world deployment.

---

## 2. SE 3.0 — The Autonomous Coding Agent Era

### Key Source
Peng, B., et al. (2025). "SE 3.0: The Next Era of Software Engineering in the Age of Autonomous Coding Agents." arXiv:2507.15003

### Findings
- Introduces the **AIDev dataset**: 456,862 pull requests from 82,228 repositories across 57 programming languages
- Defines **Software Engineering 3.0** as distinct from SE 1.0 (manual) and SE 2.0 (agile/DevOps)
- Key characteristics of SE 3.0:
  - Autonomous agents handle full development cycles
  - Human role shifts to **direction-setting and review**
  - Code quality increasingly validated by AI, not just CI/CD

### Alignment with ADLC
The ADLC course explicitly advocates for SE 3.0 practices:
- Phase 04 (Briefing to PDR): Human sets direction → AI executes
- Phase 11 (Testing): AI-driven test generation and validation
- Phase 13 (Review): AI quality gates with human approval
- Dobryakov's "AI is your delegate, not your replacement" manifesto aligns with SE 3.0's human-AI collaboration model

---

## 3. Multi-Agent Orchestration Frameworks

### Key Source
Ecosystem analysis: CrewAI, LangGraph, AutoGen, Microsoft Semantic Kernel

### Findings
- **CrewAI**: Role-based agent coordination, natural language task assignment, task delegation patterns
- **LangGraph**: State-machine workflow orchestration with cycle support, checkpointing, and human-in-the-loop
- **AutoGen**: Multi-agent conversation patterns, group chat orchestration
- **Common patterns**:
  - Pipeline agents (sequential)
  - Router agents (conditional)
  - Evaluator agents (quality gates)
  - Specialist agents (domain experts)

### Alignment with ADLC
ADLC Phase 14 (Orchestration) directly maps to these frameworks:
- The course's "role matrix" (PM, Architect, Tester, Reviewer) parallels CrewAI's role-based agents
- The "checkpoint" system (07, 10, 13) mirrors LangGraph's state checkpointing
- The course's dependency graph concept is identical to graph-based orchestration

**Gap identified**: The ADLC course describes orchestration conceptually but doesn't specify which framework to use. For practitioners, the choice between CrewAI (simpler) and LangGraph (more flexible) depends on workflow complexity.

---

## 4. Critical Research Findings

### What the Research Validates
1. **The ADLC's phased approach is academically sound** — aligns with published architectures
2. **Pre-development phases are unique** — academic research starts at coding; ADLC starts at strategy
3. **The "checkpoint" system mirrors production orchestration patterns**
4. **AI-generated code quality has reached production viability** (SWE-bench 60-70%+)

### What the Research Questions
1. **Scalability unproven** — no published data on ADLC applied to large enterprise projects (100K+ LOC)
2. **Framework gap** — no concrete tooling recommendations for Phase 14 orchestration
3. **Cost models missing** — academic research shows 3-10x token costs; ADLC doesn't address budget planning
4. **Skill transfer unclear** — how quickly can a junior developer become effective with ADLC?

### Open Questions for Further Research
1. How does ADLC compare to GitHub Copilot Workspace / Cursor's agent mode workflows?
2. What is the optimal team size for ADLC adoption?
3. Can ADLC be formalized into a certification program?
4. What industries have successfully adopted ADLC-like processes?

---

## 5. Comparison Matrix

| Dimension | Academic Research | ADLC Course | Gap |
|---|---|---|---|
| Pre-development | Not covered | 6 phases (00-05) | ADLC is ahead |
| Coding methodology | Generation → Repair → Evolution | Briefing → PDR → Decomposition → Generation | ADLC more structured |
| Testing | AI-generated tests | AI tests + human review | Minimal gap |
| Orchestration | Frameworks (CrewAI, LangGraph) | Conceptual roles + checkpoints | ADLC lacks tooling |
| Quality assurance | SWE-bench metrics | Checkpoint gates | Different measurement |
| Human role | Direction + Review | Direction + Review + Approval | ADLC more explicit |
| Cost modeling | Token usage analysis | Not addressed | Significant gap |
| Enterprise readiness | Emerging research | Not addressed | Significant gap |

---

## 6. Recommendations for Practitioners

1. **Start with Phase 00 (Manifesto)** — understand the philosophy before tactics
2. **Use Phase 04 (Briefing → PDR)** as the standard entry point for any project
3. **Implement checkpoints at 07, 10, 13** — non-negotiable quality gates
4. **For Phase 14 (Orchestration)**, evaluate:
   - CrewAI for simple 2-3 agent workflows
   - LangGraph for complex, stateful, multi-phase orchestration
5. **Track token costs** — budget 3-10x for iterative refinement cycles
6. **Plan for human review capacity** — AI generates, humans validate

---

## Sources
1. Gao, Z. et al. (2026). "Agentic AI for Software Development." arXiv:2604.26275
2. Peng, B. et al. (2025). "SE 3.0: The Next Era of Software Engineering." arXiv:2507.15003
3. CrewAI Documentation — https://docs.crewai.com/
4. LangGraph Documentation — https://langchain-ai.github.io/langgraph/
5. ADLC Course — https://www.dobryakov.com/courses/adlc/index.html
