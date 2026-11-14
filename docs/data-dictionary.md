# พจนานุกรมข้อมูล

ตารางนี้ครอบคลุมคอลัมน์ใน `Sleep_health_and_lifestyle_dataset.csv` (374 แถว) และตัวแปรที่ใช้ก่อนส่งเข้าโมเดล ชื่อคอลัมน์และค่าหมวดหมู่คงเป็นภาษาอังกฤษตามไฟล์ต้นทาง ตัวอย่างมาจากแถว `Person ID` 1 เว้นแต่จะระบุไว้เป็นอย่างอื่น

บทบาทใช้ตาม Project Guidance ข้อ 4.4

## ตัวแปรในไฟล์ข้อมูล

| ตัวแปร | ชนิดข้อมูล | คำอธิบาย | ตัวอย่าง | บทบาท |
| --- | --- | --- | --- | --- |
| Person ID | Integer | รหัสบุคคลในไฟล์ มีค่าไม่ซ้ำ 1 ถึง 374 ไม่ได้ใช้ทำนาย | 1 | Identifier |
| Gender | Categorical | เพศที่บันทึกในตาราง มีสองค่า คือ Female และ Male | Male | Input feature |
| Age | Integer | อายุเป็นปี ค่าในตารางอยู่ที่ 27–59 | 27 | Input feature |
| Occupation | Categorical | อาชีพ มี 11 ค่าในตารางฝึก ได้แก่ Accountant, Doctor, Engineer, Lawyer, Manager, Nurse, Sales Representative, Salesperson, Scientist, Software Engineer และ Teacher | Software Engineer | Input feature |
| Sleep Duration | Numeric | ระยะเวลานอนเป็นชั่วโมง ค่าในตารางอยู่ที่ 5.8–8.5 สอดคล้องกับค่าที่สมาร์ทวอทช์ทั่วไปรายงาน | 6.1 | Input feature |
| Quality of Sleep | Integer | คะแนนคุณภาพการนอนในสเกล 1–10 ค่าในตารางอยู่ที่ 4–9 ในเดโมให้แมปจาก sleep score ของนาฬิกา | 6 | Input feature |
| Physical Activity Level | Integer | กิจกรรมทางกายเป็นนาทีต่อวัน ค่าในตารางอยู่ที่ 30–90 | 42 | Input feature |
| Stress Level | Integer | คะแนนความเครียดในสเกล 1–10 ค่าในตารางอยู่ที่ 3–8 ในเดโมให้แมปจากคะแนนความเครียดของนาฬิกา (มักประมาณจาก HRV) | 6 | Input feature |
| BMI Category | Categorical | หมวดดัชนีมวลกายในไฟล์ต้นทาง มี Normal, Normal Weight, Overweight และ Obese ก่อนเข้าโมเดล ค่า Normal Weight 21 แถวถูกเปลี่ยนเป็น Normal | Overweight | Input feature |
| Blood Pressure | Text | ความดันในรูปตัวบน/ตัวล่าง หน่วย mmHg ค่าในตารางอยู่ที่ 115–142 สำหรับตัวบน และ 75–95 สำหรับตัวล่าง **ไม่เข้าโมเดล** เพราะไม่ใช่ค่าที่สมาร์ทวอทช์ทั่วไปมี | 126/83 | Variable excluded from the model |
| Heart Rate | Integer | อัตราชีพจรขณะพัก หน่วยครั้งต่อนาที ค่าในตารางอยู่ที่ 65–86 | 77 | Input feature |
| Daily Steps | Integer | จำนวนก้าวต่อวัน ค่าในตารางอยู่ที่ 3,000–10,000 | 4200 | Input feature |
| Sleep Disorder | Categorical | ป้ายกลุ่มเป้าหมาย มี None 219 แถว, Sleep Apnea 78 แถว และ Insomnia 77 แถว คำว่า None คือไม่มีภาวะผิดปกติ ไม่ใช่ค่าว่าง | None | Target variable |

## ตัวแปรที่สร้างก่อนเข้าโมเดล

โมเดลเวอร์ชันปัจจุบัน (`MODEL_VERSION = 2`) **ไม่สร้าง** `Systolic_BP` / `Diastolic_BP` อีกต่อไป คอลัมน์ Blood Pressure ใน CSV ถูกเก็บไว้เป็นข้อมูลอ้างอิงเท่านั้น

ฟอร์มประเมินรับน้ำหนักเป็นกิโลกรัมและส่วนสูงเป็นเซนติเมตร แล้วคำนวณหมวด BMI ตามเกณฑ์ WHO ก่อนส่งเข้าโมเดล สองค่านี้ไม่มีในไฟล์ข้อมูล โมเดลเห็นเฉพาะหมวด BMI Category

อาชีพ Other และ Student (นักเรียน/นักศึกษา) ใช้ได้ตอนกรอกแบบประเมิน แต่ไม่มีในตารางฝึก โมเดลถือเป็นค่าที่ไม่เคยเห็น

## แหล่งข้อมูลในเดโม

| กลุ่ม | แหล่งที่มาใน UI |
| --- | --- |
| เพศ อายุ อาชีพ น้ำหนัก ส่วนสูง | กรอกเอง |
| Sleep Duration, Quality of Sleep, Physical Activity, Stress Level, Daily Steps, Heart Rate | แนะนำจากสมาร์ทวอทช์ทั่วไป (มีปุ่มเดโม + ป้าย Watch) |
