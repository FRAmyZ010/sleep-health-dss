# Handoff สำหรับ Gemini — รายงานฉบับเต็ม (จัดตามตัวอย่าง MFU)

**ตัวอย่างฟอร์แมต (ศึกษาแล้ว ให้เลียนแบบโครงสร้าง/น้ำเสียง/ความซื่อสัตย์ของหลักฐาน):**  
https://docs.google.com/document/d/1G4kJYuZ1Z-Eks_ZaK8y9DQBlDWBAbeSnu66zIM6TRKA/edit?usp=sharing  
ชื่อตัวอย่าง: *Expressway Accident Classification Using Machine Learning* (วิชา 1501418)

**วิธีใช้:** คัดลอกไฟล์นี้ทั้งก้อน + แนบ `README.md`, `docs/report-supporting-content.md`, `docs/data-dictionary.md` ไปให้ Gemini  
แล้วสั่งให้เขียนรายงานตามโครงข้อ 3 ด้านล่าง

---

## 0) Title ที่ใช้ทั้งเล่ม

### แนะนำหลัก
**SLEEPBEFORERISK: A TWO-STAGE WATCH-AWARE DECISION SUPPORT SYSTEM FOR SLEEP DISORDER SCREENING**

ชื่อสั้นในเนื้อหา: **SleepBeforeRisk**

### สำรอง
1. NightTriage DSS: Hybrid Rule and Random Forest Screening for Insomnia and Sleep Apnea  
2. WatchSleep Assist: From Symptom Triage to Lifestyle-Based Sleep Risk Decisions  

---

## 1) สิ่งที่ต้องเลียนแบบจากตัวอย่าง (สำคัญมาก)

### ปก (หน้าแรก)
- โลโก้/หัว MFU style ถ้ามี (`mfu_02` ในตัวอย่าง)
- **TITLE ตัวพิมพ์ใหญ่ กึ่งกลาง**
- รายชื่อสมาชิก (ตัวพิมพ์ใหญ่)
- `PROJECT REPORT FOR COURSE 1501418`
- `SELECTED TOPICS IN DATA SCIENCE AND AI`
- `BACHELOR OF ENGINEERING IN COMPUTER ENGINEERING`
- `MAE FAH LUANG UNIVERSITY`
- ปี `2026`
- `© COPYRIGHT BY MAE FAH LUANG UNIVERSITY`

### น้ำเสียงและกฎการเขียน (เหมือนตัวอย่าง)
- เขียน **ภาษาอังกฤษ** เป็นหลัก (ตัวอย่างเป็นอังกฤษทั้งเล่ม)
- ประโยคสั้น ชัด ตรวจสอบได้
- **อย่า overclaim**: ย้ำว่าเป็น prototype / screening aid / ไม่ใช่การวินิจฉัย / ไม่ลดความเสียหายในโลกจริงโดยอัตโนมัติ
- ทุกครั้งที่มีตัวเลข ต้องบอกว่ามาจากไฟล์/การรันใด
- แยก **ผลที่มีอยู่ตอนนี้** กับ **แผนการประเมินรอบถัดไป**
- ใต้ทุก Figure ต้องมี:  
  `Figure N. …`  
  `Source: …`
- ตารางใช้หัวคอลัมน์สั้น แล้วอธิบายใต้ตาราง
- มีส่วน **Limitations Ethics and Risks** ที่ตรงไปตรงมา
- มี **Academic honesty / Use of AI Tools** (ระบุว่า Gemini ช่วยจัดรูปและร่างรายงาน แต่ผู้เขียนตรวจเอง)
- References แบบ **APA 7th**
- Appendices A–E ละเอียด (dictionary, files, how to reproduce, contribution)

### สิ่งที่ตัวอย่างทำดี — ให้ทำแบบเดียวกันกับโปรเจกต์นอน
- Executive Summary มีตารางสรุปผลตรวจแล้ว
- Decision statement ชัด
- Stakeholders เป็นตาราง
- Dataset details เป็นตาราง Item / Data used
- Data quality เป็น Finding / Action
- Evaluation criteria มี “proposed next evaluation” ที่ยังไม่ผ่านบางข้อก็ยอมรับตรงๆ
- Prototype section มีเคส TP/FP/TN/FN หรือ conflict ตัวอย่าง
- Conclusion ปิดด้วย local use, scale-up, better data collection

