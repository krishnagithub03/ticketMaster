from flask import Blueprint, jsonify, request
import urllib
from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.models.event_occurance import EventOccurrence, EventOccurrenceStatus
from app.extensions import db
from datetime import datetime, timezone
from app.models.venue_hall import VenueHall
from flask_jwt_extended import jwt_required, get_jwt_identity

events_bp = Blueprint('events', __name__, url_prefix='/api/events')


def _event_to_dict(event: Event) -> dict:
    return {
        "event_id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "image_url": event.image_url,
        "status": event.status.value,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat()
    }


@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can add events"}), 403
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400
    title = data.get('title')
    if not title or not isinstance(title, str) or len(title) > 100:
        return jsonify({"error": "Invalid title"}), 400
    title = title.strip()
    category = data.get('category')
    if not category or not isinstance(category, str) or len(category) > 50:
        return jsonify({"error": "Invalid category"}), 400
    category = category.strip()
    description = data.get('description')
    if description is not None:
        if not isinstance(description, str) or len(description) > 500:
            return jsonify({"error": "Invalid description"}), 400
        description = description.strip()
        if not description:
            return jsonify({"error": "Invalid description"}), 400
    image_url = data.get('image_url')
    if image_url and (not isinstance(image_url, str) or len(image_url) > 200) and image_url.strip() == "" and not image_url.startswith("https"):
        return jsonify({"error": "Invalid image URL"}), 400
    new_event = Event(
        title=title,
        description=data.get('description'),
        category=category,
        image_url=data.get('image_url'),
        status=EventStatus.DRAFT  # Default status is DRAFT
    )
    db.session.add(new_event)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while creating event"}), 500
    response = {
        "message": "Event created successfully",
        "event_id": new_event.id,
        "title": new_event.title,
        "description": new_event.description,
        "category": new_event.category,
        "image_url": new_event.image_url,
        "status": new_event.status.value,
        "created_at": new_event.created_at.isoformat(),
        "updated_at": new_event.updated_at.isoformat()
    }
    return jsonify(response), 201

@events_bp.route('/', methods=['GET'])
def get_events():
    stmt = (
        db.select(Event)
        .where(Event.status == EventStatus.PUBLISHED)
        .order_by(Event.created_at.desc())
    )

    published_events_list = db.session.scalars(stmt).all()

    response = {
        "events": [_event_to_dict(event) for event in published_events_list]
    }
    return jsonify(response), 200

@events_bp.route('/<string:event_id>', methods=['GET'])
def get_event(event_id):
    event = db.session.get(Event, event_id)
    if not event or event.status != EventStatus.PUBLISHED:
        return jsonify({"error": "Event not found"}), 404

    response = _event_to_dict(event)
    return jsonify(response), 200

