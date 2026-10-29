
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.extensions import db
from app.models.user import User, UserRole
from app.models.venue import Venue
from app.models.venue_hall import VenueHall


venues_bp = Blueprint("venues", __name__, url_prefix="/api/venues")


# --------------------------------------------------
# Reusable helpers
# --------------------------------------------------

def _is_admin():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    return user is not None and user.role == UserRole.ADMIN


def _venue_to_dict(venue):
    return {
        "venue_id": venue.id,
        "name": venue.name,
        "description": venue.description,
        "address_line": venue.address_line,
        "city": venue.city,
        "state": venue.state,
        "country": venue.country,
        "postal_code": venue.postal_code,
        "latitude": venue.latitude,
        "longitude": venue.longitude,
    }


def _hall_to_dict(hall):
    return {
        "hall_id": hall.id,
        "venue_id": hall.venue_id,
        "name": hall.name,
        "capacity": hall.capacity,
        "hall_type": hall.hall_type,
    }


def _validate_string(data, field, max_length, required=False):
    value = data.get(field)

    if value is None:
        if required:
            return None, f"{field} is required"
        return None, None

    if not isinstance(value, str):
        return None, f"{field} must be a string"

    value = value.strip()

    if required and not value:
        return None, f"{field} cannot be empty"

    if len(value) > max_length:
        return None, f"{field} must not exceed {max_length} characters"

    return value, None


def _validate_coordinates(latitude, lon):
    # Both must be supplied together.
    if (latitude is None) != (lon is None):
        return "Latitude and longitudeitude must be provided together"

    if latitude is None:
        return None

    # bool is a subclass of int in Python, so reject it explicitly.
    if (
        isinstance(latitude, bool)
        or not isinstance(latitude, (int, float))
        or not -90 <= latitude <= 90
    ):
        return "Invalid latitudeitude"

    if (
        isinstance(lon, bool)
        or not isinstance(lon, (int, float))
        or not -180 <= lon <= 180
    ):
        return "Invalid longitudeitude"

    return None


# --------------------------------------------------
# 1. CREATE VENUE
# POST /api/venues/
# --------------------------------------------------

@venues_bp.route("/", methods=["POST"])
@jwt_required()
def create_venue():
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    allowed = {
        "name", "description", "address_line", "city",
        "state", "country", "postal_code", "latitude", "longitude"
    }

    if not set(data).issubset(allowed):
        return jsonify({"error": "Unsupported fields provided"}), 400

    limits = {
        "name": 150,
        "address_line": 255,
        "city": 100,
        "state": 100,
        "country": 100,
        "postal_code": 20,
    }

    values = {}
    for field, limit in limits.items():
        value, error = _validate_string(
            data, field, limit, required=True
        )
        if error:
            return jsonify({"error": error}), 400
        values[field] = value

    description, error = _validate_string(
        data, "description", 1000
    )
    if error:
        return jsonify({"error": error}), 400

    latitude = data.get("latitude")
    lon = data.get("longitude")

    coordinate_error = _validate_coordinates(latitude, lon)
    if coordinate_error:
        return jsonify({"error": coordinate_error}), 400

    venue = Venue(
        **values,
        description=description,
        latitude=latitude,
        longitude=lon,
    )

    db.session.add(venue)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Venue conflicts with existing data"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create venue"}), 500

    return jsonify({
        "message": "Venue created successfully",
        "venue": _venue_to_dict(venue),
    }), 201


# --------------------------------------------------
# 2. LIST VENUES (PUBLIC)
# GET /api/venues/?page=1&per_page=20
# --------------------------------------------------

