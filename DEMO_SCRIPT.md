# PRESENTATION DEMO SCRIPT
# Dharwad District Child Adoption Monitoring System (DDCAPMS)
# Estimated Total Time: 10 Minutes

---

## STEP 1 — Show Login Page (30 sec)
- Navigate to `http://localhost:5000`
- Point to the child character illustration and animated headline
- Say: *"This is the unified login portal for all 7 roles in our system.
  Each role sees a completely different dashboard with role-specific colors."*

---

## STEP 2 — Admin Dashboard (1 min)
**Login:** `admin@dharwad.gov.in` / `admin123`

- Show the 4 animated stat cards with number counters.
- Point to: *"All data comes live from our MySQL database."*
- Show the 4 interactive Chart.js graphs.
- Open the notification bell — show unread notifications.
- Click **[Generate PDF Report]** to download the official district report.
- Say: *"In 2 seconds, admin has full visibility of the entire district."*

---

## STEP 3 — Orphanage Flow (1 min)
**Login:** `sneha@orphanage.com` / `orphan123`

- Show the Orphanage Dashboard with stat cards.
- Click **[Register New Child]** — show the drag-and-drop photo upload form.
- Fill in: Name, Age, Gender, Health Status, How child came.
- Click **Submit** — show SweetAlert2 confirmation dialog.
- Go back to "My Children" — show **[Submit to CWC]** button.
- Click it — say: *"Child now moves to CWC review stage. Status updates instantly."*

---

## STEP 4 — CWC Flow (30 sec)
**Login:** `cwc@dharwad.gov.in` / `cwc123`

- Show the CWC Dashboard — pending review section.
- Click **Review** on a child.
- Fill the investigation form: Background Verified ✅, Medical Examined ✅.
- Click **Approve** — issue order number `CWC/DHW/2026/001`.
- Say: *"Child is now declared Legally Free for adoption under JJ Act §36."*

---

## STEP 5 — Parent Flow (2 min)
**Login:** `veena@gmail.com` / `parent123`

- Show the Parent Dashboard — home study status "Completed ✅".
- Click **Browse Children** — show card grid with filters.
- Use Age and Gender filters — show live filtering.
- Click **Apply** on Arjun Kumar (age 5).
- In the 3-step Apply Form:
  - Step 1: Enter DOB → watch age auto-calculate + eligibility check.
  - Step 2: Fill personal info.
  - Step 3: Upload documents — show drag-and-drop + green checkmarks.
- Submit the application.
- Click **Track Status** — show the 7-step progress bar.

---

## STEP 6 — Admin Approval with Consent (1 min)
**Login:** `admin@dharwad.gov.in` / `admin123`

- Go to **Applications** — see Veena's new application.
- Click **Review**.
- Show age validation: *"Age gap: 29 years ✅ — CARA eligible."*
- Check documents uploaded: ID ✅, Income ✅, Marriage ✅, Medical ✅.
- Select a Social Worker for Consent Assessment.
- Click **Approve**.
- Show the flash message:
  *"Application approved! Consent Assessment assigned — child is 5+ years, JJ Act §58(3) applies."*

---

## STEP 7 — Child Consent Assessment (1 min)
**Login:** `rekha.sw@dharwad.gov.in` / `sw123`

- Show the Social Worker Dashboard — "Child Consent Assessments" section.
- Click **Start Assessment** for Arjun Kumar.
- Show the legal banner: *"JJ Act 2015 §58(3) — consent is mandatory."*
- Fill: Child met parents ✅, Reaction: Happy 😊.
- Enter verbal response: *"Mujhe yeh aunty uncle achhe lagte hain."*
- Select **Child appears willing ✅**.
- Click Submit — show SweetAlert2 confirmation.
- Confirm — see flash: *"Consent obtained! Proceeding to foster care."*

---

## STEP 8 — Court Process (1 min)
**Login:** `court@dharwad.gov.in` / `court123`

- Show Court Dashboard with pending cases.
- Click **Schedule Hearing** — fill date, time, venue, judge name.
- Go to **Track Status** as parent — show hearing details with purple info box.
- Back as Court — click **Issue Order** after hearing.
- Upload scanned order — show order number `DCF/HBL/2026/001`.
- Show parent notification: *"Court order issued! Download available."*

---

## STEP 9 — Show Completed Case (30 sec)
**Login:** `admin@dharwad.gov.in` / `admin123`

- Show Sunita Patil's completed adoption (Rohan Joshi).
- Show all 3 follow-up visits: ✅ 1 month, ✅ 6 months, ✅ 1 year.
- Show status: **COMPLETED — ADOPTION FINAL**.
- Click **Download PDF Report** — show the official printable report.
- Say: *"Full lifecycle from child registration to adoption complete — all tracked."*

---

## STEP 10 — Show Database (1 min)
Open **MySQL Workbench** or run `mysql -u root -p adoption_db`:

```sql
SHOW TABLES;
SELECT name, status FROM child;
SELECT id, status FROM application;
SELECT * FROM child_consent LIMIT 5;
```

Say: *"11 normalized tables. Every action is recorded. Zero corruption possible."*

---

## TOTAL TIME: ~10 Minutes
