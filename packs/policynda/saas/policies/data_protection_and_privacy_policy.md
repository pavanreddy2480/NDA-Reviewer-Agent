# Data Protection and Privacy Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Privacy Office, reporting to the General Counsel
**Policy number:** PRV-002
**Effective date:** April 1, 2025
**Applies to:** All Northwind workers, and all systems and vendors that process personal data for Northwind

---

## 1. Purpose and Scope

Northwind Cloud, Inc. ("Northwind") processes personal data in two capacities. As a **processor** (service provider), it hosts and handles personal data that enterprise customers place in the Northwind platform: their employees' names and business contact details, their end customers' account records, usage logs, support transcripts and in some cases payroll or benefits data. As a **controller** (business), it handles the personal data of its own workers, job applicants, website visitors, prospects and the employees of its customers and vendors.

This Policy sets out the principles Northwind follows to protect personal data, the duties of the people who handle it, and the specific controls that apply to common situations, including exchanges of personal data with customers, vendors and partners and transfers outside the United States. It supports compliance with the California Consumer Privacy Act as amended by the California Privacy Rights Act (CCPA/CPRA), the Virginia, Colorado and Connecticut privacy statutes, the New York SHIELD Act, the EU General Data Protection Regulation (GDPR) and UK GDPR, and Northwind's contractual commitments to customers.

## 2. Definitions

- **Personal data** means any information relating to an identified or identifiable individual, including names, email addresses, IP addresses, device identifiers, account numbers, location data, employment records and any inference drawn from such data.
- **Sensitive personal data** means personal data revealing government identifiers, financial account credentials, precise geolocation, health information, racial or ethnic origin, religious belief, union membership, biometric identifiers, or the personal data of a child.
- **Processing** means any operation performed on personal data, including collection, storage, use, disclosure, transfer and deletion.
- **Controller / business** and **processor / service provider** have the meanings given in the applicable law.
- **Data subject** means the individual to whom personal data relates.
- **Privacy Office** means the Chief Privacy Officer and the team of privacy counsel and analysts reporting to the General Counsel.
- **Data Protection Impact Assessment (DPIA)** means a structured assessment of the privacy risk of a proposed processing activity.
- **Restricted transfer** means a transfer of personal data from the European Economic Area, the United Kingdom or Switzerland to a country that has not been found to provide adequate protection.

## 3. Exchanging Personal Data With Outside Parties

### 3.1 Protection that does not depend on labels

Where personal data will be exchanged, protection may not depend on the disclosing party marking or labelling the information as confidential. Personal data arrives in Northwind in bulk, in support tickets, logs, screenshots and spreadsheets, and nobody can reasonably be expected to label every record. The obligation to protect personal data attaches to the nature of the data, not to the presence of a stamp.

### 3.2 Minimization before sharing

Before sending personal data to a customer, vendor or partner, the sender must ask whether the purpose can be met with less. Where it can, the sender must remove, mask, pseudonymize or aggregate the data first. Direct identifiers must not be sent when a stable internal identifier would do.

### 3.3 Approved channels

Personal data may be exchanged only through channels approved by the Security team: the customer portal, the managed secure file transfer service, the encrypted email gateway, and APIs authenticated with credentials issued through the secrets manager. Personal data must never be sent through consumer messaging apps, personal email or unmanaged file-sharing tools.

### 3.4 Records of disclosures

Each time Northwind discloses personal data to a third party outside a standard integration, the sender records in the privacy register the date, the recipient, the categories of data, the purpose and the legal basis. The register is reviewed by the Privacy Office each quarter.

## 4. International Transfers

### 4.1 Cross-border transfer mechanism

When personal data is transferred to or from a counterparty outside the United States, the agreement must incorporate the EU Standard Contractual Clauses or an equivalent transfer mechanism approved by the Privacy Office. The Privacy Office maintains the approved mechanisms, which at present are the Standard Contractual Clauses (controller-to-processor and processor-to-processor modules), the UK International Data Transfer Addendum and the Swiss addendum, together with certification under the EU-U.S. Data Privacy Framework where the recipient holds one.

### 4.2 Transfer impact assessments

For each restricted transfer the Privacy Office completes a transfer impact assessment that considers the laws of the destination country, the access powers of its public authorities, the supplementary measures proposed and the sensitivity of the data. The assessment is refreshed annually and whenever the destination country's laws change materially.

### 4.3 Data localization commitments