@venues_bp.route("/", methods=["GET"])
def get_venues():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid pagination parameters"}), 400

    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({
            "error": "page must be >= 1 and per_page must be between 1 and 100"
        }), 400

    stmt = (
        db.select(Venue)
        .order_by(Venue.name.asc(), Venue.id.asc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    venues = db.session.scalars(stmt).all()
    total = db.session.scalar(
        db.select(func.count()).select_from(Venue)
    )

    return jsonify({
        "venues": [_venue_to_dict(v) for v in venues],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        },
    }), 200


# --------------------------------------------------
# 3. GET VENUE BY ID (PUBLIC)
# GET /api/venues/<venue_id>
# --------------------------------------------------

@venues_bp.route("/<string:venue_id>", methods=["GET"])
def get_venue(venue_id):
    venue = db.session.get(Venue, venue_id)

    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    halls = db.session.scalars(
        db.select(VenueHall)
        .where(VenueHall.venue_id == venue_id)
        .order_by(VenueHall.name.asc())
    ).all()

    response = _venue_to_dict(venue)
    response["halls"] = [_hall_to_dict(h) for h in halls]

    return jsonify(response), 200


# --------------------------------------------------
# 4. UPDATE VENUE
# PATCH /api/venues/<venue_id>
# --------------------------------------------------

@venues_bp.route("/<string:venue_id>", methods=["PATCH"])
@jwt_required()
def update_venue(venue_id):
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    allowed = {
        "name", "description", "address_line", "city",
        "state", "country", "postal_code", "latitude", "longitude"
    }

    if not data or not set(data).issubset(allowed):
        return jsonify({
            "error": "Provide at least one valid field to update"
        }), 400

    limits = {
        "name": 150,
        "address_line": 255,
        "city": 100,
        "state": 100,
        "country": 100,
        "postal_code": 20,
    }

    updates = {}

    for field, limit in limits.items():
        if field in data:
            value, error = _validate_string(
                data, field, limit, required=True
            )
            if error:
                return jsonify({"error": error}), 400
            updates[field] = value

    if "description" in data:
        description, error = _validate_string(
            data, "description", 1000
        )
        if error:
            return jsonify({"error": error}), 400
        updates["description"] = description

    # If either coordinate is provided, validate the final pair.
    new_latitude = data.get("latitude", venue.latitude)
    new_lon = data.get("longitude", venue.longitude)

    if "latitude" in data or "longitude" in data:
        coordinate_error = _validate_coordinates(new_latitude, new_lon)
        if coordinate_error:
            return jsonify({"error": coordinate_error}), 400
        updates["latitude"] = new_latitude
        updates["longitude"] = new_lon

    for field, value in updates.items():
        setattr(venue, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Venue conflicts with existing data"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update venue"}), 500

    return jsonify({
        "message": "Venue updated successfully",
        "venue": _venue_to_dict(venue),
    }), 200


# --------------------------------------------------
# 5. DELETE VENUE
# DELETE /api/venues/<venue_id>
# --------------------------------------------------

@venues_bp.route("/<string:venue_id>", methods=["DELETE"])
@jwt_required()
def delete_venue(venue_id):
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    db.session.delete(venue)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Cannot delete venue while dependent records exist"
        }), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not delete venue"}), 500

    return jsonify({"message": "Venue deleted successfully"}), 200


# --------------------------------------------------
# 6. CREATE VENUE HALL
# POST /api/venues/<venue_id>/halls
# --------------------------------------------------

@venues_bp.route("/<string:venue_id>/halls", methods=["POST"])
@jwt_required()
def create_venue_hall(venue_id):
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    allowed = {"name", "capacity", "hall_type"}
    if not set(data).issubset(allowed):
        return jsonify({"error": "Unsupported fields provided"}), 400

    name, error = _validate_string(
        data, "name", 100, required=True
    )
    if error:
        return jsonify({"error": error}), 400

    capacity = data.get("capacity")
    if (
        isinstance(capacity, bool)
        or not isinstance(capacity, int)
        or capacity <= 0
    ):
        return jsonify({
            "error": "Capacity must be a positive integer"
        }), 400

    hall_type, error = _validate_string(
        data, "hall_type", 50, required=True
    )
    if error:
        return jsonify({"error": error}), 400

    # Friendly pre-check; the database unique constraint remains essential.
    duplicate = db.session.scalar(
        db.select(VenueHall).where(
            VenueHall.venue_id == venue_id,
            func.lower(VenueHall.name) == name.lower(),
        )
    )

    if duplicate:
        return jsonify({
            "error": "A hall with this name already exists at this venue"
        }), 409

    hall = VenueHall(
        venue_id=venue_id,
        name=name,
        capacity=capacity,
        hall_type=hall_type,
    )

    db.session.add(hall)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Hall conflicts with existing data"
        }), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create venue hall"}), 500

    return jsonify({
        "message": "Venue hall created successfully",
        "hall": _hall_to_dict(hall),
    }), 201


