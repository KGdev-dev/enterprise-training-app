## Deliverable 5.2: Application Profiling Analysis

* **Profiling Technique Used:** Python's built-in `cProfile` module combined with `pstats` to analyze cumulative execution time (`cumtime`) and per-call time (`tottime`) during a 1000-request concurrent batch load.
* **Analysis of Results:** The profiling output reveals that the system spends the majority of its execution time outside of business logic. The highest overhead comes from `threading.Lock.acquire()` and context switching between thread pools in `concurrent.futures`. Dictionary lookups ($O(1)$) and set insertions for duplicate prevention registered negligible time, validating the Phase 3 optimizations.
* **Optimization Opportunities:** To further reduce lock contention on the course capacity counter, we could implement a lock-free architecture using atomic counters (e.g., via Redis) or batch-process capacity decrements asynchronously rather than acquiring a thread lock for every single registration request.

---

## Deliverable 5.3: Microservices Readiness Assessment

As the application scales, the monolithic architecture should be decomposed into bounded contexts.

### 1. Candidate Microservices & Responsibilities
1. **Identity & Learner Service:** Manages user profiles, authentication (JWT), and RBAC. Operates independently to serve login requests.
2. **Catalogue & Course Service:** Manages course metadata, schedules, and total capacity limits.
3. **Registration Engine Service:** A high-throughput, horizontally scalable service responsible strictly for seat allocation, concurrency control, and duplicate prevention.
4. **Assessment & Grading Service:** Handles the strategy-based calculation algorithms and gradebook storage.
5. **Support Ticketing Service:** Manages the factory-pattern ticket creation, routing, and agent SLAs.

### 2. Service Communication Mechanisms
* **Synchronous (REST/gRPC):** Used for front-end client queries (e.g., fetching the course catalogue or viewing grades).
* **Asynchronous (Message Broker):** RabbitMQ or Apache Kafka will handle core workflows. For example, when the Registration Engine successfully allocates a seat, it publishes an `EnrolmentConfirmed` event. The Notification Service and Assessment Service consume this event independently.

### 3. Testing, Tracing, and Monitoring
* **Tracing:** Implement OpenTelemetry to inject a `Correlation-ID` at the API Gateway. This ID will be passed through all service headers, allowing Bugzot to trace a single user request across multiple microservices.
* **Testing:** Shift from monolithic integration tests to API Contract Testing (e.g., using Pact) to ensure independent services do not break each other's expected payload schemas. 

### 4. Independently Executable Services
The **Assessment & Grading Service** and **Support Ticketing Service** can operate entirely independently. If the Registration Engine goes down under heavy peak load, learners can still view their past grades and submit support tickets because those services possess their own dedicated databases and isolated compute resources.

### 5. Architecture Diagram

```mermaid
graph TD
    Client[Web / Mobile Interface] --> APIGW[API Gateway]

    subgraph "Core Microservices"
        APIGW --> LearnerSvc[Identity & Learner Service]
        APIGW --> CourseSvc[Catalogue Service]
        APIGW --> RegSvc[Registration Engine Service]
        APIGW --> TicketSvc[Support Ticket Service]
        APIGW --> AssessSvc[Assessment Service]
    end

    subgraph "Event-Driven Backbone"
        RegSvc -->|Publish Event| Kafka[(Message Broker / Kafka)]
        Kafka -->|Consume Event| AssessSvc
        Kafka -->|Consume Event| NotificationSvc[Notification Service]
    end

    subgraph "Observability"
        RegSvc -.-> Bugzot[Bugzot Telemetry & Profiling]
        TicketSvc -.-> Bugzot
    end