---

## 2) ข้อมูลจริงของโปรเจกต์เรา (ห้าม invent)

| Item | Value |
| --- | --- |
| Course | 1501418 Selected Topics in Data Science and AI |
| Working title in code | Sleep Health and Lifestyle Decision Support System |
| Brand title for report | SleepBeforeRisk |
| Team nicknames | Frame (เฟรม), Dos (ดอส), Doi (ด๋อย), Ben (เบน), Boss (บอส) — **ใส่ชื่อจริง+รหัสนักศึกษาถ้าผู้ใช้ให้** |
| Demo | `python server.py` → http://127.0.0.1:8765/ |
| Dataset | Sleep Health and Lifestyle Dataset (Kaggle; Laksika Tharmalingam / `uom190346a`) |
| Rows | 374 |
| Classes | None 219, Sleep Apnea 78, Insomnia 77 |
| Model | RandomForestClassifier (`n_estimators=300`, `min_samples_leaf=2`, `class_weight=balanced`, `random_state=42`) |
| Validation | Stratified 5-fold CV on all 374 rows |
| Current CV (after removing BP) | accuracy **0.904 ± 0.037**, macro F1 **0.881 ± 0.044** |
| Duplicate feature rows | 265 (CV may look optimistic) |
| Deep inputs (watch-aligned) | Sleep Duration, Quality of Sleep, Physical Activity, Stress (HRV-mapped 1–10), Daily Steps, Heart Rate + Gender/Age/Occupation/BMI |
| Excluded from model | Blood Pressure (not a general smart-watch metric) |
| Pre-screen | 13 symptom items; items **2–5** allow Unknown/live-alone (does **not** count as a hit) |
| Hybrid flow | Rule triage → deep form (after triage; optional on None) → RF → decision layer (confidence bands, conflict, screen evidence) + parallel STOP-Bang/ISI scores |
| UX rule | Color/wording follow **model class**; “next step / action” is separate (avoid saying High risk on None) |
| Audit / step 10 | Anonymous SQLite log → `#logs` / CSV; proxy GT + reference profiles on `#trust`. Outcome feedback = future work |
| Repo | https://github.com/FRAmyZ010/sleep-health-dss |
| Branch | `feat/assess-guide` |

### Decision statement (ใส่ Section 4)
The proposed system would help clinicians or wellness staff decide the next action for sleep-risk screening. It would use a short symptom pre-screen and lifestyle or heart metrics that general smart watches commonly report. It is a course prototype and is not a medical diagnosis.

---

## 3) โครงรายงานที่ต้องตามตัวอย่าง (เลขหัวข้อแบบนี้)

เขียนเป็นรายงานต่อเนื่องแบบตัวอย่าง ไม่ใช่โครง “บทที่ 1/2” แบบตำราไทย

**Cover page**

1. **Executive Summary** (+ summary table + keywords + project evidence line)  
2. **Background and Problem**  
3. **Reasons and Supporting Evidence** (อ้าง WHO/sleep research ได้ แต่ต้องบอกขอบเขต)  
4. **Stakeholders and Decision Needs** (+ Decision statement)  
5. **Project Objectives and Questions**  
6. **Dataset Details** (ตาราง Item / Data used)  
7. **Data Dictionary and Target Definition**  
8. **Data Quality and Preparation** (Finding / Action)  
9. **Exploratory Data Analysis** (อย่างน้อย 3–4 รูป + Source)  
10. **Data Model** (diagram + component table)  
11. **Proposed Decision Support Model**  
    - 11.1 Technical Design  
12. **System Design and Workflow**  
    - 12.1 Current Training and Evaluation  
    - 12.2 Plan for the Next Evaluation  
13. **Evaluation and Success Criteria**  
    - 13.1 Results on the Existing Evaluation  
    - 13.2 Proposed Criteria for the Next Evaluation  
    - 13.3 Errors / Conflict Cases / Workload-style discussion  
