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
แต่ละสไลด์มีบล็อก **รูปแบบที่แนะนำ** เพื่อเลือกเลย์เอาต์ตอนลงสไลด์

### คีย์รูปแบบที่ใช้ในแพ็กนี้

| รหัส | ความหมาย | ใช้เมื่อ |
| --- | --- | --- |
| `Title` | ชื่อใหญ่กลางจอ + บรรทัดรอง | เปิด / ปิด |
| `Statement` | ประโยคหลัก 1 บรรทัด + รายการสั้น | นิยามปัญหา / decision statement |
| `Bullets` | หัวข้อ + บูลเล็ต 3–5 ข้อ | อธิบายสั้น |
| `Two-col` | สองคอลัมน์ซ้าย–ขวา | เปรียบเทียบ / objectives vs questions |
| `Table` | ตาราง | stakeholders / dataset / metrics |
| `Visual-3` | หัวข้อ + รูป/กราฟ 3 ช่อง | EDA |
| `Flow` | แผนภาพลูกศร / process | workflow / architecture |
| `Rules` | สองกล่องกฎ + แถบสรุป | decision rules |
| `Demo` | หมายเลขขั้น + จุดโชว์เดโม | POC ก่อนสลับไปแอป |
| `Close` | Benefits / Limits / Closing | ปิดท้าย |

---

## Slide 1 — Title (เฟรม)

**รูปแบบที่แนะนำ:** `Title`  
- ชื่อโปรเจกต์ใหญ่กลางจอ  
- บรรทัดวิชา + สมาชิกใต้ชื่อ  
- pitch หนึ่งบรรทัดด้านล่าง (ไม่ใส่บูลเล็ต)

**Title:** Sleep Health and Lifestyle Decision Support System  
**Subtitle:** Final Project · 1501418 Selected Topics in Data Science and AI  
**Members:** Frame · Dos · Doi · Ben · Boss  
**One-line pitch:** A two-stage screening prototype that triages sleep-disorder risk, then supports None / Insomnia / Sleep Apnea decisions with a Random Forest model.

Speaker note (ไทย): ทักทาย บอกชื่อโปรเจกต์ แนะนำสมาชิกสั้นๆ แล้วส่งไม้ต่อดอส

---

## Slide 2 — Problem background (ดอส)

**รูปแบบที่แนะนำ:** `Statement` + `Bullets`  
- บนสุด: decision statement ในกล่องเน้น  
- ด้านล่าง: บูลเล็ตปัญหา 4 ข้อ (อย่าเกิน)

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

**รูปแบบที่แนะนำ:** `Two-col`  
- ซ้าย: ทำไมสำคัญ (บูลเล็ต)  
- ขวา: หลักฐาน 1–2 แหล่ง + citation APA  
- แถบล่างเล็ก: “Course screening aid — not a medical diagnosis”

**Heading:** Why this problem matters  
**Bullets:**
- Sleep disorders raise health risk and reduce daytime function for workers and patients.
- Screening tools (for example STOP-Bang style reasoning for apnea risk) show why structured questions matter before deep assessment.
- A local decision-support demo can standardize first advice: keep routine, change habits, or seek clinical review.
- This project is a **course screening aid**, not a medical diagnosis.

**Evidence to add before submission:** 1–2 cited statistics or papers (APA 7) chosen by Dos.

---

## Slide 4 — Stakeholders and decision requirements (ดอส)

**รูปแบบที่แนะนำ:** `Table`  
- ตาราง 4 แถว stakeholder เป็นเนื้อหาหลัก  
- ใต้ตาราง: decision requirement หนึ่งประโยค

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

**รูปแบบที่แนะนำ:** `Two-col`  
- ซ้าย: Objectives 1–4 (เลขลำดับ)  
- ขวา: Project questions (บูลเล็ตสั้น)

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

