import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import LocationSubmission


def sanitize_text(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    return " ".join(value.split())[:255]


def sanitize_email(value):
    value = sanitize_text(value)
    return value.lower() if value else ""


def geo_lookup(location):
    try:
        response = requests.get(
            "https://secure.geonames.org/searchJSON",
            params={"q": location, "maxRows": 1, "fuzzy": 0.8, "username": "dimagi"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.getLogger(__name__).error("Error during geolocation lookup: %s", e)
        return None, None, None, None

    geonames = data.get("geonames", [])
    if not geonames:
        return None, None, None, None

    entry = geonames[0]
    latitude = entry.get("lat")
    longitude = entry.get("lng")
    if latitude is None or longitude is None:
        return None, None, None, None

    timezone_name, local_time = lookup_timezone(latitude, longitude)
    return latitude, longitude, timezone_name, local_time


def lookup_timezone(latitude, longitude):
    try:
        response = requests.get(
            "https://secure.geonames.org/timezoneJSON",
            params={"lat": latitude, "lng": longitude, "username": "dimagi"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.getLogger(__name__).error("Error during timezone lookup: %s", e)
        return None, None

    timezone_name = data.get("timezoneId")
    if not timezone_name:
        return None, None

    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        return timezone_name, None

    local_time = datetime.now(timezone.utc).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    return timezone_name, local_time


def _create_submission(email, location):
    email = sanitize_email(email)
    location = sanitize_text(location)
    latitude, longitude, timezone_name, local_time = geo_lookup(location)
    if latitude is None or longitude is None:
        raise ValueError("Unable to find a valid location in GeoNames. Please double check your spelling.")

    submission, created = LocationSubmission.objects.update_or_create(
        email=email,
        defaults={
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "timezone_name": timezone_name,
            "local_time": local_time,
        },
    )
    return submission


@require_http_methods(["GET", "POST"])
def form_view(request):
    if request.method == "POST":
        email = sanitize_email(request.POST.get("email", ""))
        location = sanitize_text(request.POST.get("location", ""))

        if email and location:
            try:
                _create_submission(email, location)
            except ValueError as exc:
                return render(
                    request,
                    "form.html",
                    {
                        "error": str(exc),
                        "email": email,
                        "location": location,
                    },
                )

            return render(
                request,
                "form.html",
                {
                    "success": "Your location update was saved successfully.",
                    "email": email,
                    "location": location,
                },
            )

        return render(
            request,
            "form.html",
            {
                "error": "Please enter both your email and location.",
                "email": email,
                "location": location,
            },
        )

    return render(request, "form.html")


@csrf_exempt
@require_http_methods(["POST"])
def api_update_location(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    email = sanitize_email(payload.get("email") or "")
    location = sanitize_text(payload.get("location") or "")

    if not email or not location:
        return JsonResponse({"error": "email and location are required"}, status=400)

    try:
        submission = _create_submission(email, location)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "id": submission.id,
            "email": submission.email,
            "location": submission.location,
            "latitude": submission.latitude,
            "longitude": submission.longitude,
        },
        status=201,
    )


@require_http_methods(["GET"])
def api_get_user_locations(request, email=None):
    query = sanitize_text(request.GET.get("q", ""))
    if email:
        submissions = LocationSubmission.objects.filter(email=email).order_by("-created_at")
    elif query:
        submissions = LocationSubmission.objects.filter(
            email__icontains=query
        ) | LocationSubmission.objects.filter(location__icontains=query)
        submissions = submissions.order_by("-created_at")
    else:
        submissions = LocationSubmission.objects.all().order_by("-created_at")

    data = [
        {
            "id": submission.id,
            "email": submission.email,
            "location": submission.location,
            "latitude": submission.latitude,
            "longitude": submission.longitude,
            "created_at": submission.created_at.isoformat(),
        }
        for submission in submissions
    ]
    return JsonResponse({"query": query or email or "", "locations": data})


@require_http_methods(["GET"])
def map_view(request):
    submissions = LocationSubmission.objects.exclude(latitude__isnull=True, longitude__isnull=True).order_by("-created_at")
    locations = [
        {
            "id": submission.id,
            "email": submission.email,
            "location": submission.location,
            "latitude": float(submission.latitude),
            "longitude": float(submission.longitude),
        }
        for submission in submissions
    ]
    return render(request, "map.html", {"locations": json.dumps(locations)})


@require_http_methods(["GET"])
def normalized_data_view(request):
    submissions = LocationSubmission.objects.order_by("-created_at")
    normalized = []
    for submission in submissions:
        normalized.append(
            {
                "id": submission.id,
                "email": sanitize_email(submission.email),
                "location": sanitize_text(submission.location),
                "latitude": submission.latitude,
                "longitude": submission.longitude,
                "timezone_name": submission.timezone_name,
                "local_time": submission.local_time,
                "created_at": submission.created_at.isoformat(),
            }
        )
    return render(request, "normalized_data.html", {"submissions": normalized})
