# Vendor and Third-Party Risk Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Vendor Risk Management, reporting to the Chief Financial Officer
**Policy number:** PRC-011
**Effective date:** January 15, 2025
**Applies to:** All Northwind workers who select, onboard, manage or pay a third-party vendor

---

## 1. Purpose and Scope

Northwind Cloud, Inc. ("Northwind") runs its platform on infrastructure, software and services supplied by several hundred outside companies. These range from hyperscale cloud providers, to customer support tooling, to recruiting agencies, to a small design studio that produces our conference materials. Each of them is a source of operational, security, privacy, financial and legal risk. This Policy sets out how Northwind selects vendors, assesses and monitors their risk, and ends relationships with them.

The Policy covers every third party that provides goods or services to Northwind in return for payment or other consideration, and every sub-processor that handles customer data on Northwind's behalf. It does not cover customers, employees or government bodies. Partners that both buy from and sell to Northwind are treated as vendors for the purposes of this Policy when they supply us with something.

## 2. Definitions

- **Vendor** means any third party supplying goods or services to Northwind.
- **Sub-processor** means a Vendor that processes customer personal data or customer content on Northwind's behalf.
- **Business Owner** means the Northwind employee who sponsors the vendor relationship and is accountable for it.
- **Vendor Risk Management (VRM)** means the team in Finance that runs the vendor lifecycle.
- **Critical Vendor** means a Vendor whose failure for more than four hours would interrupt service to customers, or that holds Restricted information.
- **Inherent risk** means the risk a Vendor presents before controls are considered.
- **Residual risk** means the risk remaining after controls have been verified.
- **Offboarding** means all steps taken when a vendor relationship ends, including return or destruction of Northwind information and revocation of access.

## 3. Ending a Vendor or Partner Relationship

Offboarding is where many third-party risks are realized: access that is never switched off, copies that are never deleted, and invoices that continue after services have stopped. The rules in this Part apply from the day Northwind gives notice of termination, or the day the relationship expires, whichever is earlier.

### 3.1 Return or destruction

Vendors and partners must be required to return or destroy our information when the relationship ends. The Business Owner confirms the exit method (return, destruction or both) with the Security team and records it in the offboarding checklist.

### 3.2 Time to complete

Return or destruction must be completed within 30 days of the end of the relationship or of our written request, whichever comes first. The vendor must certify completion in writing, signed by an officer of the vendor, and the Business Owner files the certificate in the vendor record. Where the relationship is a data-processing arrangement, the certificate must also state the systems from which the data was removed.

### 3.3 Nothing kept afterward

A vendor that handles personal data must not be allowed to keep any of our information once it has returned or destroyed it, whether in archives, backups or working files, unless the Chief Information Security Officer approves in writing. Where such approval is given, the Chief Information Security Officer records the reason, the retention period, the controls the vendor will keep in place and the date by which the remaining copies will be deleted. The approval is reviewed at least every six months until the copies are gone.

### 3.4 Protecting what we share

Vendor agreements must prohibit the vendor from reverse engineering, decompiling or disassembling any software, hardware or material that embodies our information. The prohibition is particularly important for vendors given pre-release builds, test hardware, security tooling or sandbox environments, because the material they hold can reveal how our platform works.

### 3.5 Access revocation

On the day the relationship ends, the Business Owner must ask IT to revoke the vendor's accounts, API keys, VPN profiles, badges and shared credentials, and must rotate any shared secrets. The Security team verifies revocation within two business days and logs it in the offboarding checklist.

### 3.6 Final reconciliation

Accounts Payable holds the final payment until the Business Owner confirms that the deliverables are complete and the offboarding checklist is closed. Prepaid balances are claimed back or applied to a credit memo.

## 4. Information Vendors Receive from Us and Pass On

### 4.1 Advisers and subcontractors

We must be allowed to share information we receive with our professional advisers, auditors, contractors and subcontractors who need it for the engagement. Northwind's outside counsel, external auditors, penetration testers and implementation contractors all handle information from our Vendors and customers, and a restriction that excluded them would stop us from doing our work.

### 4.2 Our own people

Our employees who need the information to do their jobs must be permitted to see it. A vendor-facing restriction on which Northwind employees may see vendor information would make ordinary engineering, finance and support work impossible.

### 4.3 Vendor subcontractors

A vendor may use a subcontractor to deliver services to Northwind only with the Business Owner's prior written consent, and only if the subcontractor is bound to the same security, privacy and offboarding obligations as the vendor. For Sub-processors, Northwind maintains a public list of approved sub-processors and gives customers thirty days' notice of additions, as promised in the customer data processing addendum.

