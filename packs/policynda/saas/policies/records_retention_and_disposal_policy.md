# Records Retention and Disposal Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Office of the General Counsel, with the Chief Information Security Officer
**Policy number:** LEG-015
**Effective date:** January 6, 2025
**Applies to:** All Northwind workers, systems and vendors that create, hold or dispose of company records

---

## 1. Purpose and Scope

Northwind Cloud, Inc. ("Northwind") creates and receives a very large volume of records: customer agreements, invoices, engineering tickets, audit logs, emails, chat messages, recordings of support calls, personnel files, board minutes and backups of all of them. Keeping records for too short a time exposes the company to legal and operational risk; keeping them for too long increases storage costs, widens the impact of any breach and can breach privacy law. This Policy sets how long records are kept, how they are stored and protected, how they are put on hold when litigation is possible, and how they are destroyed.

The Policy covers records in every medium and location: corporate systems, cloud applications, laptops, mobile devices, removable media, paper files and the systems of vendors that hold records for Northwind. It applies to records that Northwind creates and to records it receives from customers, vendors and partners. Customer content hosted in the platform is governed by the customer's agreement and instructions and by Part 9 of this Policy.

## 2. Definitions

- **Record** means information, in any form, that evidences a business activity, transaction, decision or obligation, or that Northwind must keep by law.
- **Non-record** means a duplicate, draft of no continuing value, convenience copy or publicly available material.
- **Retention period** means the minimum period for which a record must be kept, counted from the trigger event stated in Schedule 1.
- **Legal hold** means an instruction from the General Counsel to preserve records relevant to actual or anticipated litigation, investigation or audit.
- **Records Coordinator** means the person in each department who is trained to manage that department's records.
- **Disposal** means secure deletion of electronic records or secure destruction of paper and physical media so that they cannot be reconstructed.
- **Backup** means a copy made solely to restore systems after a failure or loss.
- **System of record** means the designated repository where the official version of a record is kept.

## 3. Copies and How Long Obligations Run

### 3.1 Copies for backup and legal records

We must be allowed to make copies of information we receive to the extent needed for backup, disaster recovery and legally required records. Northwind's systems replicate data across availability zones and are backed up nightly, and finance, tax and legal teams are required to keep archival records for periods set by law. These copies are held under the same classification as the original and are destroyed on the schedule in Part 5. The Confidentiality and NDA Standard describes the protections that apply to information received from outside parties.

### 3.2 Longest period for surviving obligations

Obligations that survive the end of the agreement must not be stated to survive for more than 84 months. Seven years is the longest period for which Northwind can reliably track, remember and audit its post-termination obligations under this Policy's retention schedule, and an obligation that outlives the records that evidence it cannot be monitored. The minimum period for surviving obligations is set in the Confidentiality and NDA Standard.

### 3.3 Obligations after exit

When a relationship ends and the retention period for the associated records starts to run, the Records Coordinator updates the retention calendar so that the final disposal date for all related copies is recorded. Where a vendor holds Northwind records, the Business Owner ensures that the vendor's disposal obligations are tracked under the Vendor and Third-Party Risk Policy.

## 4. Retention Schedule

### 4.1 Schedule 1

| Record category | Retention period | Trigger event |
|---|---|---|
| Executed customer agreements and order forms | 7 years | End of the agreement |
| Executed vendor agreements | 7 years | End of the agreement |
| Legal Intake records and approvals | 7 years | Signature or closure |
| Invoices, credit memos and receipts | 7 years | End of fiscal year |
| General ledger, financial statements, audit workpapers | 10 years | End of fiscal year |
| Tax returns and supporting records | 7 years | Filing date |
| Payroll records | 7 years | End of tax year |
| Personnel files | 7 years | End of employment |
| Job applicant records (not hired) | 2 years | Decision date |
| Benefit plan records | 6 years | End of plan year |
| Board and committee minutes, resolutions | Permanent | None |
| Corporate formation and equity records | Permanent | None |
| Patent and trademark files | Life of right plus 6 years | Expiry or abandonment |
| Source code repositories and release records | 7 years | Release retirement |
| Security logs and audit trails | 1 year online, 6 years archived | Creation |
| Customer support tickets and transcripts | 3 years | Ticket closure |
| Call recordings | 90 days, unless flagged for training | Recording date |
| Customer content in the platform | Per customer instruction; deleted within 30 days of termination | Termination |
| Marketing leads and prospect data | 2 years since last interaction | Last interaction |
| Email and chat | 3 years | Message date |
| System backups | 35 days (rolling) | Backup date |

