# Incident Response Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Chief Information Security Officer
**Policy number:** SEC-004
**Effective date:** March 17, 2025
**Applies to:** All Northwind workers, systems and vendors involved in detecting, reporting, handling or recovering from security and operational incidents

---

## 1. Purpose

Northwind Cloud, Inc. ("Northwind") operates a multi-tenant platform on which its customers run critical business processes. When something goes wrong, whether it is an attack, an outage, a software defect or human error, the way Northwind responds determines how much harm is done and how quickly normal service returns. This Policy defines what counts as an incident, who does what, how decisions are made, how customers and regulators are kept informed, and how the company learns from each event.

## 2. Scope

The Policy covers security incidents (unauthorized access, malware, data exposure, denial of service, insider misuse), operational incidents (outages, degradations, failed deployments, data corruption) and privacy incidents (loss or exposure of personal data). It covers production, corporate and development environments, and systems operated for Northwind by vendors.

## 3. Definitions

- **Event** means any observable occurrence in a system or network.
- **Incident** means an event, or series of events, that compromises or threatens the security, availability, integrity or privacy of Northwind systems or data, or that violates a policy.
- **Major incident** means an incident rated Severity 1 or Severity 2 under Part 5.
- **Incident Commander (IC)** means the person who leads the response and makes decisions until the incident is closed.
- **Communications Lead** means the person responsible for internal and external messages during an incident.
- **Scribe** means the person who records the timeline and decisions.
- **Subject matter expert (SME)** means an engineer or specialist called on to diagnose or fix a problem.
- **Security Operations Center (SOC)** means the 24-hour team that monitors for security events.
- **Post-incident review (PIR)** means a blameless review held after an incident.
- **Indicators of compromise (IOCs)** means artifacts that indicate a system may have been compromised.

## 4. Roles and Responsibilities

### 4.1 Incident response team

| Role | Primary | Responsibilities |
|---|---|---|
| Incident Commander | On-call engineering manager (operational) or on-call security lead (security) | Declares and closes the incident, assigns roles, sets the cadence of updates, decides on containment and recovery |
| Technical Lead | Senior engineer for the affected service | Diagnoses, coordinates SMEs, proposes remediation |
| Communications Lead | Customer Support Director or delegate | Drafts and sends customer, status page and executive updates |
| Scribe | Any trained team member | Keeps the timeline, decisions and actions |
| Legal Liaison | Deputy General Counsel or delegate | Advises on legal duties, evidence and notifications |
| Privacy Liaison | Chief Privacy Officer or delegate | Assesses personal data impacts |
| Executive Sponsor | CISO (security) or CTO (operational) | Removes obstacles, approves major decisions |

### 4.2 Everyone

All workers must report suspected incidents immediately, preserve evidence, follow the instructions of the Incident Commander and avoid speculating about incidents in public or on social media.

## 5. Severity Levels

| Severity | Definition | Examples | Response time | Update frequency |
|---|---|---|---|---|
| Sev 1 (Critical) | Widespread loss of service, confirmed compromise of customer data, or active attack on production | Full platform outage, ransomware in production, exfiltration of customer records | Immediate; IC within 15 minutes | Every 30 minutes |
| Sev 2 (High) | Significant degradation affecting many customers, or credible threat to customer data | Regional outage, compromised privileged credential, serious vulnerability being exploited | IC within 30 minutes | Every hour |
| Sev 3 (Medium) | Limited impact on a small number of customers or non-production systems | Failing batch job, phishing email clicked with no further compromise | Within 4 hours | Every business day |
| Sev 4 (Low) | Minor issue with no customer impact | Single failed login alert, policy violation without exposure | Within 2 business days | As needed |

The Incident Commander may raise or lower the severity as more is learned.

## 6. Incident Lifecycle

### 6.1 Detection and reporting

Incidents are detected through monitoring and alerting, customer reports, worker reports, vendor notifications and external researchers. Alerts for production services page the on-call engineer. The SOC triages security alerts, and anything it cannot rule out within thirty minutes is escalated. Workers can report by calling the incident hotline, using the security mailbox or messaging the incident channel.

### 6.2 Triage and declaration

The first responder evaluates the report, gathers basic facts (what, where, since when, how many customers) and assigns a provisional severity. For Sev 1 and Sev 2, the first responder declares an incident, opens a dedicated chat channel and a video bridge, and pages the Incident Commander.

### 6.3 Containment

The Incident Commander directs steps to stop the incident from spreading, such as isolating hosts, disabling accounts, revoking tokens, blocking addresses, rolling back a release or failing over to another region. Containment decisions balance the harm of the incident against the disruption of the fix. Containment steps are recorded in the timeline.

