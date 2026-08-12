# Feature Documentation: AI Model Execution System

## Project

GOALGORITHM — FIFA AI Prediction Scoring Platform


---

# Overview

The AI Model Execution System introduces an additional prediction workflow for GOALGORITHM.

Currently, teams can manually upload prediction JSON files. Those JSON predictions are validated, stored in the predictions table, compared against actual match results, and processed by the existing scoring engine.

This existing workflow is fully functional and MUST NOT be modified.

The new AI Model Execution System adds a separate workflow where teams can upload trained machine learning models (`.pkl` files). The platform executes these uploaded models, captures the generated prediction output, converts it into the same prediction JSON format already used by the platform, and stores the generated prediction.

The scoring engine continues working exactly as before.

From the scoring engine's perspective, there is no difference between:

- manually uploaded JSON predictions
- AI model generated predictions


---

# Critical Implementation Rule

## Existing Manual Prediction Flow Must Remain Untouched


DO NOT modify:

- existing prediction upload pages
- existing prediction APIs
- prediction validation logic
- scoring engine
- leaderboard calculations
- match result logic
- existing database columns unless absolutely required


The Model Execution System must be implemented as an independent module.

It should connect to existing functionality only at the final prediction creation step.


Architecture:


Existing Flow:


Team

 ↓

Upload prediction.json

 ↓

Existing Prediction APIs

 ↓

Predictions Table

 ↓

Scoring Engine



New Flow:


Team

 ↓

Upload model.pkl

 ↓

Model Execution Module

 ↓

Execute AI Model

 ↓

Generate Prediction JSON

 ↓

Existing Prediction Creation Logic

 ↓

Predictions Table

 ↓

Scoring Engine


Both flows must continue to work independently.


---

# Goals


## Primary Goals


The system should:

- Allow teams to upload trained AI models
- Store uploaded model files safely
- Track model upload history
- Allow multiple uploads per team/match
- Execute uploaded models
- Display execution progress
- Capture successful prediction outputs
- Convert model output into platform prediction JSON
- Save generated predictions
- Display model execution failures clearly
- Allow debugging without affecting other features


---

# Non Goals


This system will NOT:

- Replace manual prediction uploads
- Remove JSON upload functionality
- Change scoring formulas
- Modify leaderboard calculation
- Change actual result management
- Automatically run models without user action


---

# User Role


## Team Leader


Team Leader can:

- Open Model Execution page
- Select match
- Upload `.pkl` model
- View uploaded models
- Run model execution
- Monitor execution status
- View success/failure result


---

# Dashboard Changes


Add new dashboard option:


Model Execution


This should be a separate page.


Existing pages remain unchanged:

- Dashboard
- Matches
- Predictions
- Leaderboard
- Actual Results


---

# Model Upload System


## Upload Behaviour


User selects:

- Match
- Model file


The logged-in team information is taken automatically.


Example file:


team_model.pkl


---

# Upload Storage


For every upload store:


- team_id
- match_id
- original filename
- stored file path
- upload timestamp
- current status


A team can upload multiple models for the same match.


Example:


Team A uploads:


model_v1.pkl

model_v2.pkl

model_final.pkl


All records are stored.


Latest upload is considered active.


---

# Model States


A model execution follows:


IDLE

 ↓

RUNNING

 ↓

---------------

|             |

SUCCESS     FAILED



---


# State Details


## IDLE


Meaning:


Model uploaded.

Execution not started.


Example:


{
    "status": "IDLE"
}


---


# RUNNING


Meaning:


Model is currently being executed.


Frontend should show:


"Model running..."


Example:


{
    "status":"RUNNING"
}


---


# SUCCESS


Meaning:


Model executed successfully.

Prediction was generated.

Prediction saved.


Example:


{
    "status":"SUCCESS",
    "prediction_id":"uuid"
}


---


# FAILED


Meaning:


Execution crashed or output was invalid.


Possible reasons:


- corrupted pickle file
- unsupported dependency
- runtime error
- prediction format error
- timeout


Example:


{
    "status":"FAILED",
    "error_message":
    "Missing sklearn dependency"
}


---

# Model Execution Process


Internal workflow:


Receive execution request

        |

Create execution record

        |

Set status RUNNING

        |

Load .pkl model

        |

Deserialize model

        |

Prepare match input

        |

Run model prediction

        |

Capture model output

        |

Validate output format

        |

Convert into prediction JSON

        |

Save using prediction service

        |

