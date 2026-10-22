# Project Campus — Phase C: Supervised Student Pilot Plan (5–10 Participants)

**Document Version:** 1.0.0  
**Target Cohort Size:** 5 to 10 Consenting Students  
**Target Curriculum:** CBSE Class 12 (Physics, Chemistry, Mathematics)  
**Target Duration:** 7 Days (1 Initial Guided Session of 25–30 mins + 6 Days of Optional Self-Paced Practice)  
**Execution Environment:** Controlled Staging URL (`https://staging.<IP>.nip.io` or Local Supervised Lab)  
**Date:** October 2026  

---

## 1. Pilot Purpose & Problem Statement

### 1.1. Core Problem Addressed
Secondary students preparing for board exams and entrance tests frequently encounter three systemic problems:
1. **Formula & Formatting Distortion:** Mathematical and scientific derivations in digital tools often suffer from layout distortion, rendering errors, or blurry images, hindering conceptual understanding.
2. **Ambiguous or Unverified Solutions:** Standard question banks provide answer letters without rigorous, educator-verified derivations or tolerance for rounding in numerical calculations.
3. **Ineffective Revision Patterns:** Students rely on passive re-reading rather than structured retrieval practice and spaced repetition schedules.

### 1.2. Pilot Objective
The primary objective of this pilot is to evaluate whether Project Campus's verified formula typesetting (KaTeX), deliberate practice engine, automated daily study planning, and SuperMemo-2 (SM-2) flashcard revision provide a superior, friction-free learning experience for real students, while identifying any visual, conceptual, or usability bugs before investing in public domain deployment.

---

## 2. Participant Profile & Recruitment Criteria

* **Cohort Size:** 5 to 10 students (strictly capped to ensure personalized support and controlled oversight).
* **Target Grade & Stream:** Grade 12 (Science / PCM or PCMB stream).
* **Curriculum Focus:** CBSE Board syllabus.
* **Prerequisites:** Access to a modern desktop, laptop, or tablet with internet access and a supported browser (Google Chrome, Microsoft Edge, Firefox, or Safari).
* **Informed Consent & Minor Protection:**
  - Because Class 12 students are typically 16–18 years of age, transparent informed consent is mandatory.
  - For students under 18, counter-signature from a parent or legal guardian is required.
  - Participation is 100% voluntary, free of charge, and has no impact on school academic grades.
  - Students may withdraw at any time with one click using the built-in account deletion feature.

---

## 3. First-Session Test Script (Guided Walkthrough)

**Estimated Duration:** 25–30 minutes  
**Facilitation Mode:** Supervised remote session (video call with screen sharing) or self-paced with script.

### Stage 1: Registration & Academic Onboarding (5 mins)
1. Navigate to the pilot URL.
2. Click **"Create Student Account"**.
3. Register using your name/pseudonym, email, and strong password ($\ge 8$ chars).
4. In the Onboarding Wizard:
   - Select **CBSE** (marked *Active Pilot • Lessons Ready*).
   - Select **Class 12** and target exam year (e.g. 2027).
   - Select **Physics**, **Chemistry**, and **Mathematics**.
   - Set daily study goal (e.g. 60 or 90 minutes).
5. Click **"Complete Setup & Enter Dashboard"**.

### Stage 2: Lesson Study & Formula Reading (8 mins)
1. On the Student Dashboard, click **"Browse Curriculum Lessons"** or the top-bar **"Lessons"** button.
2. Select **Physics** $\to$ **Electric Charges and Fields** $\to$ **Coulomb's Law and Principle of Superposition**.
3. Open the published lesson: *"Coulomb's Law, Electrostatic Force, and the Superposition Principle"*.
4. Read through the 5 sections:
   - Review the scalar and vector formulas.
   - Inspect the worked example (Triangular Charge Configuration).
5. Mark the lesson as completed using the completion toggle.
6. Verify whether the formulas are clear, legible, and rendered without graphical glitches.

### Stage 3: Deliberate Practice Drill & Answer Feedback (7 mins)
1. Click **"Start Practice"** on the Coulomb's Law topic.
2. Solve Question 1 (Multiple Choice). Select an answer and submit.
3. Solve Question 2 (Numerical input with decimal answer: e.g., enter `0.90`). Submit.
4. Review the immediate answer verification and step-by-step educator solution.
5. In Question 3, click **"Report Errata"** to test the reporting dialog. Enter a test comment (e.g. "Testing errata submission") and submit.
6. Complete the practice session and view your score summary.

### Stage 4: Dashboard, Study Planner & Flashcard Review (7 mins)
1. Click the **"Dashboard"** button in the header.
2. Confirm that your KPI cards updated:
   - Lessons Completed ($+1$)
   - Questions Answered ($+3$)
   - Observed Accuracy (%)