**รูปแบบที่แนะนำ:** `Table`  
- ตาราง key–value เต็มสไลด์  
- แถวล่าง: class counts เป็นตัวเลขเด่น (None 219 / Insomnia 77 / Sleep Apnea 78)  
- ใส่ badge เล็ก: “Synthetic / illustrative”

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

**รูปแบบที่แนะนำ:** `Bullets` + callout  
- บูลเล็ตขั้นตอน clean 5–6 ข้อ  
- callout สีอ่อน: “265 duplicate feature rows → CV may look optimistic”

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

**รูปแบบที่แนะนำ:** `Visual-3`  
- หัวข้อสั้นด้านบน  
- กลางจอ: แคปกราฟจาก `#eda` สามช่องเท่ากัน  
- ใต้แต่ละรูป: คำอธิบาย 1 บรรทัด (ไม่ใส่บูลเล็ตยาว)

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

**รูปแบบที่แนะนำ:** `Flow`  
- แผนภาพแนวนอน: Source → Features → Target → Pre-screen layer  
- บูลเล็ตสั้นใต้แผนภาพได้ไม่เกิน 4 ข้อ  
- ดึง Mermaid จาก `docs/report-supporting-content.md` §2 มาวาดใหม่ในสไลด์

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

**รูปแบบที่แนะนำ:** `Table` + แถบเหตุผลด้านล่าง  
- ตาราง Component | Design เป็นหลัก  
- ใต้ตาราง 2 บรรทัด: Why RF + Honest limit

**Heading:** Proposed decision model (hybrid)  

| Component | Design |
| --- | --- |
| Users | Clinician / wellness staff (course demo) |
| Input | Pre-screen answers + lifestyle / heart form |
| Processing | Rules for triage + Random Forest for deep scoring + decision layer |
| Output | Class, probabilities, screen evidence, hybrid score |
| Decision | Confidence bands, conflict rules, screen boost |
| Action | Keep routine / adjust habits / seek clinician |
| Audit log | Anonymous SQLite log after assess → `#logs` / CSV; trust report on `#trust` (step 10 prototype). Outcome feedback = future work |

**Why Random Forest:** mixed feature types, nonlinear patterns, class imbalance, and built-in importance for explanation.  
**Honest limit:** the 13 pre-screen items are not RF training features; they adjust the decision layer.

---

## Slide 11 — Model workflow / architecture (บอส)

**รูปแบบที่แนะนำ:** `Flow`  
- แถวบน: 10 ขั้นเป็นลูกศรสั้น (ตัวเลข + คำเดียว)  
- แถวล่าง: architecture one-liner ในกล่องสรุป  
- เน้นขั้น 1 (triage before deep) และขั้น 10 (anonymous log + trust)

**Heading:** Ten-step workflow  
List briefly:
1. Collect → 2. Validate → 3. Clean → 4. Engineer features → 5. Train → 6. Validate → 7. Interpret → 8. Recommend → 9. Act → 10. Anonymous log / trust review

**Architecture one-liner:**  
Rule triage gates the deep form (optional continue on None); RF scores lifestyle/heart features; the decision layer merges probability bands, conflicts, and screen evidence; parallel STOP-Bang/ISI scores support trust; anonymous logs land in SQLite.

---

## Slide 12 — Evaluation and success criteria (บอส)

**รูปแบบที่แนะนำ:** `Table` + `Two-col` ล่าง  
- บน: ตารางเปรียบเทียบ 3 โมเดล (ไฮไลต์ RF)  
- ล่างซ้าย: success criteria  
- ล่างขวา: caveat แถวซ้ำ

**Heading:** Evaluation and success criteria  

| Model | Accuracy | Macro F1 |
| --- | ---: | ---: |
| Logistic Regression | 0.904 ± 0.039 | 0.884 ± 0.048 |
| Decision Tree | 0.866 ± 0.042 | 0.845 ± 0.047 |
| **Random Forest** | **0.909 ± 0.035** | **0.885 ± 0.045** |

