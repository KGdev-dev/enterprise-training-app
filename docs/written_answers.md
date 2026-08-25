## Deliverable 1: Design Patterns Justification

### 1. Singleton Pattern (`AppConfig`)
* **Enterprise Relevance:** In large-scale, multi-user training systems, application settings (such as connection pooling parameters, business rule thresholds, and concurrency limits) must remain unified across the runtime.
* **Benefits:** 
  - Prevents race conditions and inconsistent state across components.
  - Reduces memory overhead by avoiding redundant configuration instantiations.
  - Provides a controlled global access point to system-wide configurations.

### 2. Factory Pattern (`SupportTicketFactory`)
* **Enterprise Relevance:** Training providers process diverse inquiries ranging from billing disputes to technical LMS outages and course curriculum questions. Each ticket category has distinct routing, priority assignment, and service level agreements (SLAs).
* **Benefits:**
  - Decouples client code from concrete ticket classes.
  - Centralizes validation and instantiation logic, making it simple to add new ticket types without modifying existing business logic (adhering to the Open/Closed Principle).
  - Encapsulates ticket classification and auto-priority assignment.

### 3. Strategy Pattern (`AssessmentStrategy`)
* **Enterprise Relevance:** An enterprise training provider offers diverse academic and corporate qualifications. Short skill modules often use binary competency checks (Pass/Fail at 80%), whereas formal certification programmes require weighted letter grading.
* **Benefits:**
  - Encapsulates assessment algorithms in standalone classes, allowing runtime switching without altering the `Assessment` domain model.
  - Eliminates brittle conditional ladders (`if/elif/else`) across evaluation logic.
  - Facilitates isolated unit testing for individual scoring rules.