Northwind offers EU customers hosting in the Frankfurt and Dublin regions. Engineers and support staff must not move customer personal data out of the region selected by the customer, except as the customer instructs or as needed to resolve a support case under the controls in the support runbook.

## 5. Duration of Protection

### 5.1 Longer protection for personal data

When personal data is involved, the duty of confidence must last at least 36 months. The longer period reflects the time over which a leak of personal data can be used for fraud, identity theft or targeted phishing. The general minimum and maximum periods that apply to all other exchanges are in the Confidentiality and NDA Standard.

## 6. Principles of Processing

Northwind follows these principles in every processing activity.

1. **Lawfulness, fairness and transparency.** Every processing activity has a documented legal basis, and individuals are told in clear language what is done with their data.
2. **Purpose limitation.** Personal data is collected for specified purposes and is not used in ways incompatible with them.
3. **Data minimization.** Only the data needed for the purpose is collected and retained.
4. **Accuracy.** Reasonable steps are taken to keep data accurate and up to date.
5. **Storage limitation.** Personal data is kept no longer than necessary, as set in the Records Retention and Disposal Policy.
6. **Integrity and confidentiality.** Appropriate technical and organizational measures protect the data.
7. **Accountability.** Northwind can demonstrate compliance through records, assessments and audits.

## 7. Roles and Responsibilities

- **Chief Privacy Officer (CPO)** owns this Policy, advises the business, chairs the Privacy Council and reports to the Audit Committee quarterly.
- **Privacy Office** maintains the register of processing activities, runs DPIAs and transfer assessments, handles data subject requests and regulator inquiries, and reviews vendor and customer terms involving personal data.
- **Chief Information Security Officer** is responsible for technical and organizational security measures and for breach detection.
- **Product and Engineering leaders** build privacy into design (privacy by design and by default) and ensure data flows are documented.
- **Data Owners** are accountable for each dataset, including its purpose, legal basis, retention and access.
- **All workers** complete privacy training, handle personal data only as needed for their roles and report suspected incidents immediately.

## 8. Data Subject Rights

Individuals may have the right to access, correct, delete, port or restrict the use of their personal data, to opt out of sale, sharing or targeted advertising, and to object to certain processing. The Privacy Office operates a request portal and a toll-free number. Requests are verified, logged and answered within the statutory period, generally 45 days under U.S. state laws and one month under GDPR. Where Northwind acts as a processor, it forwards the request to the customer within five business days and assists the customer in responding, as the data processing addendum provides. Workers who receive a request by any channel must forward it to the Privacy Office the same day and must not respond themselves.

## 9. Privacy by Design and DPIAs

A DPIA is required before launching a new product feature, vendor or data use that involves sensitive personal data, large-scale profiling, systematic monitoring, automated decision-making that significantly affects individuals, or new use of existing data for an incompatible purpose. The product manager prepares the DPIA with the Privacy Office, which documents risks, mitigations and residual risk. High residual risks are escalated to the Privacy Council and may be accepted only by the Chief Privacy Officer.

## 10. Security of Personal Data

Personal data must be protected by controls proportionate to its sensitivity. At a minimum:

- sensitive personal data and data at rest in production are encrypted using current standards, with keys held in the managed key service;
- access is role-based, reviewed quarterly and logged;
- production personal data is not copied into development or test environments, except in masked form;
- logs and backups containing personal data are subject to the same retention limits as primary stores; and
- engineers handling personal data in support cases use the break-glass procedure, which requires a ticket reference and generates an access record.

## 11. Personal Data Breaches

A worker who suspects a personal data breach must report it to the Security team immediately. The Security team and the Privacy Office decide within 24 hours whether a breach has occurred and assess its scope. Where a breach affects customer personal data, Northwind notifies the affected customers without undue delay and in any event within 48 hours of confirming it, so that they can meet their own legal duties. Where Northwind is the controller, the General Counsel decides whether notice to regulators and individuals is required under state law, the GDPR (72 hours) or other applicable rules. All breaches, whether or not notified, are recorded in the incident register with the facts, effects and remedial action.

## 12. Vendors and Sub-processors

Vendors that process personal data for Northwind must pass the security and privacy review described in the Vendor and Third-Party Risk Policy, sign a data processing addendum reflecting this Policy, flow the same obligations down to their own sub-processors and support Northwind in meeting data subject requests and breach duties. The Privacy Office maintains the public list of Northwind's sub-processors and gives customers advance notice of changes.

## 13. Marketing and Communications

