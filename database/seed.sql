-- Synthetic demo data. No real systems, people or organisations.
INSERT INTO controls (id,name,domain,objective,risk,test_procedure,owner,frequency) VALUES
('IAM-001','MFA','Identity & Access','Ensure multi-factor authentication is enforced for all interactive users.','Account takeover through stolen or guessed credentials.','Compare the active user list against the MFA enrollment export; every active user must be enrolled.','IAM Team','Quarterly'),
('IAM-002','Privileged Access','Identity & Access','Ensure privileged access is properly authorized.','Unauthorized privileged access.','Compare assigned administrative roles against approved access records.','Infrastructure Security','Quarterly'),
('AC-003','Access Expiration','Access Control','Ensure temporary access is revoked on its approved expiry date.','Stale access remains after business need ends.','Compare temporary access grants against their expiry dates in the access export.','IT Operations','Quarterly'),
('AC-004','Periodic User Access Review','Access Control','Ensure managers review and certify user access periodically.','Excessive access accumulates unnoticed.','Verify that every in-scope application has a completed, signed-off review for the period.','IT Operations','Quarterly'),
('CM-001','Change Approval','Change Management','Ensure production changes are approved before deployment.','Unauthorized or untested changes cause outages.','Sample production changes and confirm an approval timestamp precedes deployment.','Change Advisory Board','Quarterly'),
('CM-002','Emergency Change Review','Change Management','Ensure emergency changes are reviewed after implementation.','Emergency path is used to bypass normal approval.','Confirm every emergency change has a post-implementation review within 5 business days.','Change Advisory Board','Quarterly'),
('BK-001','Backup Job Monitoring','Resilience','Ensure scheduled backups complete successfully.','Data loss due to unnoticed backup failures.','Review backup job logs for the period; failures must have a documented re-run.','Infrastructure Operations','Monthly'),
('BK-002','Restore Testing','Resilience','Ensure backups can actually be restored.','Backups exist but cannot be restored.','Inspect the latest restore test record: success status and recovery time within target.','Infrastructure Operations','Semi-annual'),
('LOG-001','Log Retention','Monitoring','Ensure security logs are retained for the required period.','Insufficient data for incident investigation.','Compare configured retention per log source against the policy minimum.','Security Operations','Semi-annual'),
('VM-001','Critical Patching','Vulnerability Mgmt','Ensure critical patches are applied within the SLA.','Exploitation of known vulnerabilities.','Compare critical vulnerabilities against patch dates; flag items older than 14 days.','Infrastructure Operations','Monthly');

INSERT INTO evidence (id,control_id,filename,description,collected_on) VALUES
(1,'IAM-001','mfa_enrollment_2026_08.csv','MFA enrollment export - August','2026-08-12'),
(2,'IAM-001','mfa_enrollment_2026_09.csv','MFA enrollment export - September (retest)','2026-09-20'),
(3,'IAM-002','access_review_2026_09.csv','Admin roles vs approved access records','2026-09-15'),
(4,'AC-003','access_expiration_2026_09.csv','Temporary access grants and expiry dates','2026-09-05'),
(5,'AC-004','user_access_review_q3_2026.csv','Q3 access review completion tracker','2026-09-10'),
(6,'CM-001','change_sample_q3_2026.csv','Sample of production changes with approvals','2026-09-08'),
(7,'BK-001','backup_jobs_2026_09.csv','Backup job log - September','2026-09-12'),
(8,'BK-002','restore_test_2026_09.csv','Restore test record','2026-09-14'),
(9,'LOG-001','log_retention_config_2026_09.csv','Retention per log source','2026-09-16'),
(10,'VM-001','critical_patch_report_2026_09.csv','Critical vulnerabilities and patch dates','2026-09-18');

INSERT INTO control_tests (id,control_id,test_date,tester,result,evidence_id,notes,is_retest) VALUES
(1,'IAM-001','2026-08-12','GRC Analyst','FAIL',1,'3 active users not enrolled in MFA.',0),
(2,'IAM-001','2026-09-20','GRC Analyst','PASS',2,'Retest: all active users enrolled.',1),
(3,'IAM-002','2026-09-15','GRC Analyst','FAIL',3,'2 admin accounts without current approval.',0),
(4,'AC-003','2026-09-05','GRC Analyst','FAIL',4,'4 temporary grants past expiry.',0),
(5,'AC-004','2026-09-10','GRC Analyst','PASS',5,'All applications certified.',0),
(6,'CM-001','2026-09-08','GRC Analyst','PASS',6,'25/25 sampled changes approved before deployment.',0),
(7,'CM-002','2026-09-25','GRC Analyst','PENDING',NULL,'Awaiting emergency change list from CAB.',0),
(8,'BK-001','2026-09-12','GRC Analyst','PASS',7,'All failures re-run within 24h.',0),
(9,'BK-002','2026-09-14','GRC Analyst','PASS',8,'Restore succeeded within RTO.',0),
(10,'LOG-001','2026-09-16','GRC Analyst','PASS',9,'All sources meet 12-month minimum.',0),
(11,'VM-001','2026-09-18','GRC Analyst','FAIL',10,'5 critical vulnerabilities unpatched beyond SLA.',0);

INSERT INTO findings (id,control_id,test_id,title,severity,description,owner,remediation_plan,due_date,status,opened_on,closed_on,retest_result) VALUES
(1,'IAM-002',3,'Unauthorized Admin Access','HIGH','2 users have administrative privileges without current approval.','Infrastructure Security',NULL,'2026-10-15','OPEN','2026-09-15',NULL,NULL),
(2,'AC-003',4,'Expired Access Approval','MEDIUM','4 temporary access grants remain active after their approved expiry date.','IT Operations','Revoke expired grants and add automated expiry job.','2026-09-25','IN_REMEDIATION','2026-09-05',NULL,NULL),
(3,'IAM-001',1,'Missing MFA','HIGH','3 active users are not enrolled in MFA.','IAM Team','Enforce enrollment via conditional access policy.','2026-09-15','CLOSED','2026-08-12','2026-09-20','PASS'),
(4,'VM-001',11,'Critical Patches Beyond SLA','HIGH','5 critical vulnerabilities remain unpatched beyond the 14-day SLA.','Infrastructure Operations',NULL,'2026-09-20','OPEN','2026-09-18',NULL,NULL);

INSERT INTO finding_history (finding_id,changed_on,from_status,to_status,note) VALUES
(1,'2026-09-15',NULL,'OPEN','Finding opened from failed test.'),
(2,'2026-09-05',NULL,'OPEN','Finding opened from failed test.'),
(2,'2026-09-12','OPEN','IN_REMEDIATION','Remediation plan approved.'),
(3,'2026-08-12',NULL,'OPEN','Finding opened from failed test.'),
(3,'2026-08-20','OPEN','IN_REMEDIATION','Remediation plan approved.'),
(3,'2026-09-18','IN_REMEDIATION','READY_FOR_RETEST','Conditional access policy enforced.'),
(3,'2026-09-20','READY_FOR_RETEST','CLOSED','Retest PASS: all active users enrolled.'),
(4,'2026-09-18',NULL,'OPEN','Finding opened from failed test.');