### 4.2 Exceptions to the schedule

A longer period applies where law, regulation or a contract requires it. A shorter period may be adopted only with the General Counsel's written approval and, for personal data, the Privacy Office's approval.

### 4.3 Personal data

Where Schedule 1 allows a range of periods for records containing personal data, the shortest period that meets the legal and business need is used. The Privacy Office reviews the schedule annually against the principle of storage limitation in the Data Protection and Privacy Policy.

## 5. Storage, Protection and Disposal

### 5.1 Systems of record

Each category of record has a system of record designated in the records inventory. Official versions are kept there, and other copies are non-records that may be deleted when no longer needed. Departments must not build shadow archives in personal drives or unmanaged tools.

### 5.2 Protection

Records are protected by the classification and handling rules in the Confidentiality and NDA Standard, and by the controls in the Information Security Acceptable Use Policy. Records held longer than three years are moved to archival storage with access limited to the Records Coordinator and Legal.

### 5.3 Scheduled disposal

Systems that support automated deletion are configured to delete records when the retention period expires. For other records, the Records Coordinator reviews the inventory every quarter and arranges disposal. The Coordinator records what was disposed of, when and by whom, in the disposal log, unless the record is a routine non-record.

### 5.4 Methods

- **Electronic records:** secure deletion by overwriting, cryptographic erasure or the cloud provider's certified deletion function.
- **Paper records:** cross-cut shredding or locked shred bins collected by a certified vendor.
- **Physical media and devices:** degaussing or physical destruction, with a certificate from the IT asset disposal vendor.

### 5.5 Backups

Backups are rotated on the schedule above. Restoring a backup to a production system requires a ticket approved by the Security team, and the restored data is re-subjected to deletion if any records had been deleted since the backup.

## 6. Legal Holds

### 6.1 Issuing a hold

The General Counsel issues a legal hold when litigation, a government inquiry or an audit is reasonably anticipated. The hold names the matter, the categories of records, the custodians and the systems affected, and it suspends scheduled disposal for those records.

### 6.2 Duties of custodians

Custodians must preserve all relevant records, including drafts and informal notes, must not alter or delete them, and must confirm in writing that they have complied. The Security team suspends auto-delete for custodians' mailboxes and chat accounts.

### 6.3 Releasing a hold

Only the General Counsel may release a hold, in writing. After release, records revert to the retention schedule, and anything past its period is promptly disposed of.

## 7. Departing Workers and Reorganizations

When a worker leaves, the manager and Records Coordinator identify any business records in the worker's accounts and move them to the system of record. The worker's mailbox is retained for ninety days and then archived or deleted in line with Schedule 1 unless a legal hold applies. On the sale, merger or wind-down of a business unit, the General Counsel decides who will take over responsibility for its records.

## 8. Vendor-Held Records

Vendors that hold Northwind records must retain and dispose of them in line with this Policy and the instructions in the agreement. The Business Owner obtains a certificate of destruction at the end of the relationship, and the Records Coordinator files it with the vendor record. Cloud hosting providers must support cryptographic erasure or equivalent deletion.

## 9. Customer Content

Northwind retains customer content in the platform only as long as needed to provide the service and as instructed by the customer. Within thirty days after termination of a customer subscription, Northwind deletes customer content from production systems, and within a further thirty-five days from backups, unless the customer has requested earlier return or the law requires retention. Northwind certifies deletion on request.

