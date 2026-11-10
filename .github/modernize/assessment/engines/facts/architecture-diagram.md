# Architecture Diagram

ConsultAI is designed as a local-first, checkpointed LangGraph application with explicit privacy, evidence, and human-review boundaries. The diagrams describe the phase-1 target architecture, not implemented source components.

## Application Architecture

<!-- mermaid-checked: no \n, no em-dash/en-dash, no {} in labels, subgraphs are id["label"], arrows are -->|"label"|, all subgraphs closed by end, ids unique -->
~~~mermaid
flowchart TD
    subgraph ClientLayer["Client Layer"]
        Browser["React frontend"]
    end
    subgraph ApiLayer["API Layer"]
        Api["FastAPI streaming API"]
        Session["Session service"]
    end
    subgraph GraphLayer["Agent Graph Layer"]
        Supervisor["LangGraph supervisor"]
        Intake["Intake and redaction"]
        Workers["Typed agent nodes"]
        Review["Human review interrupt"]
        Composer["Result composer"]
    end
    subgraph DataLayer["Data Layer"]
        Postgres[("PostgreSQL and checkpoints")]
        Vector[("pgvector and BM25")]
        Reranker["Cross encoder reranker"]
    end
    subgraph ModelLayer["Model Layer"]
        Ollama["Ollama local inference"]
        LiteLLM["LiteLLM fallback policy"]
    end
    subgraph Connectors["Approved Sources"]
        Sources["User documents and connectors"]
    end

    Browser -->|"streaming session requests"| Api
    Api -->|"create and resume"| Session
    Session -->|"invoke graph"| Supervisor
    Supervisor -->|"sanitize input"| Intake
    Intake -->|"typed safe state"| Workers
    Workers -->|"retrieve evidence"| Vector
    Vector -->|"rerank candidates"| Reranker
    Workers -->|"model calls"| Ollama
    Ollama -.->|"configured fallback"| LiteLLM
    Workers -->|"checkpoint outputs"| Postgres
    Workers -->|"review request"| Review
    Review -->|"resume decision"| Supervisor
    Workers -->|"compose outputs"| Composer
    Sources -->|"ingest as untrusted data"| Intake
    Composer -->|"stream final package"| Api
~~~

### Technology Stack Summary

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Client | React | TBD in phase 2 | Streaming workflow and review UI |
| API | FastAPI | TBD in phase 2 | Session, streaming, and review endpoints |
| Orchestration | LangGraph and LangChain | TBD in phase 2 | Typed supervisor graph and model adapters |
| Contracts | Pydantic | v2 | Node and API validation |
| Database | PostgreSQL | TBD in phase 2 | Application data and graph checkpoints |
| Retrieval | pgvector and BM25 | TBD in phase 2 | Hybrid evidence retrieval |
| Reranking | Cross-encoder | TBD in phase 2 | Candidate relevance ranking |
| Privacy | Presidio | TBD in phase 2 | PII detection and redaction |
| Models | Ollama and LiteLLM | TBD in phase 2 | Local inference and controlled fallback |
| Evaluation | Ragas and evaluator model | TBD in phase 2 | Retrieval and output quality measurement |
| Observability | LangSmith or Langfuse | TBD in phase 7 | Traces, metrics, and audit support |
| Delivery | Docker and GitHub Actions | TBD in phase 2 | Local execution and CI |

### Data Storage & External Services

PostgreSQL stores session metadata, typed node outputs, review decisions, provenance, and LangGraph checkpoints. pgvector and BM25 indexes support session-scoped hybrid retrieval; the cross-encoder reranker runs before evidence enters the research context. Ollama is the default local model boundary. LiteLLM can mediate an external fallback only when explicitly configured after redaction. User documents and connectors enter through an untrusted-ingestion boundary.

### Key Architectural Decisions

- Use a modular LangGraph supervisor so critic failures can route to the responsible node and human review can resume from a checkpoint.
- Keep PII redaction, retrieval authorization, and provider policy in application boundaries rather than relying on prompts.
- Keep prompt versions outside application code so changes can trigger the evaluation suite.

## Component Relationships

<!-- mermaid-checked: no \n, no em-dash/en-dash, no {} in labels, subgraphs are id["label"], arrows are -->|"label"|, all subgraphs closed by end, ids unique -->
~~~mermaid
flowchart LR
    subgraph PresentationLayer["Presentation"]
        cReact["React client"]
        cStream["Streaming adapter"]
        cReview["Review workspace"]
    end
    subgraph BusinessLayer["Business Logic"]
        cApi["FastAPI routes"]
        cSession["Session service"]
        cGraph["LangGraph supervisor"]
        cNodes["Typed agent nodes"]
        cCritic["Critic and evaluator"]
        cCompose["Composer"]
    end
    subgraph DataAccessLayer["Data Access"]
        cRepo["Session repository"]
        cCheckpoint["Checkpoint repository"]
        cRetrieval["Hybrid retrieval service"]
        cCitation["Citation verifier"]
    end
    subgraph InfraLayer["Infrastructure"]
        cRedact["PII redaction policy"]
        cModel["Model gateway"]
        cTrace["Trace and metrics"]
        cPolicy["Input trust policy"]
    end

    cReact -->|"opens session"| cApi
    cStream -->|"renders events"| cReact
    cReview -->|"submits decision"| cApi
    cApi -->|"delegates"| cSession
    cSession -->|"starts or resumes"| cGraph
    cGraph -->|"runs"| cNodes
    cNodes -->|"checks output"| cCritic
    cCritic -->|"routes retry"| cGraph
    cCritic -->|"verified outputs"| cCompose
    cSession -->|"reads and writes"| cRepo
    cGraph -->|"persists state"| cCheckpoint
    cNodes -->|"queries evidence"| cRetrieval
    cCritic -->|"checks claims"| cCitation
    cRedact -.->|"guards intake"| cNodes
    cModel -.->|"serves model calls"| cNodes
    cTrace -.->|"observes run"| cApi
    cPolicy -.->|"classifies content"| cNodes
~~~

### Component Inventory

| Component | Layer | Type | Responsibility |
|---|---|---|---|
| React client | Presentation | UI | Collects input and displays progress and results |
| Streaming adapter | Presentation | Client service | Converts run events into UI state |
| Review workspace | Presentation | UI | Presents evidence and captures review decisions |
| FastAPI routes | Business Logic | API | Exposes session and streaming operations |
| Session service | Business Logic | Service | Creates, resumes, and authorizes session work |
| LangGraph supervisor | Business Logic | Orchestrator | Routes typed stages and retry transitions |
| Typed agent nodes | Business Logic | Agent services | Performs intake, discovery, analysis, research, and risk work |
| Critic and evaluator | Business Logic | Quality service | Scores outputs and verifies constraints |
| Composer | Business Logic | Formatter | Builds the final reviewable package |
| Session repository | Data Access | Repository | Persists session metadata and outputs |
| Checkpoint repository | Data Access | Repository | Persists graph state and resume points |
| Hybrid retrieval service | Data Access | Retrieval service | Combines vector and lexical evidence retrieval |
| Citation verifier | Data Access | Verification service | Checks claim-to-source support |
| PII redaction policy | Infrastructure | Safety service | Detects and redacts sensitive data |
| Model gateway | Infrastructure | Provider adapter | Applies local-first and fallback policy |
| Trace and metrics | Infrastructure | Observability | Records non-sensitive run telemetry |
| Input trust policy | Infrastructure | Security boundary | Prevents data from becoming instructions |