Store prediction_id

        |

Set status SUCCESS



If any step fails:


Catch exception

        |

Save error message

        |

Set status FAILED

        |

Do NOT create prediction



---

# Expected Model Output


Models must return:


```json
{
    "predicted_winner": "Belgium",

    "score": {
        "Belgium": 2,
        "Iran": 1
    },

    "confidence": 78
}
```

---

# Output Validation Rules


Required fields:


- predicted_winner
- score
- confidence


Invalid output should fail execution.


Example:


Missing confidence:


FAILED


Wrong score format:


FAILED


---

# Prediction JSON Conversion


Model output is converted internally into the existing prediction schema.


Example:


Model output

 ↓

Serializer

 ↓

Existing prediction format

 ↓

Prediction table


Do not duplicate scoring logic here.


---

# Database Design


## New Table: model_uploads


Purpose:

Stores uploaded AI models.


Fields:


id UUID PK

team_id FK

match_id FK

original_filename

stored_file_path

status

created_at



Example:


{
"id":"uuid",
"team":"Team A",
"match":"Belgium vs Iran",
"status":"IDLE"
}


---


# New Table: model_executions


Purpose:

Tracks every execution attempt.


Fields:


id UUID PK

model_upload_id FK

status

started_at

completed_at

error_message

prediction_id FK nullable



Example success:


{
"status":"SUCCESS",
"prediction_id":"123"
}


Example failure:


{
"status":"FAILED",
"error":"Model crashed"
}


---

# Backend Structure


Create a separate module:


backend/

 app/

  model_execution/

        router.py

        service.py

        executor.py

        serializer.py

        schemas.py

        models.py



Responsibilities:


router.py

- API endpoints only


service.py

- business logic


executor.py

- model loading/running


serializer.py

- converts model output


models.py

- database models


schemas.py

- request/response schemas



---

# API Design


## Upload Model


POST


/api/v1/model-execution/upload


Input:


multipart/form-data


Fields:


match_id

file


Response:


```json
{
"model_id":"uuid",
"status":"IDLE"
}
```


---

# Execute Model


POST


/api/v1/model-execution/{model_id}/execute



Behaviour:


Starts execution.

Returns immediately.



Response:


```json
{
"execution_id":"uuid",
"status":"RUNNING"
}
```


---

# Execution Status API


GET


/api/v1/model-execution/{execution_id}/status



Used for frontend polling.


Example running:


```json
{
"status":"RUNNING"
}
```


Success:


```json
{
"status":"SUCCESS",
"prediction_created":true
}
```


Failed:


```json
{
"status":"FAILED",
"error":"Invalid model output"
}
```


---

# Frontend Requirements


Create new page:


ModelExecutionPage


Features:


## Upload Section


Contains:


- Match dropdown
- File upload
- Submit button


---


# Execution Section


Shows:


Team

Match

Status

Error Message

Generated Prediction



Example UI:


Team A

RUNNING


Team B

SUCCESS

Prediction saved


Team C

FAILED

Missing dependency



---

# Status Updates


Frontend should poll:


GET execution status


Interval:


2 seconds


Stop polling when:


SUCCESS

or

FAILED



---

# Error Handling Rules


Important:


A failed model must NEVER:

- crash backend
- create partial predictions
- affect scoring


Errors should:

- be stored
- be visible on frontend
- allow retry


---

# Security


Pickle files are unsafe.


Future production execution must happen inside:


- separate Docker container
- restricted permissions
- limited CPU/memory
- timeout protection


Main backend should never crash because of model failure.


---

# Implementation Phases


## Phase 1 — Backend Foundation


Implement:

- database models
- migrations
- upload storage
- upload API
- execution records
- status API


No pickle execution yet.


Use dummy statuses.


---

# Phase 2 — Model Runner


Implement:

- pickle deserialization
- executor service
- model.predict()
- capture output
- exception handling


---

# Phase 3 — Prediction Integration


Implement:


- output validation
- serializer
- convert result
- save generated prediction


Use existing prediction service.

Do not duplicate logic.


---

# Phase 4 — Frontend Integration


Implement:


- dashboard menu item
- model upload page
- execution trigger
- status polling
- success/error UI


---

# Phase 5 — Sandbox Execution


Implement:


- isolated runner container
- resource limits
- execution timeout
- safer pickle handling


---

# Final Rule


Build this feature independently.

Existing GOALGORITHM functionality must continue working exactly as before.