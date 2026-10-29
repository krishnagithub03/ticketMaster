
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User, UserRole
from app.models.venue_hall import VenueHall
from app.models.seat import Seat, SeatType


seats_bp = Blueprint(
    "seats",
    __name__,
    url_prefix="/api/venues/halls/<string:venue_hall_id>/seats"
)


def _is_admin():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    return user is not None and user.role == UserRole.ADMIN


def _seat_to_dict(seat):
    return {
        "id": seat.id,
        "row_label": seat.row_label,
        "seat_number": seat.seat_number,
        "seat_type": seat.seat_type.value,
        "venue_hall_id": seat.venue_hall_id,
        "created_at": seat.created_at.isoformat() if seat.created_at else None,
        "updated_at": seat.updated_at.isoformat() if seat.updated_at else None
    }


@seats_bp.route("/", methods=["POST"])
@jwt_required()
def create_bulk_seats(venue_hall_id):
    """Create multiple seats for a venue hall."""

    if not _is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    venue_hall = db.session.get(VenueHall, venue_hall_id)
    if not venue_hall:
        return jsonify({"error": "Venue hall not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400

    seats_data = data.get("seats")

    if not isinstance(seats_data, list) or not seats_data:
        return jsonify({"error": "Seats must be a non-empty list"}), 400

    if len(seats_data) > 500:
        return jsonify({"error": "Maximum 500 seats per request"}), 400

    new_seats = []
    seen = set()

    for seat_info in seats_data:
        if not isinstance(seat_info, dict):
            return jsonify({
                "error": "Each seat must be a JSON object"
            }), 400

        row_label = seat_info.get("row_label")
        seat_number = seat_info.get("seat_number")

        if not isinstance(row_label, str):
            return jsonify({"error": "Row label must be a string"}), 400

        row_label = row_label.strip().upper()

        if not row_label.isalpha() or len(row_label) > 5:
            return jsonify({
                "error": "Row label must contain 1-5 alphabetic characters"
            }), 400

        if (
            isinstance(seat_number, bool)
            or not isinstance(seat_number, int)
            or seat_number <= 0
        ):
            return jsonify({
                "error": "Seat number must be a positive integer"
            }), 400

        try:
            seat_type = SeatType(
                seat_info.get("seat_type", SeatType.STANDARD.value)
            )
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid seat type"}), 400

        seat_key = (row_label, seat_number)

        if seat_key in seen:
            return jsonify({
                "error": (
                    f"Duplicate seat in request: "
                    f"Row {row_label}, Seat {seat_number}"
                )
            }), 400

        seen.add(seat_key)

        new_seats.append(
            Seat(
                venue_hall_id=venue_hall_id,
                row_label=row_label,
                seat_number=seat_number,
                seat_type=seat_type
            )
        )

    # Check existing seats in this hall.
    # The database unique constraint remains necessary for concurrent requests.
    existing_seats = Seat.query.filter(
        Seat.venue_hall_id == venue_hall_id,
        db.or_(
            *[
                db.and_(
                    Seat.row_label == row_label,
                    Seat.seat_number == seat_number
                )
                for row_label, seat_number in seen
            ]
        )
    ).all()

    if existing_seats:
        existing = existing_seats[0]
        return jsonify({
            "error": (
                f"Seat already exists: Row {existing.row_label}, "
                f"Seat {existing.seat_number}"
            )
        }), 409

    try:
        db.session.add_all(new_seats)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Seat conflict: one or more seats already exist"
        }), 409

    return jsonify({
        "message": f"{len(new_seats)} seats created successfully",
        "seats": [_seat_to_dict(seat) for seat in new_seats]
    }), 201


@seats_bp.route("/", methods=["GET"])
def get_seats(venue_hall_id):
    """Get all seats for a venue hall."""

    venue_hall = db.session.get(VenueHall, venue_hall_id)
    if not venue_hall:
        return jsonify({"error": "Venue hall not found"}), 404

    seats = (
        Seat.query
        .filter_by(venue_hall_id=venue_hall_id)
        .order_by(Seat.row_label, Seat.seat_number)
        .all()
    )

    return jsonify({
        "seats": [_seat_to_dict(seat) for seat in seats]
    }), 200


@seats_bp.route("/<string:seat_id>", methods=["GET"])
def get_seat(venue_hall_id, seat_id):
    """Get a specific seat in a venue hall."""

    venue_hall = db.session.get(VenueHall, venue_hall_id)
    if not venue_hall:
        return jsonify({"error": "Venue hall not found"}), 404

    seat = Seat.query.filter_by(
        venue_hall_id=venue_hall_id,
        id=seat_id
    ).first()

    if not seat:
        return jsonify({"error": "Seat not found"}), 404

    return jsonify({"seat": _seat_to_dict(seat)}), 200


@seats_bp.route("/<string:seat_id>", methods=["PATCH"])
@jwt_required()
def update_seat(venue_hall_id, seat_id):
    """Update a specific seat."""

    if not _is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    venue_hall = db.session.get(VenueHall, venue_hall_id)
    if not venue_hall:
        return jsonify({"error": "Venue hall not found"}), 404

    seat = Seat.query.filter_by(
        venue_hall_id=venue_hall_id,
        id=seat_id
    ).first()

    if not seat:
        return jsonify({"error": "Seat not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400

    allowed_fields = {"row_label", "seat_number", "seat_type"}

    if not data:
        return jsonify({"error": "At least one field is required"}), 400

    invalid_fields = set(data.keys()) - allowed_fields
    if invalid_fields:
        return jsonify({
            "error": "Unsupported fields",
            "fields": sorted(invalid_fields)
        }), 400

    # Validate everything before modifying the model.
    new_row_label = seat.row_label
    new_seat_number = seat.seat_number
    new_seat_type = seat.seat_type

    if "row_label" in data:
        row_label = data["row_label"]

        if not isinstance(row_label, str):
            return jsonify({"error": "Row label must be a string"}), 400

        row_label = row_label.strip().upper()

        if not row_label.isalpha() or len(row_label) > 5:
            return jsonify({
                "error": "Row label must contain 1-5 alphabetic characters"
            }), 400

        new_row_label = row_label

    if "seat_number" in data:
        seat_number = data["seat_number"]

        if (
            isinstance(seat_number, bool)
            or not isinstance(seat_number, int)
            or seat_number <= 0
        ):
            return jsonify({
                "error": "Seat number must be a positive integer"
            }), 400

        new_seat_number = seat_number

    if "seat_type" in data:
        try:
            new_seat_type = SeatType(data["seat_type"])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid seat type"}), 400

    seat.row_label = new_row_label
    seat.seat_number = new_seat_number
    seat.seat_type = new_seat_type

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "A seat with this row and number already exists"
        }), 409

    return jsonify({
        "message": "Seat updated successfully",
        "seat": _seat_to_dict(seat)
    }), 200


@seats_bp.route("/<string:seat_id>", methods=["DELETE"])
@jwt_required()
def delete_seat(venue_hall_id, seat_id):
    """Delete a seat if it is not referenced by other records."""

    if not _is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    venue_hall = db.session.get(VenueHall, venue_hall_id)
    if not venue_hall:
        return jsonify({"error": "Venue hall not found"}), 404

    seat = Seat.query.filter_by(
        venue_hall_id=venue_hall_id,
        id=seat_id
    ).first()

    if not seat:
        return jsonify({"error": "Seat not found"}), 404

    db.session.delete(seat)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": (
                "Cannot delete this seat because it is referenced by "
                "event inventory or booking records"
            )
        }), 409

    return jsonify({"message": "Seat deleted successfully"}), 200
