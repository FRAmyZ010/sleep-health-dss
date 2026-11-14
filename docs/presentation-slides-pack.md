# Presentation Slides Pack (15 slides)

- Slide body language: **English** (matches Project Guidance tone)
- Work assignment notes: **Thai**
- Timing target: ~15 minutes + 5 minutes Q&A
- Group: เฟรม, ดอส, ด๋อย, เบน, บอส

---

## การแจกจ่ายงาน (ภาษาไทย)

| คน | สไลด์ | หน้าที่หลักตอนพรีเซนต์ | สิ่งที่ต้องเตรียมเพิ่ม |
| --- | ---: | --- | --- |
| **เฟรม** | 1, 13, 14 | เปิดงาน, กฎตัดสินใจ, เดโมสด | เปิด `python server.py` ให้พร้อมก่อนพรีเซนต์ |
| **ดอส** | 2, 3, 4, 15 | ปัญหา ความสำคัญ ผู้มีส่วนได้ส่วนเสีย ปิดท้าย | หาสถิติ/งานวิจัยประกอบ 1–2 แหล่ง ใส่ APA |
| **ด๋อย** | 5, 6, 7 | วัตถุประสงค์ ชุดข้อมูล คุณภาพข้อมูล | ยืนยันวันที่ดาวน์โหลด + ข้อความ license บน Kaggle |
| **เบน** | 8, 9 | EDA + data model | แคป 3 กราฟจากหน้า Explore |
| **บอส** | 10, 11, 12 | โมเดล workflow ประเมินผล | ตาราง baseline + เกณฑ์สำเร็จ |

ลำดับพูดแนะนำ: เฟรม → ดอส → ด๋อย → เบน → บอส → เฟรม (เดโม) → ดอส (ปิด)

รายละเอียดเนื้อหาอังกฤษของแต่ละสไลด์อยู่ด้านล่าง นำไปวางใน PowerPoint / Google Slides ได้เลย

---

## Slide 1 — Title (เฟรม)

**Title:** Sleep Health and Lifestyle Decision Support System  
**Subtitle:** Final Project · 1501418 Selected Topics in Data Science and AI  
**Members:** Frame · Dos · Doi · Ben · Boss  
**One-line pitch:** A two-stage screening prototype that triages sleep-disorder risk, then supports None / Insomnia / Sleep Apnea decisions with a Random Forest model.

Speaker note (ไทย): ทักทาย บอกชื่อโปรเจกต์ แนะนำสมาชิกสั้นๆ แล้วส่งไม้ต่อดอส

---

## Slide 2 — Problem background (ดอส)

**Heading:** Problem background  
**Bullets:**
- Poor sleep is common among working-age adults and linked to health and daytime performance problems.
- Two frequent disorder patterns in this project scope are **Insomnia** and **Sleep Apnea**.
- Current intake is often long forms or late clinical referral, with little structured first-pass triage.
- Opportunity: use available lifestyle and cardiovascular data to support earlier screening decisions.

**Decision statement (fill-in form from Guidance):**  
The proposed model will help **clinicians and wellness staff** to **classify sleep-disorder risk and recommend the next action** by using **demographic, lifestyle, cardiovascular, and short symptom-screen data**.

---

## Slide 3 — Justification and evidence (ดอส)

**Heading:** Why this problem matters  
**Bullets:**
- Sleep disorders raise health risk and reduce daytime function for workers and patients.
- Screening tools (for example STOP-Bang style reasoning for apnea risk) show why structured questions matter before deep assessment.
- A local decision-support demo can standardize first advice: keep routine, change habits, or seek clinical review.
- This project is a **course screening aid**, not a medical diagnosis.

**Evidence to add before submission:** 1–2 cited statistics or papers (APA 7) chosen by Dos.

---

## Slide 4 — Stakeholders and decision requirements (ดอส)

**Heading:** Stakeholders  

