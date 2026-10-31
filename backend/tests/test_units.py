import unittest
from datetime import datetime, timedelta, timezone

ABO_COMPAT = {
    'O': ['O', 'A', 'B', 'AB'],
    'A': ['A', 'AB'],
    'B': ['B', 'AB'],
    'AB': ['AB']
}

def is_abo_compatible(donor_blood: str, recipient_blood: str) -> bool:
    """
    Unit 1: Biological filter. Returns True if donor blood is compatible
    with recipient blood type, False otherwise.
    """
    if not donor_blood or not recipient_blood:
        return False
    allowed = ABO_COMPAT.get(donor_blood.strip().upper(), [])
    return recipient_blood.strip().upper() in allowed


def calculate_priority_score(urgency: str, waitlist_months: int) -> int:
    """
    Unit 2: Algorithmic Scorer. Evaluates clinical urgency weight
    (Routine=10, Urgent=25, Critical=40) and adds accrued waiting time
    capped strictly at 30 points.
    """
    urgency_weights = {'Routine': 10, 'Urgent': 25, 'Critical': 40}
    base = urgency_weights.get(urgency, 0)
    capped_wait = max(0, min(waitlist_months, 30))
    return base + capped_wait


class AccountLockoutManager:
    """
    Unit 3: Security Unit. Handles failed login tracking and brute-force lockout.
    """
    def __init__(self, max_allowed_attempts=5):
        self.failed_attempts = 0
        self.max_allowed_attempts = max_allowed_attempts
        self.locked_until = None

    def record_failed_attempt(self, current_time=None):
        now = current_time or datetime.now(timezone.utc)
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_allowed_attempts:
            self.locked_until = now + timedelta(minutes=10)

    def is_account_locked(self, current_time=None) -> bool:
        now = current_time or datetime.now(timezone.utc)
        if self.locked_until and now < self.locked_until:
            return True
        return False

    def reset_attempts_on_success(self):
        self.failed_attempts = 0
        self.locked_until = None


class TestODMSCoreUnits(unittest.TestCase):

    def test_tc_abo_01_donor_o_universal(self):
        """TC-ABO-01: Universal donor O should be compatible with A, B, AB, and O"""
        self.assertTrue(is_abo_compatible('O', 'A'))
        self.assertTrue(is_abo_compatible('O', 'B'))
        self.assertTrue(is_abo_compatible('O', 'AB'))
        self.assertTrue(is_abo_compatible('O', 'O'))

    def test_tc_abo_02_incompatible_donor_a_to_b(self):
        """TC-ABO-02: Donor A to Recipient B must be strictly rejected"""
        self.assertFalse(is_abo_compatible('A', 'B'))

    def test_tc_abo_03_incompatible_donor_ab_to_o(self):
        """TC-ABO-03: Donor AB to Recipient O must be rejected"""
        self.assertFalse(is_abo_compatible('AB', 'O'))

    def test_tc_abo_04_universal_recipient_ab(self):
        """TC-ABO-04: Recipient AB can accept organs from all valid donors"""
        self.assertTrue(is_abo_compatible('A', 'AB'))
        self.assertTrue(is_abo_compatible('B', 'AB'))

    def test_tc_abo_05_invalid_empty_inputs(self):
        """TC-ABO-05: Robustness - empty or null blood type returns False"""
        self.assertFalse(is_abo_compatible('', 'A'))
        self.assertFalse(is_abo_compatible('O', ''))

    def test_tc_scr_01_critical_candidate_scoring(self):
        """TC-SCR-01: Critical (40) + 12 months wait = 52 points"""
        self.assertEqual(calculate_priority_score('Critical', 12), 52)

    def test_tc_scr_02_urgent_candidate_scoring(self):
        """TC-SCR-02: Urgent (25) + 5 months wait = 30 points"""
        self.assertEqual(calculate_priority_score('Urgent', 5), 30)

    def test_tc_scr_03_routine_candidate_scoring(self):
        """TC-SCR-03: Routine (10) + 0 months wait = 10 points"""
        self.assertEqual(calculate_priority_score('Routine', 0), 10)

    def test_tc_scr_04_wait_time_boundary_cap(self):
        """TC-SCR-04: Accrued wait time over 30 months must cap at 30 (Boundary Testing)"""
        # Critical base (40) + capped wait (30) = 70 points
        self.assertEqual(calculate_priority_score('Critical', 45), 70)

    def test_tc_scr_05_negative_wait_time_handling(self):
        """TC-SCR-05: Negative wait time should safely default to 0"""
        self.assertEqual(calculate_priority_score('Routine', -5), 10)

    def test_tc_sec_01_failed_attempts_increment(self):
        """TC-SEC-01: 3 bad attempts should increment count without locking"""
        manager = AccountLockoutManager(max_allowed_attempts=5)
        for _ in range(3):
            manager.record_failed_attempt()
        self.assertEqual(manager.failed_attempts, 3)
        self.assertFalse(manager.is_account_locked())

    def test_tc_sec_02_lockout_triggered_at_threshold(self):
        """TC-SEC-02: 5th bad attempt must lock the account"""
        manager = AccountLockoutManager(max_allowed_attempts=5)
        for _ in range(5):
            manager.record_failed_attempt()
        self.assertEqual(manager.failed_attempts, 5)
        self.assertTrue(manager.is_account_locked())
 
    def test_tc_sec_03_success_resets_lockout_state(self):
        """TC-SEC-03: Successful login resets attempts and unlocks account"""
        manager = AccountLockoutManager(max_allowed_attempts=5)
        for _ in range(3):
            manager.record_failed_attempt()
        manager.reset_attempts_on_success()
        self.assertEqual(manager.failed_attempts, 0)
        self.assertFalse(manager.is_account_locked())


if __name__ == '__main__':
    unittest.main()
