# Healthcare Insurance Claims Analytics

**Project Overview:-** Real-world healthcare insurance claims analytics and MIS reporting using Python, Excel, and Power BI.
This project demonstrates end-to-end claim data processing, financial KPI analysis, and interactive dashboarding aligned with healthcare Revenue Cycle Management (RCM) workflows commonly used in KPO environments.

The primary objective is to showcase analytics methodology, reporting structure, and decision-support design, rather than actual financial outcomes.

## Data Privacy & Compliance Notice

To strictly comply with healthcare data protection standards and company confidentiality policies, this project uses anonymised, duplicated, and synthetically generated datasets that closely replicate real-world healthcare insurance claim structures.

No real patient, provider, payer, or client data is used or disclosed.
The focus is on analytics skills, workflow design, and reporting logic, not on real operational or financial figures.

## Healthcare Insurance Claims & RCM Context

**Insurance Claim:-** An insurance claim is a reimbursement request submitted by a healthcare provider to an insurance payer for services rendered to a patient.

**Revenue Cycle Management (RCM):-** Represents the financial lifecycle of a healthcare service, from patient registration to final payment or denial resolution.

Why analytics matters in RCM:

Identifies revenue leakage

Tracks payer performance

Monitors denial and pending trends

Supports operational and financial decision-making

## Revenue Cycle Management (RCM) Workflow
<img width="1080" height="1080" alt="image" src="https://github.com/user-attachments/assets/3877c340-0845-4d42-a327-14e52b65e99a" />

## Architecture Overview

1. Submitted Amount: Should not be zero / blank
 
2. Payment Reference Number: Remove blank
 
3. Paid Amount: Set blank = 0, after that Check, it should not be greater than the submitted amount. If it's greater than, do it equal to the submitted amount
 
4. Denied Amount: Should be equal to (submitted amount - Paid Amount), after that, remove zeros
 
5. Resubmitted Amount1: Remove blank and then equal the amount to the denied amount
 
6. RA Transaction ID1: Remove Blank
 
7. Resubmission Paid Amount 1: set blank = 0. After that Check, it should not exceed Resubmitted Amount1. If it is greater than, do it equal to Resubmitted Amount1
 
8. Resubmission Denied Amount RA 1: Resubmitted Amount1 - Resubmission Paid Amount
, after that filter- zeros
 
9. Resubmitted Amount2: Filter blank and then equal the amount to dthe enied amount1
 
10. RA Transaction ID2: Remove Blank
 
11. Resubmission Paid Amount2: Set Blank = 0. After the check, it should not exceed Resubmitted Amount2. If it's greater than, do it equal to Resubmitted Amount2
 
12. Resubmission Denied Amount2: Resubmitted Amount2 - Resubmission Paid Amount2


├── DATE_OF_SERVICE
├── SUBMITTED_DATE
├── RA_RECEIVE_DATE
├── SUBMITTED_AMOUNT
│   ├── [Rule 1]  blank = 0
│   ├── [Rule 2] If value = 0 or blank → Delete all columns' values for that row
│
├── PAYMENT_REFERENCE_NO
│   ├── [Rule 3] Remove blank
│   ├── [Rule 4] If value = 0 or blank → Delete all columns' values for that row
│
├── PAID_AMOUNT
│   ├── [Rule 5] If > SUBMITTED_AMOUNT → Set = SUBMITTED_AMOUNT 
│   ├── [Rule 6] If blank → Replace with 0
│
├── DENIED_AMOUNT
│   ├── [Rule 7] = SUBMITTED_AMOUNT - PAID_AMOUNT
│   └── Filter if zero
│
├── ReSubmitted_Amount_1
│   ├── [Rule 8] Remove blank → Set = DENIED_AMOUNT
│   └── RA_TRANSACTION_ID_1
│       └── [Rule 9] Remove blank
│   └── ReSubmission_Paid_Amount_1
│           └── [Rule 10] set >= ReSubmitted_Amount_1 
│   └── RESUBMISSION_DENIED_AMOUNT_RA_1
│           ├── [Rule 11] = ReSubmitted_Amount_1 - ReSubmission_Paid_Amount_1
│           └── Remove if zero
│
├── ReSubmitted_Amount2
│   ├── [Rule 12] Remove blank → Set = RESUBMISSION_DENIED_AMOUNT_RA_1
│   └── RA_TRANSACTION_ID_2
│       └── [Rule 13] Remove blank
│   └── ReSubmission_Paid_Amount2
│       ├── [Rule 14] If > ReSubmitted_Amount2 → Set = ReSubmitted_Amount2
│       └── RESUBMISSION_DENIED_AMOUNT_RA_2
│           ├── [Rule 15] = ReSubmitted_Amount2 - ReSubmission_Paid_Amount2
│           └── Remove if zero


## 🎥 Live Dashboard Demo (Ngrok)

▶️ Click to watch the full dashboard walkthrough:

[▶ Watch Dashboard Demo](https://drive.google.com/file/d/1_xr7_riQIxYIogNDLUjWVKtHkib2i62m/view?usp=drive_link))