| Stakeholder | Role | Decision / information needed |
| --- | --- | --- |
| Clinician / sleep specialist | Decision maker | Whether deeper assessment or referral is warranted |
| Wellness staff / nurse | System user | What action to recommend after screening |
| Working-age adult / patient | Affected person | Clear next step without overclaiming diagnosis |
| Data / ML student team | Knowledge provider | Transparent features, metrics, and limits |

**Decision requirement:** output must map to an action the user can take immediately, with human oversight.

---

## Slide 5 — Objectives and project questions (ด๋อย)

**Heading:** Objectives and questions  

**Objectives**
1. Examine relationships among lifestyle, cardiovascular markers, and sleep-disorder labels.
2. Build a hybrid decision path: rule-based pre-screen, then Random Forest deep assessment.
3. Translate model outputs into Low / Medium / High actions.
4. Evaluate the classifier with stratified cross-validation and explicit success criteria.

**Project questions**
- Which inputs matter most for prediction?
- Can these features classify None / Insomnia / Sleep Apnea usefully?
- How should outputs become practical actions?
- How good is the model against simple baselines?

---

## Slide 6 — Dataset overview (ด๋อย)

**Heading:** Dataset overview  

| Item | Value |
| --- | --- |
| Name | Sleep Health and Lifestyle Dataset |
| Owner | Laksika Tharmalingam |
| Source | Kaggle (`uom190346a/sleep-health-and-lifestyle-dataset`) |
| Records / attributes | 374 rows · 13 columns |
| Target | `Sleep Disorder` |
| Class counts | None 219 · Sleep Apnea 78 · Insomnia 77 |
| Note | Publisher describes the data as **synthetic / illustrative** |

**URL:** https://www.kaggle.com/datasets/uom190346a/sleep-health-and-lifestyle-dataset  
**Date accessed:** *[fill exact date]*

---

## Slide 7 — Data quality and preprocessing (ด๋อย)

**Heading:** Data quality and preprocessing  
**Bullets:**
- Preserve literal `None` labels during CSV import.
- Relabel `Normal Weight` → `Normal` (21 rows).
- Split blood-pressure text into `Systolic_BP` and `Diastolic_BP`.
- 265 duplicate feature rows → CV scores may look optimistic.
- Imbalance handled with `class_weight="balanced"`.
- Demo form computes WHO BMI category from weight and height.

---

## Slide 8 — Exploratory data analysis (เบน)

**Heading:** Exploratory data analysis  
**Show 3 visuals from the app (`#eda`):**
1. Correlation heatmap — stress, sleep duration, blood pressure, disorder risk
2. Sleep duration vs stress scatter — colored by disorder label
3. Sleep-disorder prevalence by occupation

**Interpretation prompts**
- Which pairs move together?
- Where do Insomnia / Sleep Apnea clusters appear?
- Which occupations look extreme because of small counts?

Speaker note (ไทย): แคปจากหน้า Explore จริง อย่าใช้กราฟปลอม

---

## Slide 9 — Data model (เบน)

**Heading:** Data model  
**Bullets:**
- Source entity: person-level sleep and lifestyle record
- Engineered fields: systolic / diastolic blood pressure
- ML inputs: demographics + lifestyle + cardiovascular features
- Target: sleep-disorder class
- Extra layer: 13-item pre-screen rules aligned to the same three classes

**Diagram cue:** use the Mermaid flow from `docs/report-supporting-content.md` §2.

---

## Slide 10 — Proposed decision model (บอส)

**Heading:** Proposed decision model (hybrid)  

| Component | Design |
| --- | --- |
| Users | Clinician / wellness staff (course demo) |
| Input | Pre-screen answers + lifestyle / heart form |
| Processing | Rules for triage + Random Forest for deep scoring + decision layer |
| Output | Class, probabilities, screen evidence, hybrid score |
| Decision | Confidence bands, conflict rules, screen boost |
| Action | Keep routine / adjust habits / seek clinician |
| Feedback | Usefulness log on `#result` → localStorage + `data/feedback.jsonl` (step 10 prototype) |