14. **Decision Rules and Suggested Actions**  
15. **Prototype and Demonstration** (เคสจริงจากเดโม)  
16. **Expected Benefits**  
17. **Limitations Ethics and Risks** (รวม Academic honesty / AI use)  
18. **Conclusion** (local use, future scale-up, better data collection)  
19. **References** (APA 7)  
20. **Appendices**  
    - Appendix A Data Sources and Supporting Files  
    - Appendix B Full Data Dictionary  
    - Appendix C Code Models and Repeating the Results  
    - Appendix D More Evaluation Results and Figures  
    - Appendix E Individual Work and Final Review (+ AI tools + optional cost note)

เป้าหมายความยาวใกล้ตัวอย่าง: **หนาและมีหลักฐาน** (ประมาณ 15–25 หน้าเมื่อรวมรูป/ภาคผนวกได้)

---

## 4) แผนรูปประกอบแบบใหม่ — **ไม่พึ่ง Gemini สร้างรูป**

Gemini ถึงลิมิตสร้างรูปแล้ว ให้ทำแบบนี้แทน:
1. Gemini เขียนรายงาน + **ใส่เฉพาะ caption / Source / ช่องว่างรูป** ตามตารางด้านล่าง  
2. ทีมใส่รูปจริงเองจาก (ก) screenshot เดโม (ข) chart จาก Excel/Google Sheets/Python (ค) ภาพสาธารณะ Unsplash/Wikimedia (ง) assets ในโปรเจกต์

### ตาราง Caption + ประเภทภาพที่แนะนำ

| Figure | Caption ที่ใช้ในรายงาน (อังกฤษ แบบตัวอย่าง) | ควรเอารูปแบบไหนมาใส่ | วิธีหาง่ายๆ | Source บรรทัดแนะนำ |
| --- | --- | --- | --- | --- |
| **Cover / optional hero** | — (ไม่มีเลข Figure ก็ได้) | ห้องคลินิกสว่าง / บรรยากาศการนอนที่สงบ ไม่โชว์หน้าคนชัด | ใช้ `assets/clinic-background.jpg` ในโปรเจกต์ | Project asset: `assets/clinic-background.jpg` |
| **Figure 1** | Figure 1. Sleep-disorder class counts in the training table. None contains 219 records (58.6%), Insomnia 77 (20.6%), and Sleep Apnea 78 (20.9%). The unequal class sizes show why macro F1 should be reported with accuracy. | **Bar chart หรือ pie chart** 3 คลาส สีเขียว/ส้ม/แดงตาม UI | Excel/Sheets จากตัวเลข 219/77/78 หรือ screenshot จากหน้า Explore ถ้ามี | Calculated from `Sleep_health_and_lifestyle_dataset.csv`. |
| **Figure 2** | Figure 2. Sleep duration versus stress level in the training table, colored by sleep-disorder class. The chart describes association in the sample. It does not prove that stress causes insomnia. | **Scatter plot** แกน X=Sleep Duration, Y=Stress, สีตามคลาส | หน้า `#eda` ในเดโม → screenshot หรือ export จาก pandas | Project Explore page / calculated from the training CSV. |
| **Figure 3** | Figure 3. Share of sleep-disorder labels by BMI category (or occupation). Counts describe the available sample. They do not estimate population prevalence. | **Grouped bar** BMI×disorder หรือ occupation prevalence | หน้า Explore prevalence / heatmap screenshot | Project Explore page; see Appendix B for field definitions. |
| **Figure 4** | Figure 4. Two input paths used in the prototype: partner-dependent symptom answers (with an Unknown option) and lifestyle metrics aligned with general smart-watch readings. | **ภาพเปรียบเทียบ 2 ฝั่ง**: ซ้ายแบบสอบถามอาการ / ขวา smartwatch + ไอคอนนอน ชีพจร ก้าว stress | Unsplash: “smartwatch sleep”, “clipboard checklist”; หรือ collage ง่ายใน PowerPoint | Photo: Unsplash (credit photographer). Icons: project UI / CC0. |
| **Figure 5** | Figure 5. Data model and file flow used in the project. It shows the Kaggle CSV, preparation without blood-pressure features, the Random Forest pipeline, the local web demo, and the anonymous SQLite assessment log. | **Flow diagram** กล่องลูกศรแนวนอน ไม่ต้องสวยแบบ AI | วาดใน PowerPoint / draw.io / Mermaid แล้ว screenshot | Based on `model.py`, `server.py`, and `db.py`. See Appendix A. |
| **Figure 6** | Figure 6. Two-stage screening workflow. Solid lines show the current local demo. Dashed lines show a proposed future path with clinician review and outcome feedback before any clinical deployment. | **Flowchart 2 ขั้น**: pre-screen → deep assess → decision; เส้นประ = future | PowerPoint / draw.io | Project design in `README.md` and Section 12. |
| **Figure 7** | Figure 7. Result screen concept after the UX fix. The card color follows the model class, while the next-step line states the recommended action separately. Class probabilities are shown as a spider chart, and feature importance is limited to the top factors. | **Screenshot จริงจากเดโม** หน้า `#result` หลังประเมินเคสหนึ่ง | รัน `python server.py` → hard refresh → ถ่าย screenshot | Screenshot from the local demo at http://127.0.0.1:8765/ (`#result`). |
| **Figure 8** | Figure 8. Partner-observed symptoms remain difficult for people who sleep alone. The prototype therefore allows Unknown answers for selected items and does not count Unknown as a positive hit. | **ภาพคนนอนคนเดียวตอนกลางคืน** หรือ screenshot ข้อ 2–5 ที่มีปุ่ม Unknown | Unsplash “person sleeping alone” **หรือ** screenshot หน้า `#screen` | Screenshot from `#screen`, or Unsplash photo (credit photographer). |
| **Figure D1** | Figure D1. Top contributing features in the fitted Random Forest after blood pressure was removed. Rank order may change if the model is retrained. | **Horizontal bar / ranked list** Top 5 (+ Other) | Screenshot ความสำคัญของปัจจัยบน `#result` หรือตารางจาก `importances` | Model importances from the local demo / `artifacts` after `python model.py`. |