@events_bp.route('/<string:event_id>', methods=['PATCH'])
@jwt_required()
def update_event(event_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can update events"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    title = data.get('title')
    if title is not None:
        if not isinstance(title, str) or len(title) > 100 or title.strip() == "":
            return jsonify({"error": "Invalid title"}), 400
        event.title = title.strip()

    category = data.get('category')
    if category is not None:
        if not isinstance(category, str) or len(category) > 50 or category.strip() == "":
            return jsonify({"error": "Invalid category"}), 400
        event.category = category.strip()

    description = data.get('description')
    if description is not None:
        if not isinstance(description, str) or len(description) > 500 or description.strip() == "":
            return jsonify({"error": "Invalid description"}), 400
        event.description = description.strip()

    image_url = data.get('image_url')
    if image_url is not None:
        if not isinstance(image_url, str) or len(image_url) > 200 or image_url.strip() == "" or urllib.parse.urlparse(image_url).scheme not in ("http", "https"):
            return jsonify({"error": "Invalid image URL"}), 400
        event.image_url = image_url.strip()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while updating event"}), 500

    response = _event_to_dict(event)
    return jsonify(response), 200

@events_bp.route('/<string:event_id>/publish', methods=['POST'])
@jwt_required()
def publish_event(event_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can publish events"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.status != EventStatus.DRAFT:
        return jsonify({"error": "Only draft events can be published"}), 400

    event.status = EventStatus.PUBLISHED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while publishing event"}), 500

    response = _event_to_dict(event)
    return jsonify(response), 200

@events_bp.route('/<string:event_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_event(event_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can cancel events"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.status != EventStatus.PUBLISHED:
        return jsonify({"error": "Only published events can be cancelled"}), 400

    event.status = EventStatus.CANCELLED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while cancelling event"}), 500

    response = _event_to_dict(event)
    return jsonify(response), 200

@events_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_all_events_admin():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can view all events"}), 403

    stmt = db.select(Event).order_by(Event.created_at.desc())
    all_events_list = db.session.scalars(stmt).all()

    response = {
        "events": [_event_to_dict(event) for event in all_events_list]
    }
    return jsonify(response), 200

@events_bp.route('/<string:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can delete events"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while deleting event"}), 500

    return jsonify({"message": "Event deleted successfully"}), 200

@events_bp.route('/<string:event_id>/occurrences', methods=['POST'])
@jwt_required()
def create_event_occurrence(event_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can add event occurrences"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.status != EventStatus.DRAFT:
        return jsonify({"error": "Cannot add occurrences to a published or cancelled event"}), 400
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400
    venue_hall_id = data.get('venue_hall_id')
    if not venue_hall_id or not isinstance(venue_hall_id, str) or len(venue_hall_id) > 32:
        return jsonify({"error": "Invalid venue hall ID"}), 400
    if not db.session.get(VenueHall, venue_hall_id):
        return jsonify({"error": "Venue hall not found"}), 404
    starts_at = data.get('starts_at')
    if not starts_at or not isinstance(starts_at, str):
        return jsonify({"error": "Invalid start time"}), 400
    ends_at = data.get('ends_at')
    if not ends_at or not isinstance(ends_at, str):
        return jsonify({"error": "Invalid end time"}), 400
    if datetime.fromisoformat(starts_at) >= datetime.fromisoformat(ends_at):
        return jsonify({"error": "End time must be after start time"}), 400

    starts_at = data.get("starts_at")
    ends_at = data.get("ends_at")

    if not isinstance(starts_at, str) or not starts_at.strip():
        return jsonify({"error": "Invalid start time"}), 400

    if not isinstance(ends_at, str) or not ends_at.strip():
        return jsonify({"error": "Invalid end time"}), 400

# Parse ISO 8601 datetime strings
    try:
        starts_at_dt = datetime.fromisoformat(starts_at.strip())
        ends_at_dt = datetime.fromisoformat(ends_at.strip())
    except ValueError:
        return jsonify({
        "error": "Invalid datetime format. Use ISO 8601 format."
    }), 400

# Ensure both datetimes include timezone information
    if (
    starts_at_dt.tzinfo is None
    or starts_at_dt.utcoffset() is None
    or ends_at_dt.tzinfo is None
    or ends_at_dt.utcoffset() is None
    ):
        return jsonify({
        "error": "Both start and end times must include a timezone."
        }), 400

# Convert both datetimes to UTC
    starts_at_utc = starts_at_dt.astimezone(timezone.utc)
    ends_at_utc = ends_at_dt.astimezone(timezone.utc)

# Validate chronological order
    if ends_at_utc <= starts_at_utc:
        return jsonify({
        "error": "End time must be after start time."
        }), 400
    event_occurrence = EventOccurrence(
        event_id=event_id,
        venue_hall_id=venue_hall_id,
        starts_at=starts_at_utc,
        ends_at=ends_at_utc,
        status=EventOccurrenceStatus.SCHEDULED 
    )
    db.session.add(event_occurrence)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while creating event occurrence"}), 500
    return jsonify({"message": "Event occurrence created successfully"}), 201

@events_bp.route('/<string:event_id>/occurrences', methods=['GET'])
def get_event_occurrences(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.status != EventStatus.PUBLISHED:
        return jsonify({"error": "Occurrences can only be retrieved for published events"}), 400
    stmt = (
        db.select(EventOccurrence)
        .where(
            EventOccurrence.event_id == event_id,
            EventOccurrence.status == EventOccurrenceStatus.SCHEDULED
        )
        .order_by(EventOccurrence.starts_at.asc())
    )

    occurrences_list = db.session.scalars(stmt).all()

    response = {
        "event_id": event.id,
        "occurrences": [
            {
                "occurrence_id": occurrence.id,
                "venue_hall_id": occurrence.venue_hall_id,
                "starts_at": occurrence.starts_at.isoformat(),
                "ends_at": occurrence.ends_at.isoformat(),
                "status": occurrence.status.value,
                "created_at": occurrence.created_at.isoformat(),
                "updated_at": occurrence.updated_at.isoformat()
            }
            for occurrence in occurrences_list
        ]
    }
    return jsonify(response), 200

@events_bp.route('/<string:event_id>/occurrences/<string:occurrence_id>', methods=['GET'])
def get_event_occurrence(event_id, occurrence_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.status != EventStatus.PUBLISHED:
        return jsonify({"error": "Occurrences can only be retrieved for published events"}), 404
    occurrence = db.session.get(EventOccurrence, occurrence_id)
    if not occurrence or occurrence.event_id != event_id:
        return jsonify({"error": "Occurrence not found for this event"}), 404
    if occurrence.status != EventOccurrenceStatus.SCHEDULED:
        return jsonify({"error": "Occurrence is not scheduled"}), 404
    response = {
        "occurrence_id": occurrence.id,
        "venue_hall_id": occurrence.venue_hall_id,
        "starts_at": occurrence.starts_at.isoformat(),
        "ends_at": occurrence.ends_at.isoformat(),
        "status": occurrence.status.value,
        "created_at": occurrence.created_at.isoformat(),
        "updated_at": occurrence.updated_at.isoformat()
    }
    return jsonify(response), 200

@events_bp.route(
    '/<string:event_id>/occurrences/<string:occurrence_id>',
    methods=['PATCH']
)
@jwt_required()
def update_event_occurrence(event_id, occurrence_id):
    # 1. Authenticate and authorize admin
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user is None or user.role != UserRole.ADMIN:
        return jsonify({
            "error": "Unauthorized, only admin can update event occurrences"
        }), 403

    # 2. Validate parent event
    event = db.session.get(Event, event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.status != EventStatus.DRAFT:
        return jsonify({
            "error": "Only occurrences of draft events can be updated"
        }), 400

    # 3. Validate occurrence and ownership
    occurrence = db.session.get(EventOccurrence, occurrence_id)

    if not occurrence or occurrence.event_id != event_id:
        return jsonify({
            "error": "Occurrence not found for this event"
        }), 404

    if occurrence.status != EventOccurrenceStatus.SCHEDULED:
        return jsonify({
            "error": "Only scheduled occurrences can be updated"
        }), 409

    # 4. Validate request body
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    allowed_fields = {"starts_at", "ends_at", "venue_hall_id"}

    if not data or not set(data.keys()).issubset(allowed_fields):
        return jsonify({
            "error": "Provide at least one valid field: starts_at, ends_at, venue_hall_id"
        }), 400

    # Keep proposed values local until all validation passes
    new_starts_at = occurrence.starts_at
    new_ends_at = occurrence.ends_at
    new_venue_hall_id = occurrence.venue_hall_id

    # 5. Validate start time if provided
    if "starts_at" in data:
        starts_at = data["starts_at"]

        if not isinstance(starts_at, str) or not starts_at.strip():
            return jsonify({"error": "Invalid start time"}), 400

        try:
            new_starts_at = datetime.fromisoformat(starts_at.strip())
        except ValueError:
            return jsonify({
                "error": "Invalid start time format. Use ISO 8601."
            }), 400

        if (
            new_starts_at.tzinfo is None
            or new_starts_at.utcoffset() is None
        ):
            return jsonify({
                "error": "Start time must include a timezone"
            }), 400

        new_starts_at = new_starts_at.astimezone(timezone.utc)

    # 6. Validate end time if provided
    if "ends_at" in data:
        ends_at = data["ends_at"]

        if not isinstance(ends_at, str) or not ends_at.strip():
            return jsonify({"error": "Invalid end time"}), 400

        try:
            new_ends_at = datetime.fromisoformat(ends_at.strip())
        except ValueError:
            return jsonify({
                "error": "Invalid end time format. Use ISO 8601."
            }), 400

        if (
            new_ends_at.tzinfo is None
            or new_ends_at.utcoffset() is None
        ):
            return jsonify({
                "error": "End time must include a timezone"
            }), 400

        new_ends_at = new_ends_at.astimezone(timezone.utc)

    # 7. Validate final start/end combination
    if new_ends_at <= new_starts_at:
        return jsonify({
            "error": "End time must be after start time"
        }), 400

    # 8. Validate venue hall if provided
    if "venue_hall_id" in data:
        venue_hall_id = data["venue_hall_id"]

        if (
            not isinstance(venue_hall_id, str)
            or not venue_hall_id.strip()
            or len(venue_hall_id) > 32
        ):
            return jsonify({"error": "Invalid venue hall ID"}), 400

        venue_hall_id = venue_hall_id.strip()

        venue_hall = db.session.get(VenueHall, venue_hall_id)

        if not venue_hall:
            return jsonify({"error": "Venue hall not found"}), 404

        new_venue_hall_id = venue_hall_id

    # 9. Apply changes only after validation succeeds
    occurrence.starts_at = new_starts_at
    occurrence.ends_at = new_ends_at
    occurrence.venue_hall_id = new_venue_hall_id

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Log the exception server-side in production
        return jsonify({
            "error": "Error occurred while updating event occurrence"
        }), 500

    # 10. Return updated resource
    return jsonify({
        "message": "Occurrence updated successfully",
        "occurrence": {
            "occurrence_id": occurrence.id,
            "event_id": occurrence.event_id,
            "venue_hall_id": occurrence.venue_hall_id,
            "starts_at": occurrence.starts_at.isoformat(),
            "ends_at": occurrence.ends_at.isoformat(),
            "status": occurrence.status.value,
            "updated_at": occurrence.updated_at.isoformat()
        }
    }), 200

@events_bp.route('/<string:event_id>/occurrences/<string:occurrence_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_event_occurrence(event_id, occurrence_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None or user.role != UserRole.ADMIN:
        return jsonify({"error": "Unauthorized, only admin can cancel event occurrences"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.status == EventStatus.CANCELLED:
        return jsonify({"error": "Occurrences can only be cancelled for draft events"}), 400

    occurrence = db.session.get(EventOccurrence, occurrence_id)
    if not occurrence or occurrence.event_id != event_id:
        return jsonify({"error": "Occurrence not found for this event"}), 404
    if occurrence.status != EventOccurrenceStatus.SCHEDULED:
        return jsonify({"error": "Only scheduled occurrences can be cancelled"}), 409

    occurrence.status = EventOccurrenceStatus.CANCELLED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error occurred while cancelling event occurrence"}), 500

    response = {
        "message": "Event occurrence cancelled successfully",
        "occurrence_id": occurrence.id,
        "event_id": occurrence.event_id,
        "venue_hall_id": occurrence.venue_hall_id,
        "starts_at": occurrence.starts_at.isoformat(),
        "ends_at": occurrence.ends_at.isoformat(),
        "status": occurrence.status.value,
        "created_at": occurrence.created_at.isoformat(),
        "updated_at": occurrence.updated_at.isoformat()
    }
    return jsonify(response), 200