3. Scroll to **Daily Study Plan**:
   - Check off a planned task to test the completion progress bar.
4. Scroll to **Spaced Repetition Review Queue**:
   - Click **"Start Flashcard Review"**.
   - Read the question prompt on the front of the card.
   - Click **"Reveal Answer"** to flip the card.
   - Select your recall quality ($0$ for Complete Blackout to $5$ for Perfect Recall).
   - Confirm card submission and interval update.

---

## 4. Student Feedback Questionnaire

At the conclusion of the first session, participants complete this 5-minute questionnaire:

### Part A: Quantitative Ratings (1 = Strongly Disagree, 5 = Strongly Agree)
1. **Mathematical Clarity:** The formulas, equations, and symbols were clear and easy to read on my screen. `[ 1 | 2 | 3 | 4 | 5 ]`
2. **Pedagogical Quality:** The lesson explanations and worked examples helped me understand the topic clearly. `[ 1 | 2 | 3 | 4 | 5 ]`
3. **Practice Evaluation:** The instant answer evaluation and step-by-step solutions were helpful and accurate. `[ 1 | 2 | 3 | 4 | 5 ]`
4. **Study Planner:** The daily study tasks and completion tracking felt intuitive and motivating. `[ 1 | 2 | 3 | 4 | 5 ]`
5. **Flashcard Review:** The flip-card active recall interface was simple and easy to use. `[ 1 | 2 | 3 | 4 | 5 ]`
6. **Overall Usability:** I was able to navigate the website without feeling lost or confused. `[ 1 | 2 | 3 | 4 | 5 ]`

### Part B: Qualitative Feedback (Open Responses)
1. What was the best or most helpful part of the platform?
2. Did you encounter any bugs, errors, slow loading, or confusing buttons? (Please describe where).
3. How does reading lessons on Project Campus compare to studying from your physical textbook or other websites?
4. What additional feature or chapter would you like to see next?

---

## 5. Usability Issue Classification & Tracking

Any issues reported by students or observers will be logged into a pilot registry using this triage schema:

| Severity | Definition | Resolution SLA | Example |
| :--- | :--- | :---: | :--- |
| **P0 — Critical Blocker** | Prevents registration, login, lesson loading, or causes data corruption/loss. | $< 4$ hours | Answer evaluation crashes on submit; blank white screen. |
| **P1 — Major Usability** | Core feature works but causes substantial confusion or has high friction. | $< 24$ hours | Task completion checkbox does not visually update without refresh. |
| **P2 — Minor / Visual** | Formatting glitch, minor typo, or styling imperfection on specific viewport. | Next Release | Margin alignment off on 375px mobile screen. |
| **P3 — Enhancement** | Feature suggestion outside current pilot scope. | Post-Pilot Backlog | Dark mode toggle; downloadable offline PDF notes. |

---

## 6. Privacy, Ethical Guardrails & Data Protection

### 6.1. Collected Data (Strictly Minimized)
* **Identity:** First name or chosen pseudonym, email address, Argon2id password hash.
* **Academic Context:** Enrolled board (CBSE), grade (Class 12), selected subjects (PCM).
* **Study Telemetry:** Lesson section completion timestamps, question attempts, selected answers, flashcard recall ratings ($0–5$), daily task completion states.

### 6.2. Prohibited Data (Zero Collection)
* **NO** physical home addresses, school roll numbers, or government IDs.
* **NO** financial or payment information (the pilot is 100% free).
* **NO** third-party ad trackers, social login tracking pixels, or cross-site fingerprinting.
* **NO** device location (GPS/geofencing) data.

### 6.3. Student Right to Erasure
In compliance with Section 12 of the Indian Digital Personal Data Protection (DPDP) Act 2023, every student has an autonomous statutory right to erasure. Clicking **"Delete Student Account"** on the dashboard immediately cascades deletion across all personal records and invalidates the session without administrative intervention.

---

## 7. Pilot Continuation, Pause & Exit Criteria

* **Success Criteria (Proceed to Extended Evaluation):**
  - $\ge 80\%$ of participants complete the full 4-stage test script without experiencing a P0 crash.
  - Overall usability satisfaction score averages $\ge 4.0 / 5.0$.
  - Zero security or cross-student data leakage incidents.
* **Pause Criteria (Immediate Investigation Required):**
  - Any P0 defect that prevents multiple students from submitting answers or logging in.
  - Any observed authorization breach (e.g. IDOR cross-student visibility).
  - Server downtime $> 10$ minutes during scheduled test windows.
* **Exit / Conclusion Criteria:**
  - Pilot concludes after 7 days of monitoring.
  - All feedback questionnaires analyzed.
  - Findings compiled into a Phase C Pilot Synthesis Report to determine whether to purchase a custom domain or proceed to a public beta.