## 5. Vendor Lifecycle

### 5.1 Intake

Any worker who wants to buy something from a new Vendor starts by submitting a Procurement Request. The request states what is being bought, the estimated annual spend, the data the Vendor will touch and the business justification. VRM routes the request to Security, Privacy and Finance reviewers within one business day.

### 5.2 Risk tiering

VRM assigns each Vendor an inherent-risk tier from the answers to a short questionnaire.

| Tier | Typical characteristics | Review depth |
|---|---|---|
| 1 (Critical) | Handles Restricted information, hosts production workloads or supports customer-facing functions | Full security assessment, privacy review, financial review, annual re-review |
| 2 (Important) | Handles Confidential information or integrates with internal systems | Security questionnaire, privacy review, re-review every two years |
| 3 (Standard) | No sensitive data, no integration, annual spend under $50,000 | Basic due diligence checks, re-review on renewal |

### 5.3 Due diligence

For Tier 1 and Tier 2 Vendors the reviewers examine, as applicable:

1. independent audit reports (SOC 2 Type II, ISO 27001) and their scope;
2. penetration-test summaries and remediation status;
3. business continuity and disaster recovery plans and the date of the last test;
4. insurance certificates, including cyber liability cover of at least $5 million for Tier 1;
5. financial statements or a credit report, to judge viability;
6. the Vendor's own vendor and sub-processor list;
7. sanctions, adverse-media and anti-corruption screening; and
8. references from comparable customers.

Where a Vendor cannot supply a document, the reviewer records a compensating control or a risk acceptance.

### 5.4 Contracting

Once the reviewers sign off, the Business Owner works with the Legal Department to paper the relationship. Contract approvals follow the Contract Approval Matrix. No Vendor may start work, and no data may be sent, until the agreement is fully signed.

### 5.5 Onboarding

After signature, VRM creates the vendor record, assigns a Business Owner and a backup, loads contract dates into the renewal calendar, and notifies Accounts Payable. IT provisions Vendor access under the principle of least privilege, using named accounts and single sign-on wherever possible. Shared accounts are not permitted without Security approval.

### 5.6 Ongoing monitoring

The Business Owner meets Tier 1 Vendors at least quarterly to review performance, incidents, open findings and roadmap changes. VRM subscribes to security-ratings feeds and adverse-news alerts for all Tier 1 and Tier 2 Vendors. A drop in rating below the threshold set by the CISO triggers a reassessment.

### 5.7 Renewal and exit decision

At least ninety days before a Tier 1 or Tier 2 Vendor's term ends, the Business Owner and VRM review performance, spend and risk and decide whether to renew, renegotiate or exit. Auto-renewals are disabled where possible. Decisions to exit start the Offboarding process in Part 3.

## 6. Security Requirements for Vendors

All Vendors that connect to Northwind systems or hold Northwind information must, at a minimum:

- encrypt Northwind information in transit and at rest using current industry standards;
- enforce multi-factor authentication for all administrative access;
- maintain a documented incident response plan and notify Northwind of any security incident affecting Northwind information within 48 hours of discovery;
- patch critical vulnerabilities within the time frames in the Information Security Acceptable Use Policy;
- limit access to personnel with a business need and remove access promptly on role change;
- run background checks on staff with access to Restricted information, where permitted by law; and
- permit Northwind or its auditors to review evidence of these controls on reasonable notice.

Sub-processors must additionally meet the requirements of the Data Protection and Privacy Policy.

## 7. Concentration and Resilience

VRM maintains a map of Critical Vendors and the services that depend on them. Where a single Vendor supports more than one critical service, the CISO and the Chief Technology Officer decide whether an alternative must be qualified. Each Critical Vendor must have a documented exit plan, reviewed annually, describing how Northwind would move to another provider or bring the service in-house, and an estimate of how long that would take.

## 8. Fourth-Party and Fintech Considerations

Where a Vendor relies on a fourth party for a material part of the service, the Business Owner asks for the identity of that party, the nature of the dependency and the Vendor's own oversight procedures. Payment-related Vendors must additionally provide evidence of PCI DSS compliance. Vendors that process Northwind payroll must also provide a SOC 1 report.

## 9. Roles and Responsibilities

- **Chief Financial Officer** is the executive sponsor of this Policy and approves vendor spend above the thresholds in the Contract Approval Matrix.
- **Vendor Risk Management** operates the lifecycle, keeps the vendor register and reports monthly to the CFO.
- **Business Owners** are accountable for the relationship, keep the vendor record current and run offboarding.
- **Security team and the Chief Information Security Officer** assess technical controls, approve exceptions in Part 3.3 and respond to vendor incidents.
- **Privacy Office** reviews data flows, sub-processor status and cross-border transfers.
- **Legal Department** reviews and negotiates vendor agreements.
- **Accounts Payable** pays only invoices for approved Vendors with a valid purchase order.
- **Internal Audit** tests compliance with this Policy annually.