Marketing campaigns must respect opt-out and consent records. Cookies and similar technologies on Northwind's websites are managed through a consent banner that applies the visitor's regional setting. Email lists are not purchased or rented. Customer testimonials and logos are used only with written permission from the customer's authorized representative.

## 14. Employee and Applicant Data

Human Resources handles employee and applicant data under the Employee Privacy Notice. Access is limited to HR, the employee's management chain and, where necessary, Legal and Finance. Background checks are performed only where permitted by law, with consent where required. Monitoring of work systems is carried out under the Information Security Acceptable Use Policy and is limited to what is necessary for security and compliance.

## 15. Training and Awareness

All workers complete privacy training on joining and annually. Engineers, support staff and sales teams complete role-specific modules. The Privacy Office publishes quarterly bulletins and holds office hours every week.

## 16. Audit and Enforcement

The Privacy Office tests compliance through quarterly control reviews, and Internal Audit examines the program each year. Violations may result in disciplinary action up to termination, and in some cases civil or criminal penalties for the individuals involved. Workers who report concerns in good faith are protected from retaliation.

## Appendix A. Categories of Personal Data Northwind Handles

| Category | Examples | Typical source | Typical purpose | Sensitivity |
|---|---|---|---|---|
| Customer user data | Names, work emails, job titles, login history | Customer administrators | Provide the service | Medium |
| End-customer records | Account numbers, transaction history, addresses | Customer uploads | Provide the service | High |
| Support data | Tickets, screenshots, call recordings | Customer users | Resolve cases | Medium to high |
| Usage telemetry | Device identifiers, IP addresses, feature use | Platform | Operate and improve the service | Low to medium |
| Prospect data | Business contact details, event attendance | Marketing | Sales outreach | Low |
| Worker data | Payroll, benefits, performance reviews, identifiers | Workers | Employment administration | High |
| Applicant data | Resumes, interview notes, references | Candidates | Recruiting | Medium |
| Vendor contact data | Names and business emails of vendor staff | Vendors | Manage relationships | Low |

## Appendix B. Lawful Bases Under GDPR

Where GDPR applies, each processing activity relies on one of the following bases, which the Privacy Office records in the register of processing activities: performance of a contract with the individual; compliance with a legal obligation; the legitimate interests of Northwind or a third party, after a balancing test; consent that is freely given, specific, informed and withdrawable; protection of vital interests; or the performance of a task in the public interest. Northwind relies on consent for non-essential cookies and certain marketing, and on legitimate interests for security monitoring, service improvement and fraud prevention. For processing carried out as a processor, the customer determines the basis.

## Appendix C. Data Subject Request Handling Steps

1. **Receive.** The request arrives through the portal, email, phone or any worker. Workers forward requests to the Privacy Office the same day.
2. **Verify.** The Privacy Office confirms the requester's identity using information already held, without collecting more sensitive data than necessary.
3. **Classify.** The request is classified as access, deletion, correction, portability, opt-out or objection. Requests relating to customer content are redirected to the customer, with the requester informed.
4. **Search.** The Privacy Office asks system owners to search their systems, using the data map.
5. **Assess.** Legal reviews any exemptions, for example data needed to defend legal claims or comply with the records schedule.
6. **Respond.** The response is sent in the statutory period, with an explanation of any refusal and of the right to appeal.
7. **Record.** The request, decision and evidence are logged and retained for three years.

## Appendix D. Privacy Metrics

The Privacy Office reports each quarter on: the number of data subject requests received and the median time to complete them; DPIAs completed and open; sub-processors added and removed; privacy incidents by severity; training completion; and the number of vendors with a current data processing addendum. The Audit Committee reviews the report and may ask for deeper analysis of any area.

## Appendix E. Children's Data

Northwind's services are intended for business users and are not directed at children under 16. Workers must not knowingly collect personal data from children. If a worker learns that a child's data has been collected, they must tell the Privacy Office, which will arrange deletion unless the law requires otherwise. Customers who use the platform to process children's data, such as schools, are responsible for obtaining any necessary parental permissions and are reminded of this in the data processing addendum.

## 17. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | August 12, 2019 | Privacy Office | Initial issue following CCPA readiness project |
| 1.3 | January 5, 2021 | Privacy Office | Added international transfer section after Schrems II |
| 2.0 | December 9, 2022 | Privacy Office | Updated for CPRA, Virginia and Colorado laws |
| 2.2 | April 1, 2025 | Privacy Office | Added Data Privacy Framework certification; aligned with records schedule |