**Success criteria**
- Technical: macro F1 ≥ 0.80 and accuracy ≥ 0.85 → **met**
- Audit: show `#logs` + `#trust` after rehearsal (anonymous log + proxy GT)
- Future work: user/clinician outcome feedback loop is not implemented yet

**Caveat:** duplicate feature rows can inflate CV scores.

---

## Slide 13 — Decision rules and actions (เฟรม)

**รูปแบบที่แนะนำ:** `Rules`  
- ซ้าย: Pre-screen gate  
- ขวา: Decision layer  
- แถบล่างเต็มความกว้าง: “Human approval required”

**Heading:** From output to action  

**Pre-screen gate**
- Insomnia: ≥2 of items 1, 6, 9
- Sleep Apnea: ≥2 items or red-flag 3 / 4 / 12
- Else None → summarize; optional deep assess
- Parallel STOP-Bang / ISI-inspired scores are supporting evidence only

**Decision layer**
- Confidence bands: &lt;0.40 / 0.40–0.69 / ≥0.70
- Conflict → forced clinical review
- Strong screen evidence can raise the pathway

**Governance:** human approval required for medical decisions.

---

## Slide 14 — Proof of concept demo (เฟรม)

**รูปแบบที่แนะนำ:** `Demo`  
- ใช้เป็นสไลด์ “bridge” ก่อนสลับไปเว็บจริง  
- แสดง 5 ขั้นเดโมเป็นหมายเลขใหญ่แนวตั้งหรือแนวนอน  
- ใส่ URL สั้นมุมล่าง: `http://127.0.0.1:8765/`  
- อย่าใส่ screenshot ทั้งจอทับสคริปต์ (เดโมสดสำคัญกว่า)

**Heading:** Proof of concept  
**Demo script (2–3 minutes):**
1. Try opening `#assess` first → show the lock.
2. Open `#screen`; show that one weak yes does not flag; use threshold or red-flag; point to parallel standard scores.
3. Continue to deep assessment; submit the form.
4. On `#result`, show pre-screen vs model, hybrid score, actions, and standards.
5. Open `#logs` / `#trust` briefly; optional `#eda` for one chart + CV metrics.

**Run command**
```powershell
cd D:\Coding\SelectedTopic
python server.py
```
Open http://127.0.0.1:8765/

---

## Slide 15 — Benefits, limitations, conclusion (ดอส)

**รูปแบบที่แนะนำ:** `Close` = `Two-col` + closing line  
- ซ้าย: Benefits  
- ขวา: Limitations / ethics  
- ล่างสุดเต็มความกว้าง: closing line 1 ประโยค + “Q&A”

**Heading:** Benefits, limits, and conclusion  

**Benefits**
- Faster triage before a long form
- Consistent risk-to-action mapping
- Transparent probabilities for discussion

**Limitations and ethics**
- Synthetic source data; small and partly duplicated sample
- Screening aid only; risk of false reassurance or alarm
- Needs human oversight; outcome feedback remains future work

**Closing line:**  
The prototype shows a complete Problem → Data → Model → Decision → Action path for course demonstration, while staying clear that a clinician makes the final medical call.

---

## Q&A cheat sheet (ทุกคนอ่าน)

- **ทำไมไม่ใส่ 13 ข้อเข้า RF?** CSV ไม่มีป้ายของคำถามพวกนั้น ถ้าฝืนใส่จะไม่มีคู่ฝึกที่สุจริต — เลยใช้กฎ + ชั้นตัดสินใจแทน  
- **ทำไมคะแนนสูง?** มีแถวซ้ำ 265 แถว และประเมินบนตารางเดียวกัน  
- **เป็นวินิจฉัยหรือยัง?** ไม่ใช่ เป็นเครื่องมือคัดกรองสำหรับงานวิชา  
- **ขั้นที่ 10 อยู่ตรงไหน?** หลังประเมิน ระบบเก็บ anonymous log ใน SQLite ดูที่ `#logs` / CSV และสรุป trust ที่ `#trust`; outcome feedback จากผู้ใช้/แพทย์ยังเป็น future work