### 6.4 Investigation and evidence

Responders gather logs, snapshots and memory images before systems are changed, where possible. Evidence is stored in the restricted evidence repository with chain-of-custody records. Forensic work that may support legal action is done only at the direction of the Legal Liaison, who may engage an outside forensic firm under privilege.

### 6.5 Eradication and recovery

Once the cause is understood, responders remove malicious artifacts, close vulnerabilities, rotate credentials and restore services from known good sources. Restored systems are monitored closely for at least seventy-two hours. The Incident Commander declares recovery complete only when the Technical Lead confirms that service levels are normal and no signs of the threat remain.

### 6.6 Closure

An incident is closed when recovery is complete, the immediate actions are done and a PIR has been scheduled for Sev 1 and Sev 2 incidents. The Scribe finalizes the timeline.

## 7. Communications

### 7.1 Internal

The Communications Lead keeps executives and affected teams informed at the cadence in Part 5. Updates state what is known, what is not known, what is being done and when the next update will be sent. Workers outside the response team should not speculate and should refer questions to the Communications Lead.

### 7.2 Customers

Customers are informed through the public status page and, for incidents that affect them directly, by email to their designated technical and security contacts. Notices are factual, avoid blame, and describe impact, workarounds and next steps. Where an incident has compromised customer data, the Privacy Liaison and Legal Liaison approve the notice before it is sent, and Northwind notifies affected customers without undue delay and in any event within 48 hours of confirmation.

### 7.3 Regulators and law enforcement

Only the General Counsel or the Deputy General Counsel may communicate with regulators, law enforcement or other authorities about an incident. Notification obligations depend on the facts, including the laws of the states and countries in which affected individuals live. The Legal Liaison maintains a notification matrix covering state breach laws, GDPR (72 hours), and sector-specific rules.

### 7.4 Media and public statements

All media inquiries go to Communications. No worker other than an approved spokesperson may comment publicly on an incident.

## 8. Specific Scenarios

### 8.1 Ransomware

Affected systems are isolated from the network immediately but kept powered on to preserve evidence. The Incident Commander declares a Sev 1. The Executive Sponsor and General Counsel decide on any engagement with the attacker. Northwind's policy is not to pay a ransom without Board approval and consultation with law enforcement and sanctions counsel.

### 8.2 Compromised credentials

When a credential is suspected to be exposed, it is revoked, the associated sessions are ended, and the account's recent activity is reviewed. If the credential was privileged, the Incident Commander considers a Sev 2 declaration and a review of all actions taken with the credential.

### 8.3 Cloud provider outages

For outages at a cloud provider, the Technical Lead follows the failover runbook for the affected region, and the Communications Lead relays updates from the provider's status pages. If recovery in the original region is not expected within the target recovery time, the team shifts to the secondary region.

### 8.4 Vendor incidents

When a vendor reports an incident that may affect Northwind, the Business Owner informs the Security team the same business day. The Incident Commander decides whether to open an incident. The Vendor and Third-Party Risk Policy governs follow-up with the vendor.

### 8.5 Insider threats

Reports about suspected misuse by a worker are handled by the Security team with Human Resources and Legal, and are not shared more widely than necessary. Access may be suspended while the matter is investigated.

### 8.6 Lost devices

A lost or stolen device is handled under the Information Security Acceptable Use Policy. The Security team confirms that the device was encrypted and remotely wipes it. If encryption cannot be confirmed, the Incident Commander considers a higher severity.

## 9. Post-Incident Review

### 9.1 Timing and attendance

For every Sev 1 and Sev 2 incident, the Incident Commander holds a PIR within five business days of closure. Attendees include the response team, service owners and relevant leaders. Sev 3 incidents are reviewed if the service owner or CISO asks.

### 9.2 Blameless approach

PIRs focus on how systems, processes and decisions allowed the incident to happen and how they can be improved, not on blaming individuals. Reviews cover: a timeline; the impact; root causes and contributing factors; what went well; what could be improved; and action items with owners and due dates.

### 9.3 Follow-up

Action items are tracked in the engineering backlog until complete. The CISO reports overdue items to the executive team monthly. A summary of each Sev 1 PIR is shared with the Audit Committee.

## 10. Preparedness

### 10.1 On-call

Engineering and the SOC maintain on-call rotations for 24-hour coverage. On-call engineers carry devices, acknowledge pages within five minutes and have runbooks for the services they support.

### 10.2 Exercises

