# Schema Validation Layer

Validates incoming JSON payloads against defined contracts.

**Responsibility:** Ensure all input data conforms to the expected structure, types, and constraints before it reaches the service layer.

**Key principle:** Schemas define the contract boundary of the system. Any data that fails validation is rejected before any business logic runs.

**Contents:**
- Pydantic v2 request/response models
- Prediction, result, evaluation, and leaderboard schemas