**Why Random Forest:** mixed feature types, nonlinear patterns, class imbalance, and built-in importance for explanation.  
**Honest limit:** the 13 pre-screen items are not RF training features; they adjust the decision layer.

---

## Slide 11 — Model workflow / architecture (บอส)

**Heading:** Ten-step workflow  
List briefly:
1. Collect → 2. Validate → 3. Clean → 4. Engineer features → 5. Train → 6. Validate → 7. Interpret → 8. Recommend → 9. Act → 10. Feedback / improve

**Architecture one-liner:**  
Rule triage gates the deep form; RF scores lifestyle/heart features; the decision layer merges probability bands, conflicts, and screen evidence; feedback is logged locally.

---

## Slide 12 — Evaluation and success criteria (บอส)

**Heading:** Evaluation and success criteria  

| Model | Accuracy | Macro F1 |
| --- | ---: | ---: |
| Logistic Regression | 0.904 ± 0.039 | 0.884 ± 0.048 |
| Decision Tree | 0.866 ± 0.042 | 0.845 ± 0.047 |
| **Random Forest** | **0.909 ± 0.035** | **0.885 ± 0.045** |

**Success criteria**
- Technical: macro F1 ≥ 0.80 and accuracy ≥ 0.85 → **met**
- Usefulness: ≥ 80% of local feedback entries marked useful → **measure on `#result` during rehearsal**

**Caveat:** duplicate feature rows can inflate CV scores.

---

## Slide 13 — Decision rules and actions (เฟรม)

**Heading:** From output to action  

**Pre-screen gate**
- Insomnia: ≥2 of items 1, 6, 9
- Sleep Apnea: ≥2 items or red-flag 3 / 4 / 12
- Else None → deep assess locked

**Decision layer**
- Confidence bands: &lt;0.40 / 0.40–0.69 / ≥0.70
- Conflict → forced clinical review
- Strong screen evidence can raise the pathway

**Governance:** human approval required for medical decisions.

---

## Slide 14 — Proof of concept demo (เฟรม)

**Heading:** Proof of concept  
**Demo script (2–3 minutes):**
1. Try opening `#assess` first → show the lock.
2. Open `#screen`; show that one weak yes does not flag; use threshold or red-flag.
3. Continue to deep assessment; submit the form.
4. On `#result`, show pre-screen vs model, hybrid score, actions, and submit feedback.
5. Optional: `#eda` for one chart + CV metrics.

**Run command**
```powershell
cd D:\Coding\SelectedTopic
python server.py
```
Open http://127.0.0.1:8765/

---

## Slide 15 — Benefits, limitations, conclusion (ดอส)

**Heading:** Benefits, limits, and conclusion  

**Benefits**
- Faster triage before a long form
- Consistent risk-to-action mapping
- Transparent probabilities for discussion

**Limitations and ethics**
- Synthetic source data; small and partly duplicated sample
- Screening aid only; risk of false reassurance or alarm
- Needs human oversight and future feedback data

**Closing line:**  
The prototype shows a complete Problem → Data → Model → Decision → Action path for course demonstration, while staying clear that a clinician makes the final medical call.

---

## Q&A cheat sheet (ทุกคนอ่าน)

- **ทำไมไม่ใส่ 13 ข้อเข้า RF?** CSV ไม่มีป้ายของคำถามพวกนั้น ถ้าฝืนใส่จะไม่มีคู่ฝึกที่สุจริต — เลยใช้กฎ + ชั้นตัดสินใจแทน  
- **ทำไมคะแนนสูง?** มีแถวซ้ำ 265 แถว และประเมินบนตารางเดียวกัน  
- **เป็นวินิจฉัยหรือยัง?** ไม่ใช่ เป็นเครื่องมือคัดกรองสำหรับงานวิชา  
- **Feedback อยู่ตรงไหน?** หน้า `#result` เก็บ useful/not useful ใน localStorage เป็น prototype ของขั้นที่ 10
