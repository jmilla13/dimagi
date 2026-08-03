from unittest.mock import patch

import requests
from django.test import TestCase

from .models import LocationSubmission


class FormTemplateTests(TestCase):
    def test_form_posts_to_form_route(self):
        response = self.client.get("/remote-location-form/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/remote-location-form/"')


class NormalizedDataPageTests(TestCase):
    def test_normalized_data_page_lists_sanitized_submissions(self):
        LocationSubmission.objects.create(
            email=" User@Example.com ",
            location="  New   York  ",
            latitude=40.7128,
            longitude=-74.0060,
        )

        response = self.client.get("/normalized-data/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user@example.com")
        self.assertContains(response, "New York")
        self.assertContains(response, "40.7128")
        self.assertContains(response, "-74.006")

    def test_normalized_data_page_shows_local_time_for_each_submission(self):
        LocationSubmission.objects.create(
            email="user@example.com",
            location="New York",
            latitude=40.7128,
            longitude=-74.0060,
            timezone_name="America/New_York",
        )

        response = self.client.get("/normalized-data/")

        self.assertContains(response, "Local time")
        self.assertContains(response, "America/New_York")


class FormViewTests(TestCase):
    @patch("location_form_app.views.requests.get")
    def test_post_saves_email_and_coordinates(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "geonames": [{"lat": "51.50853", "lng": "-0.12574"}]
        }

        response = self.client.post(
            "/remote-location-form/",
            {"email": "user@example.com", "location": "London"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LocationSubmission.objects.count(), 1)
        self.assertContains(response, "Your location update was saved successfully.")

        submission = LocationSubmission.objects.get()
        self.assertEqual(submission.email, "user@example.com")
        self.assertEqual(submission.location, "London")
        self.assertEqual(submission.latitude, 51.50853)
        self.assertEqual(submission.longitude, -0.12574)

    @patch("location_form_app.views.requests.get")
    def test_multiple_updates_for_same_email_replace_the_existing_record(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "geonames": [{"lat": "51.50853", "lng": "-0.12574"}]
        }

        self.client.post("/remote-location-form/", {"email": "user@example.com", "location": "London"})
        self.client.post("/remote-location-form/", {"email": "user@example.com", "location": "Paris"})

        submissions = LocationSubmission.objects.filter(email="user@example.com")
        self.assertEqual(submissions.count(), 1)
        self.assertEqual(submissions.get().location, "Paris")

    @patch("location_form_app.views.requests.get")
    def test_successful_post_shows_success_message(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "geonames": [{"lat": "51.50853", "lng": "-0.12574"}]
        }

        response = self.client.post(
            "/remote-location-form/",
            {"email": "user@example.com", "location": "London"},
            follow=True,
        )

        self.assertContains(response, "Your location update was saved successfully.")

    def test_missing_fields_show_failure_message(self):
        response = self.client.post(
            "/remote-location-form/",
            {"email": "", "location": ""},
        )

        self.assertContains(response, "Please enter both your email and location.")

    @patch("location_form_app.views.requests.get")
    def test_post_shows_error_when_geo_lookup_fails(self, mock_get):
        mock_get.side_effect = requests.RequestException("boom")

        response = self.client.post(
            "/remote-location-form/",
            {"email": "user@example.com", "location": "London"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to find a valid location in GeoNames.")

    @patch("location_form_app.views.requests.get")
    def test_api_returns_error_when_geo_lookup_fails(self, mock_get):
        mock_get.side_effect = requests.RequestException("boom")

        response = self.client.post(
            "/api/locations/",
            '{"email": "user@example.com", "location": "London"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unable to find a valid location in GeoNames.", response.content.decode())
