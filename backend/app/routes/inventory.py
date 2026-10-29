
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.user import User, UserRole
from app.models.event_occurance import EventOccurrence, EventOccurrenceStatus
from app.models.venue_hall import VenueHall
from app.models.seat import Seat
from app.models.event_seat_inventory import (
    EventSeatInventory,
    EventSeatInventoryStatus
)

inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/api/occurrences/<string:occurrence_id>/inventory"
)


def _is_admin():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    return user is not None and user.role == UserRole.ADMIN


def _inventory_to_dict(item):
    return {
        "id": item.id,
        "event_occurrence_id": item.event_occurrence_id,
        "seat_id": item.seat_id,
        "status": item.status.value,
        "price": str(item.price),
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None
    }


@inventory_bp.route("/", methods=["POST"])
@jwt_required()
def create_inventory(occurrence_id):
    if not _is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    occurrence = db.session.get(EventOccurrence, occurrence_id)
    if not occurrence:
        return jsonify({"error": "Event occurrence not found"}), 404

    if occurrence.status != EventOccurrenceStatus.SCHEDULED:
        return jsonify({
            "error": "Inventory can only be created for scheduled occurrences"
        }), 409

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400

    seats_data = data.get("seats")
    if not isinstance(seats_data, list) or not seats_data:
        return jsonify({"error": "Seats must be a non-empty list"}), 400

    if len(seats_data) > 500:
        return jsonify({"error": "Maximum 500 seats per request"}), 400

    # Resolve the hall from the occurrence's venue_hall_id.
    hall = db.session.get(VenueHall, occurrence.venue_hall_id)
    if not hall:
        return jsonify({"error": "Venue hall not found"}), 404

    new_items = []
    seen_seat_ids = set()

    for seat_info in seats_data:
        if not isinstance(seat_info, dict):
            return jsonify({
                "error": "Each seat must be a JSON object"
            }), 400

        seat_id = seat_info.get("seat_id")
        raw_price = seat_info.get("price")

        if not isinstance(seat_id, str) or not seat_id.strip():
            return jsonify({"error": "Each seat requires a seat_id"}), 400

        seat_id = seat_id.strip()

        if seat_id in seen_seat_ids:
            return jsonify({
                "error": f"Duplicate seat_id in request: {seat_id}"
            }), 400

        seen_seat_ids.add(seat_id)

        try:
            price = Decimal(str(raw_price))
        except (InvalidOperation, TypeError, ValueError):
            return jsonify({
                "error": f"Invalid price for seat {seat_id}"
            }), 400

        if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
            return jsonify({
                "error": "Price must be non-negative with at most 2 decimal places"
            }), 400

        seat = db.session.get(Seat, seat_id)
        if not seat or seat.venue_hall_id != hall.id:
            return jsonify({
                "error": f"Seat {seat_id} does not belong to this occurrence's hall"
            }), 400

        new_items.append(
            EventSeatInventory(
                event_occurrence_id=occurrence_id,
                seat_id=seat_id,
                status=EventSeatInventoryStatus.AVAILABLE,
                price=price
            )
        )

    try:
        db.session.add_all(new_items)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": (
                "One or more seats already have inventory for this occurrence"
            )
        }), 409

    return jsonify({
        "message": f"{len(new_items)} inventory records created",
        "inventory": [_inventory_to_dict(item) for item in new_items]
    }), 201