## 10. Roles and Responsibilities

- **General Counsel** owns this Policy, issues and releases legal holds and approves exceptions.
- **Chief Information Security Officer** secures records, configures deletion and oversees destruction vendors.
- **Records Coordinators** maintain the inventory, review the schedule and keep disposal logs.
- **Privacy Office** advises on personal data retention and data subject requests.
- **Department heads** make sure their teams follow the schedule.
- **IT** provides systems that support retention, deletion and holds.
- **All workers** keep records in approved systems, avoid creating unnecessary copies and dispose of non-records promptly.
- **Internal Audit** tests compliance annually.

## 11. Training

Records Coordinators complete a half-day course on joining and an annual refresher. All workers receive a short module on retention in their annual compliance training. The Legal Department publishes a one-page guide with the most common retention questions and answers.

## 12. Monitoring and Audit

The Security team reports quarterly on the volume of data held beyond its retention period. Internal Audit samples the disposal log and inventory annually. Findings are reported to the General Counsel and the Audit Committee, and the General Counsel decides on corrective actions.

## 13. Enforcement

Destroying records during a legal hold, or deleting records outside this Policy to hide information, is a serious violation that may result in termination and referral to authorities. Failure to dispose of records as required may result in disciplinary action.

## Appendix A. Disposal Request Procedure

1. The Records Coordinator generates a list of records whose retention periods have ended, using the inventory.
2. The list is sent to the department head, who confirms within ten business days that the records are not needed for any ongoing business activity.
3. The Legal Department checks the list against active legal holds.
4. If approved, the Records Coordinator or IT carries out disposal using the methods in Section 5.4.
5. The coordinator records the disposal in the log, including the category, date range, quantity, method, person responsible and a reference to any certificate.
6. For records disposed of by vendors, the vendor's certificate is attached to the log.

## Appendix B. Records Inventory Fields

Each entry in the records inventory shows: the record category; the owner; the system of record; the format; the retention period and trigger event; the legal or business reason for the period; whether the category contains personal data; the classification level; the disposal method; and the date of the last review. Departments update their entries whenever they adopt a new system or change how they store a category of records.

## Appendix C. Email and Chat Guidelines

Workers should treat email and chat as business records. Messages that evidence a decision, approval or commitment should be saved to the system of record. Workers should avoid using chat for lengthy discussions of formal matters, and should not use disappearing-message features. The company's retention settings keep messages for three years, after which they are deleted automatically unless a legal hold applies. Workers must not copy messages to personal accounts, delete mail to evade the schedule or use unapproved tools for business communication.

## Appendix D. Retention Review Calendar

| Month | Activity |
|---|---|
| January | Records Coordinators confirm inventory entries and the prior year's disposal log |
| March | Finance disposes of records whose periods ended at the previous fiscal year end |
| April | Privacy Office reviews personal data retention periods |
| June | IT tests restoration from backups and archives |
| September | Legal reviews the schedule against changes in law |
| November | Internal Audit samples disposal logs and holds |
| December | General Counsel approves any changes to Schedule 1 for the next year |

## Appendix E. Digitizing Paper Records

Paper records that must be kept may be scanned and the originals destroyed if the scan is complete, legible and stored in the system of record with a note of who made it and when, and if no law requires the original to be kept. Original documents with legal significance, such as signed corporate formation papers and stock certificates, are kept in the fire-resistant safe at headquarters. Scanning is done by trained staff or by a vendor under supervision, and a sample is checked for quality.

## 14. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | March 15, 2020 | Office of the General Counsel | Initial issue |
| 1.2 | October 8, 2021 | Office of the General Counsel | Added backups and customer content |
| 2.0 | July 25, 2023 | Office of the General Counsel | Added legal hold section; reorganized |
| 2.1 | January 6, 2025 | Office of the General Counsel | Revised schedule; added vendor-held records |