## 10. Exceptions

A Business Owner who cannot comply with a requirement of this Policy must submit an exception request to VRM, stating the requirement, the reason, the risk and the compensating controls. The CISO approves exceptions with security implications, the Privacy Office those with privacy implications, and the CFO all others. Exceptions last for no more than twelve months and are logged in the vendor register.

## 11. Incident Escalation

A Business Owner who learns that a Vendor has suffered a security incident, outage or financial distress must tell VRM and the Security team the same business day. The Security team opens an incident under the Incident Response Policy where Northwind information may be affected. VRM keeps a record of the Vendor's remediation commitments and tracks them to completion.

## 12. Metrics and Reporting

VRM reports to the CFO and the Audit Committee each quarter on: the number of Vendors by tier; overdue assessments; open findings by severity; exceptions granted; offboarding checklists closed on time; and incidents involving Vendors. Internal Audit reports annually on the effectiveness of the program.

## 13. Training

Business Owners complete Vendor Management training within thirty days of being assigned their first Vendor and annually afterward. VRM runs a refresher session each quarter on common issues such as unauthorized purchases, missing offboarding steps and incomplete due diligence.

## 14. Enforcement

Engaging a Vendor outside this Policy, splitting purchases to avoid review, or failing to complete offboarding may lead to disciplinary action, including termination. Accounts Payable may refuse to pay invoices from Vendors that have not been approved.

## Appendix A. Vendor Onboarding Checklist

| Step | Owner | Evidence |
|---|---|---|
| Procurement Request approved | Business Owner | Request ID |
| Risk tier assigned | VRM | Questionnaire result |
| Security assessment completed (Tier 1 and 2) | Security team | Assessment report |
| Privacy review completed where personal data is involved | Privacy Office | Data flow diagram |
| Financial check completed (Tier 1) | Finance | Credit report |
| Insurance certificates received | VRM | Certificates on file |
| Agreement signed | Legal | Executed copy in repository |
| Purchase order issued | Procurement | PO number |
| Access provisioned with least privilege | IT | Access ticket |
| Vendor record created and renewal date set | VRM | Vendor register entry |

## Appendix B. Sample Quarterly Review Agenda for Tier 1 Vendors

1. Service performance against the agreed service levels, including outages and their causes.
2. Security and privacy matters: open findings, incidents, changes to sub-processors and new certifications.
3. Financial matters: spend against budget, upcoming renewals, pricing changes and credits owed.
4. Roadmap: planned changes that may affect Northwind and the vendor's view of Northwind's needs.
5. Relationship health: escalations, staffing changes and satisfaction scores.
6. Action items from the previous meeting and their owners.

## Appendix C. Common Vendor Categories and Typical Tiers

| Category | Examples | Typical tier |
|---|---|---|
| Cloud infrastructure | Compute, storage, networking, managed databases | 1 |
| Identity and security tooling | Single sign-on, endpoint protection, email security | 1 |
| Customer support tooling | Ticketing, chat, call recording | 1 or 2 |
| Payroll and benefits | Payroll processors, benefits administrators | 1 |
| Sales and marketing technology | CRM, marketing automation, analytics | 2 |
| Professional services | Outside counsel, auditors, consultants | 2 |
| Recruiting | Staffing agencies, background check providers | 2 |
| Facilities and office services | Cleaning, catering, furniture | 3 |
| Events and creative | Event producers, design studios | 3 |

## Appendix D. Vendor Performance Scorecard

Business Owners of Tier 1 and Tier 2 Vendors score each Vendor every six months on a scale of one to five in the following categories: quality of work; timeliness; responsiveness; security and compliance; value for money; and innovation. Scores below three in any category require an improvement plan agreed with the Vendor. Two successive scores below three for overall performance trigger a review of whether to continue the relationship. VRM publishes aggregated scores to department heads, so that purchasing decisions can take performance into account.

## 15. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | May 2, 2020 | Finance Operations | Initial issue |
| 1.2 | November 9, 2021 | Vendor Risk Management | Introduced risk tiers |
| 2.0 | April 18, 2023 | Vendor Risk Management | Added offboarding rules and sub-processor requirements |
| 2.1 | January 15, 2025 | Vendor Risk Management | Updated insurance thresholds; added concentration risk |
