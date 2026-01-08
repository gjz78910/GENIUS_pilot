"""Unit tests for Engineer model.

Tests organized by requirement:
- Requirement 2: Working Hours Management (working_hours attribute)
- Model validation and data normalization
"""

from __future__ import annotations

import unittest

from src.models.engineer import Engineer


class TestEngineer(unittest.TestCase):
    """Test cases for Engineer model."""

    # ========================================
    # Basic Model Functionality
    # ========================================

    def test_engineer_creation(self):
        """Test basic engineer creation with all attributes."""
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=8.0)
        self.assertEqual(engineer.id, 1)
        self.assertEqual(engineer.name, "Alice")
        self.assertEqual(engineer.location, "A")
        self.assertEqual(engineer.skills, ["repair"])
        self.assertEqual(engineer.working_hours, 8.0)

    def test_skills_normalized_to_lowercase(self):
        """Test that skills are automatically normalized to lowercase.
        
        Ensures case-insensitive skill matching.
        """
        engineer = Engineer(id=1, name="Bob", location="B", skills=["REPAIR", "Install"], working_hours=8.0)
        self.assertEqual(engineer.skills, ["repair", "install"])

    def test_default_skills_empty_list(self):
        """Test that default skills is an empty list."""
        engineer = Engineer(id=1, name="Charlie", location="C", working_hours=8.0)
        self.assertEqual(engineer.skills, [])

    # ========================================
    # REQUIREMENT 2: Working Hours
    # ========================================

    def test_default_working_hours(self):
        """Test that default working hours is 8.0.
        
        Requirement 2: Each engineer has working_hours (maximum capacity).
        """
        engineer = Engineer(id=1, name="Daisy", location="D", skills=["repair"])
        self.assertEqual(engineer.working_hours, 8.0)

    def test_custom_working_hours(self):
        """Test engineer with custom working hours.
        
        Requirement 2: Working hours can be customized (6, 8, 10, 12).
        """
        engineer = Engineer(id=1, name="Alice", location="A", skills=["repair"], working_hours=12.0)
        self.assertEqual(engineer.working_hours, 12.0)

    # ========================================
    # Additional Model Tests
    # ========================================

    def test_engineer_repr(self):
        """Test engineer string representation includes all attributes."""
        engineer = Engineer(id=1, name="Eve", location="E", skills=["repair"], working_hours=10.0)
        repr_str = repr(engineer)
        self.assertIn("id=1", repr_str)
        self.assertIn("name='Eve'", repr_str)
        self.assertIn("location='E'", repr_str)
        self.assertIn("working_hours=10.0", repr_str)

    def test_tuple_location(self):
        """Test engineer with tuple location."""
        engineer = Engineer(id=1, name="Frank", location=(1.0, 2.0), skills=["repair"], working_hours=8.0)
        self.assertEqual(engineer.location, (1.0, 2.0))


if __name__ == "__main__":
    unittest.main()