### กฎใส่รูปในเล่ม (บอก Gemini)
- **อย่าเรียกสร้างรูป** — ใส่เป็น `[Insert Figure N here]` + caption + Source ตามตาราง  
- ทีมจะวางไฟล์รูปเองทีหลัง  
- ห้ามใช้ภาพที่ดูเหมือนวินิจฉัยโรค / กราฟปลอมที่ตัวเลขไม่ตรง CSV  

### ภาพในโปรเจกต์ที่ใช้ได้ทันที
- `assets/clinic-background.jpg` — ปกหรือ Section 15 prototype context  
- `assets/body-measurements.jpg` — ประกอบคำอธิบาย BMI / body step ใน deep assess

---

## 5) เนื้อหาเฉพาะที่ต้องเขียนให้เหมือนน้ำเสียงตัวอย่าง

### Pre-screen rules
- Insomnia: ≥2 yes among items 1, 6, 9  
- Sleep Apnea: ≥2 in apnea set **or** red-flag yes on 3, 4, or 12  
- Unknown on items 2–5 does **not** count as a hit  

### Decision / action rules (Section 14)
| Condition | Suggested message and action |
| --- | --- |
| Pre-screen = None | Summarize screening; optional deep assess; keep routine unless symptoms worsen |
| Model class = None, no conflict | Show model class in calm/green tone; next step = keep routine |
| Model class = Insomnia | Suggest behavior/lifestyle actions; clinician if persistent |
| Model class = Sleep Apnea | Recommend clinical review / sleep study discussion |
| Pre-screen disorder + model None (conflict) | Forced clinical review; do **not** label the person as “high disease risk” only because action urgency is high |
| Pre-screen top group ≠ model class | Forced clinical review |
| Confidence &lt; 0.40 | Uncertain pathway; cautious next step |
| Missing / out-of-range inputs | Show note; still score if allowed, with warning |