The Security team runs a tabletop exercise at least twice a year, involving executives, Legal, Communications and Engineering, and a technical simulation once a year. Findings are reported to the CISO and added to the improvement plan.

### 10.3 Runbooks and tooling

Each critical service maintains an up-to-date runbook, contact list and dashboards. The incident management tool provides templates for channels, timelines and status updates. Contact details for key executives, vendors and external advisers are kept in an offline copy.

### 10.4 Backups and recovery objectives

Critical services have recovery time and recovery point objectives set by the CTO. Backups are tested quarterly by restoring a sample to an isolated environment. Results are reported to the CISO.

## 11. Metrics

The Security team reports monthly on: incidents by severity; time to detect, to contain and to recover; incidents by root cause; customer-reported versus internally detected incidents; PIR completion; and overdue action items. The CISO and CTO review trends quarterly.

## 12. Insurance

The Chief Financial Officer maintains cyber insurance. The Legal Liaison notifies the insurer of any incident that may give rise to a claim, within the period required by the policy, and coordinates the use of the insurer's panel of response providers.

## 13. Training

All workers learn how to report an incident in their annual security training. On-call engineers and Incident Commanders complete role-specific training before their first shift and an annual refresher. Executive Sponsors take part in at least one exercise a year.

## 14. Enforcement

Failing to report an incident, interfering with a response or destroying evidence may result in discipline up to termination. Good-faith reporting, including of one's own mistakes, is encouraged and protected.

## Appendix A. Incident Commander Checklist

1. Confirm the incident, the severity and the scope with the first responder.
2. Open the incident channel and video bridge; post the incident summary.
3. Assign the Technical Lead, Communications Lead, Scribe and liaisons.
4. Set the update cadence from Part 5 and announce it.
5. Ask the Technical Lead for the working theory and the current containment options.
6. Decide on containment steps; record the decision and reason.
7. Confirm that evidence is being preserved before systems are changed.
8. Keep the response team's size manageable; relieve people after four hours and arrange handover.
9. Approve customer updates with the Communications Lead.
10. Declare recovery complete only after verification, then schedule the post-incident review.

## Appendix B. Status Update Template

**Headline:** one sentence stating what is happening and its effect on customers.
**Impact:** which services, regions and customer groups are affected; whether data is involved.
**What we know:** facts confirmed so far, with times in UTC.
**What we do not know:** open questions.
**What we are doing:** current actions and owners.
**What customers can do:** workarounds, if any.
**Next update:** time of the next scheduled update.

## Appendix C. Evidence Handling

Responders must write down the time, source and method each time evidence is collected. Disk images and log exports are hashed on collection, and the hash is recorded. Evidence is transferred only to named people, through the secure evidence repository, and every access is logged. Working copies are used for analysis, and original evidence is left untouched. Evidence is retained for at least the period set in the Records Retention and Disposal Policy for security logs, and longer if a legal hold applies. Where an incident may become the subject of a legal claim, the Legal Liaison directs all investigative steps, so that analysis can be protected by legal privilege.

## Appendix D. Sample Timeline of a Sev 1 Incident

| Time (UTC) | Event |
|---|---|
| 14:02 | Alert: error rate on API gateway above threshold; on-call engineer paged |
| 14:07 | On-call confirms customer-facing impact; declares Sev 2 and opens incident channel |
| 14:15 | Impact grows to all regions; upgraded to Sev 1; Incident Commander assigned |
| 14:22 | Technical Lead identifies a faulty configuration pushed at 13:58 |
| 14:30 | First status page update published |
| 14:41 | Configuration rolled back in the primary region |
| 15:00 | Second update published; error rates falling |
| 15:20 | All regions healthy; monitoring continues |
| 17:30 | Incident Commander declares recovery; PIR scheduled |
| Next week | PIR identifies the missing validation in the deployment pipeline; action item opened |

## Appendix E. Contact Roster Maintenance

The Security team reviews the contact roster monthly. It lists on-call schedules, executives, the outside forensic firm, outside counsel, the cyber insurer's hotline, cloud provider support, the status page vendor, the public relations adviser and law enforcement liaison contacts. Every entry shows how to reach the contact outside normal hours. The roster is stored in the incident management tool and in an offline copy kept by each Incident Commander.

## 15. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | September 9, 2019 | Security team | Initial issue |
| 1.5 | May 24, 2022 | Security team | Added severity table and blameless review |
| 2.0 | October 17, 2023 | Security team | Added ransomware scenario and exercises |
| 2.1 | March 17, 2025 | Security team | Revised customer notification timelines; added insurance section |