# --------------------------------------------------
# 7. LIST HALLS FOR A VENUE (PUBLIC)
# GET /api/venues/<venue_id>/halls
# --------------------------------------------------

@venues_bp.route("/<string:venue_id>/halls", methods=["GET"])
def get_venue_halls(venue_id):
    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    halls = db.session.scalars(
        db.select(VenueHall)
        .where(VenueHall.venue_id == venue_id)
        .order_by(VenueHall.name.asc())
    ).all()

    return jsonify({
        "venue_id": venue_id,
        "halls": [_hall_to_dict(h) for h in halls],
    }), 200


# --------------------------------------------------
# 8. UPDATE VENUE HALL
# PATCH /api/venues/<venue_id>/halls/<hall_id>
# --------------------------------------------------

@venues_bp.route(
    "/<string:venue_id>/halls/<string:hall_id>",
    methods=["PATCH"]
)
@jwt_required()
def update_venue_hall(venue_id, hall_id):
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    hall = db.session.get(VenueHall, hall_id)
    if not hall or hall.venue_id != venue_id:
        return jsonify({"error": "Venue hall not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format"}), 400

    allowed = {"name", "capacity", "hall_type"}
    if not data or not set(data).issubset(allowed):
        return jsonify({
            "error": "Provide at least one valid field to update"
        }), 400

    updates = {}

    if "name" in data:
        name, error = _validate_string(
            data, "name", 100, required=True
        )
        if error:
            return jsonify({"error": error}), 400
        updates["name"] = name

    if "capacity" in data:
        capacity = data["capacity"]
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity <= 0
        ):
            return jsonify({
                "error": "Capacity must be a positive integer"
            }), 400
        updates["capacity"] = capacity

    if "hall_type" in data:
        hall_type, error = _validate_string(
            data, "hall_type", 50, required=True
        )
        if error:
            return jsonify({"error": error}), 400
        updates["hall_type"] = hall_type

    new_name = updates.get("name", hall.name)

    duplicate = db.session.scalar(
        db.select(VenueHall).where(
            VenueHall.venue_id == venue_id,
            VenueHall.id != hall_id,
            func.lower(VenueHall.name) == new_name.lower(),
        )
    )

    if duplicate:
        return jsonify({
            "error": "A hall with this name already exists at this venue"
        }), 409

    for field, value in updates.items():
        setattr(hall, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Hall conflicts with existing data"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update venue hall"}), 500

    return jsonify({
        "message": "Venue hall updated successfully",
        "hall": _hall_to_dict(hall),
    }), 200


# --------------------------------------------------
# 9. DELETE VENUE HALL
# DELETE /api/venues/<venue_id>/halls/<hall_id>
# --------------------------------------------------

@venues_bp.route(
    "/<string:venue_id>/halls/<string:hall_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_venue_hall(venue_id, hall_id):
    if not _is_admin():
        return jsonify({"error": "Admin access required"}), 403

    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    hall = db.session.get(VenueHall, hall_id)
    if not hall or hall.venue_id != venue_id:
        return jsonify({"error": "Venue hall not found"}), 404

    db.session.delete(hall)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Cannot delete hall while dependent records exist"
        }), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not delete venue hall"}), 500

    return jsonify({"message": "Venue hall deleted successfully"}), 200

