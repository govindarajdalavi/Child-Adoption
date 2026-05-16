# Q&A ANSWERS — DDCAPMS Presentation
# Dharwad District Child Adoption Monitoring System

---

## Q: Where is data stored?
**A:** MySQL database named `adoption_db` on `localhost:3306`.
Tables: `user`, `child`, `child_document`, `cwc_order`, `home_study`,
`child_consent`, `application`, `follow_up`, `complaint`, `notification`,
`audit_log`.

---

## Q: Why Flask?
**A:** Flask is a lightweight Python web framework ideal for government projects:
- Supports **Blueprints** for clean separation of 7 roles.
- Easy MySQL integration via **SQLAlchemy ORM**.
- **Jinja2** template engine for dynamic HTML pages.
- Runs on any Python 3.8+ server — low infrastructure cost.

---

## Q: How does the database connect?
**A:** `config.py` holds the connection string:
```
mysql+pymysql://root:password@localhost/adoption_db
```
SQLAlchemy creates a connection pool. All queries go through ORM models — no
raw SQL is needed for standard operations.

---

## Q: What is ORM?
**A:** Object-Relational Mapping. Python classes map to database tables:
- `Child.query.all()` → `SELECT * FROM child`
- `Application.query.filter_by(status='pending')` → `SELECT * FROM application WHERE status='pending'`
No need to write raw SQL. Prevents SQL-injection attacks automatically.

---

## Q: What languages are used?
**A:**
| Layer | Technology |
|-------|------------|
| Backend logic | Python 3.12 |
| Web framework | Flask |
| Database | MySQL via SQLAlchemy |
| Templates | Jinja2 (HTML) |
| Frontend | Bootstrap 5, CSS3, JavaScript |
| Charts | Chart.js |
| PDF reports | ReportLab |
| Icons | Font Awesome 6 |

---

## Q: How are passwords secured?
**A:** Flask-Bcrypt hashes passwords using the bcrypt algorithm (cost factor 12).
Even if the database is compromised, passwords cannot be read. The original
password is never stored anywhere.

---

## Q: What is a Blueprint?
**A:** A Flask feature to organize routes by role. Each role has its own file:
`routes_admin.py`, `routes_parent.py`, `routes_court.py`, etc.
Each is registered as a separate Blueprint with its own URL prefix.
This keeps code modular and maintainable.

---

## Q: What is the legal basis?
**A:**
| Law | Sections Used |
|-----|--------------|
| Juvenile Justice Act 2015 | §27 (CWC), §35 (Surrender), §36 (Legally Free), §56–60 (Adoption), §58(3) (Child Consent) |
| CARA Guidelines 2022 | Reg 8 (Home Study), Reg 11 (Foster Care ≥ 30 days), Reg 12 (Court Order), Reg 13 (3 Follow-Up Visits) |
| Hindu Adoption & Maintenance Act 1956 | §6 (Valid Adoption), §10 (Who can be adopted) |
| Guardian & Wards Act 1890 | §7, §11, §17 |

---

## Q: How does age validation work?
**A:** CARA Guidelines 2022 rules:
| Rule | Requirement |
|------|------------|
| Min parent age | 25 years |
| Max age for child 0–2 yrs | Parent age ≤ 45 |
| Max age for child 2–8 yrs | Parent age ≤ 50 |
| Max age for child 8–18 yrs | Parent age ≤ 55 |
| Min age gap (parent − child) | ≥ 25 years |
| Max combined couple age | ≤ 110 years |

Both frontend JavaScript (instant feedback) and backend Python (server-side validation) enforce these rules. Applications that fail validation are automatically blocked.

---

## Q: What is child consent and why is it important?
**A:** Under JJ Act 2015 §58(3), for children aged **5 years and above**,
the child's consent is **legally mandatory** before an adoption order can be issued.
A social worker visits the child, records their reaction, verbal response, and body language.
If the child **refuses**, the adoption is **immediately stopped** and:
- Application status → `consent_refused`
- Parent, Admin, Court notified automatically
- Child returned to the available pool

Our system is one of the few district-level systems that fully implements this legal requirement digitally.

---

## Q: Why not just use the CARA portal?
**A:**
| CARA Portal | Our System |
|-------------|------------|
| National-level matching | District-level coordination |
| Inter-state / inter-country adoptions | Local orphanage ↔ local court ↔ local admin |
| No real-time local tracking | Real-time status for Dharwad parents |
| No emergency escalation | Emergency escalation to collector |
| No complaint management | Full complaint lifecycle |

Our system **works alongside CARA** — it is the "local road network" connecting Dharwad to the CARA "national highway."

---

## Q: Is an advocate compulsory in the court process?
**A:** No. JJ Act 2015 does not mandate an advocate for domestic adoption.
Parents can appear directly before the Family Court judge.
Our system tracks this process but does **not replace** the physical hearing —
the judge must sign the physical order.

---

## Q: How is the adoption certificate issued?
**A:** Our system **never generates the certificate itself**.
After the physical court hearing, the court clerk:
1. Updates the hearing result in the system.
2. Uploads a **scanned copy** of the original signed order.
3. The parent collects the original physical certificate from the court.
This follows the real legal process — the digital copy is for reference only.

---

## Q: What happens if adoption fails after placement?
**A:**
1. Social worker submits a follow-up visit and marks status **Critical 🚨**.
2. System **automatically notifies** the court for an emergency hearing.
3. Court schedules emergency session.
4. Judge can cancel the adoption order.
5. Child is returned to the orphanage.
6. All of this is fully tracked in our audit log.

---

## Q: How does the audit trail prevent corruption?
**A:** Every action (approve, reject, consent, assign, etc.) is recorded in the
`audit_log` table with:
- User ID + name + role
- Timestamp
- IP address
- Exact action + details

This log **cannot be edited or deleted** (no delete route exists for audit_log).
The District Collector can view the full audit trail at any time.
Full transparency = zero room for corruption.

---

## Q: How can this scale to other districts?
**A:** The system is designed for scalability:
- `config.py` holds all district-specific settings (database, name).
- Changing `DISTRICT_NAME = "Belagavi"` adapts all PDF reports and labels.
- Each district gets its own MySQL instance.
- A central state-level dashboard can aggregate data from all 30 Karnataka districts.
- NIC (National Informatics Centre) infrastructure can host multi-district deployment.

---

## Q: What is the real-world impact?
**A:**
| Metric | Before System | After System (Target) |
|--------|--------------|----------------------|
| Time per adoption | 3–5 years | 6–12 months |
| Parent office visits | 100+ | 3–4 physical visits only |
| File loss rate | High | Zero (fully digital) |
| Corruption potential | High | Zero (audit trail) |
| Child consent compliance | Often skipped | 100% enforced |
| Post-adoption follow-ups | Often skipped | 100% tracked |

---

*Created for DDCAPMS presentation — Dharwad District, Karnataka*