### Success criteria (Section 13.2 style)
| Proposed criterion | Current status |
| --- | --- |
| Stratified 5-fold macro F1 ≥ 0.80 and accuracy ≥ 0.85 | Met (0.881 / 0.904) after BP removal |
| Anonymous log + trust page available after rehearsal | Met when `#logs` has rows and `#trust` loads (`scripts/check_ground_truth.py`) |
| User/clinician outcome feedback loop | Future work — not in current demo |
| Partner-dependent items support Unknown | Implemented for items 2–5 |
| No BP dependency for deep assess | Implemented |
| Independent clinical validation | Not done — course prototype only |

### Prototype cases (Section 15)
Include at least:
1. Weak snore-only → None with optional deep path  
2. Alone + proxy symptoms → Sleep Apnea unlock  
3. Profile A (Male 55 Nurse, BMI obese, watch-style vitals) → Sleep Apnea-ish  
4. Conflict case (apnea screen + low-risk deep profile) → clinical review action  

---

## 6) References ตั้งต้น (ขยายเป็น APA ให้ครบ)

- Chung, F., Abdullah, H. R., & Liao, P. (2016). STOP-Bang questionnaire… *Chest*.  
- Drake, C. L., Pillai, V., & Roth, T. (2014). Stress and sleep reactivity… *Sleep*.  
- Watson, N. F., et al. (2015). Recommended amount of sleep… *Sleep*.  
- World Health Organization. BMI / healthy lifestyle pages as used.  
- Tharmalingam, L. (n.d.). Sleep Health and Lifestyle Dataset [Data set]. Kaggle. https://www.kaggle.com/datasets/uom190346a/sleep-health-and-lifestyle-dataset  
- scikit-learn developers documentation pages  
- Project guidance 1501418 handout  
- Google / OpenAI (or Gemini) as AI writing aid — same honesty style as the sample’s ChatGPT note  

---

## 7) Appendix mapping สำหรับโปรเจกต์เรา

### Appendix A — files
`Sleep_health_and_lifestyle_dataset.csv`, `model.py`, `server.py`, `web/*`, `scripts/check_triage.py`, `artifacts/*`, `docs/*`, GitHub repo URL

### Appendix B — dictionary
ใช้/ขยายจาก `docs/data-dictionary.md`  
ระบุชัดว่า Blood Pressure อยู่ใน CSV แต่ **excluded from model**

### Appendix C — reproduce
```powershell
cd D:\Coding\SelectedTopic
python -m pip install -r requirements.txt
python scripts\check_triage.py
python model.py
python server.py
```
Open http://127.0.0.1:8765/

### Appendix E — contributions
ตารางสมาชิก (ชื่อจริงรอผู้ใช้ใส่) + ส่วน E1 Use of AI Tools ระบุ Gemini

---

## 8) Prompt สั้น fore Gemini

```text
Read this handoff fully. Study the structure, tone, honesty rules, figure caption style, and appendix pattern of the sample Google Doc:
https://docs.google.com/document/d/1G4kJYuZ1Z-Eks_ZaK8y9DQBlDWBAbeSnu66zIM6TRKA/edit?usp=sharing

Write a complete course project report for OUR sleep DSS project using the SAME section numbering and academic English style as that sample.

Use the title:
SLEEPBEFORERISK: A TWO-STAGE WATCH-AWARE DECISION SUPPORT SYSTEM FOR SLEEP DISORDER SCREENING

Do NOT generate images. For every figure, insert a placeholder like [Insert Figure N here], then the exact caption and Source line from Section 4 of this handoff.
Use only facts from this handoff and attached project docs.
Do not claim medical diagnosis or real wearable API integration.
Separate model class from next-step action wording.
Include Appendices A–E and APA references.
Also prepare a Thai abstract (1 page) as an optional front insert if the instructor wants Thai.
```

---

## 9) Checklist ก่อนส่ง

- [ ] Cover matches MFU sample layout  
- [ ] Sections 1–20 present in order  
- [ ] Every figure has caption + Source  
- [ ] CV numbers are 0.904 / 0.881 (post-BP)  
- [ ] BP excluded; Unknown on items 2–5 documented  
- [ ] Limitations and AI-use honesty included  
- [ ] Appendices A–E included  
- [ ] No “AI diagnoses disease” language  
