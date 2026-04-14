from flask import Flask, jsonify, request
from flask_cors import CORS
from models import Session, Room, Booking, Guest, Transaction
from datetime import datetime
import random, string

app = Flask(__name__)
CORS(app)

def gen_booking_number():
    return 'BK' + ''.join(random.choices(string.digits, k=6))

# ===== ROOMS =====
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    db = Session()
    status = request.args.get('status')
    q = db.query(Room)
    if status:
        q = q.filter(Room.status == status)
    rooms = q.all()
    db.close()
    return jsonify([{
        'id': r.id,
        'room_number': r.room_number,
        'building': r.building,
        'floor': r.floor,
        'room_type': r.room_type,
        'price_night': r.price_night,
        'price_month': r.price_month,
        'status': r.status
    } for r in rooms])

@app.route('/api/rooms/stats', methods=['GET'])
def room_stats():
    db = Session()
    total = db.query(Room).count()
    occupied = db.query(Room).filter(Room.status=='occupied').count()
    available = db.query(Room).filter(Room.status=='available').count()
    maintenance = db.query(Room).filter(Room.status=='maintenance').count()
    monthly = db.query(Room).filter(Room.status=='monthly').count()
    db.close()
    return jsonify({
        'total': total,
        'occupied': occupied,
        'available': available,
        'maintenance': maintenance,
        'monthly': monthly
    })

# ===== CHECKIN =====
@app.route('/api/checkin', methods=['POST'])
def checkin():
    db = Session()
    data = request.json
    booking = Booking(
        booking_number=gen_booking_number(),
        room_number=data['room_number'],
        guest_name=data['guest_name'],
        guest_id_card=data.get('guest_id_card',''),
        guest_phone=data.get('guest_phone',''),
        check_in=datetime.fromisoformat(data['check_in']),
        check_out=datetime.fromisoformat(data['check_out']),
        payment_method=data.get('payment_method','cash'),
        total_amount=data.get('total_amount',0),
        status='confirmed'
    )
    db.add(booking)
    room = db.query(Room).filter(Room.room_number==data['room_number']).first()
    if room:
        room.status = 'occupied'
    guest = db.query(Guest).filter(Guest.id_card==data.get('guest_id_card')).first()
    if guest:
        guest.visit_count += 1
        guest.last_visit = datetime.now()
    else:
        db.add(Guest(
            name=data['guest_name'],
            id_card=data.get('guest_id_card',''),
            phone=data.get('guest_phone',''),
            last_visit=datetime.now()
        ))
    db.commit()
    db.close()
    return jsonify({'success': True, 'booking_number': booking.booking_number})

# ===== CHECKOUT =====
@app.route('/api/checkout', methods=['POST'])
def checkout():
    db = Session()
    data = request.json
    booking = db.query(Booking).filter(
        Booking.room_number==data['room_number'],
        Booking.status=='confirmed'
    ).first()
    if booking:
        booking.status = 'departed'
    room = db.query(Room).filter(Room.room_number==data['room_number']).first()
    if room:
        room.status = 'available'
    db.commit()
    db.close()
    return jsonify({'success': True})

# ===== BOOKINGS =====
@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    db = Session()
    status = request.args.get('status')
    q = db.query(Booking)
    if status:
        q = q.filter(Booking.status==status)
    bookings = q.order_by(Booking.created_at.desc()).limit(50).all()
    db.close()
    return jsonify([{
        'id': b.id,
        'booking_number': b.booking_number,
        'room_number': b.room_number,
        'guest_name': b.guest_name,
        'guest_phone': b.guest_phone,
        'check_in': b.check_in.isoformat() if b.check_in else None,
        'check_out': b.check_out.isoformat() if b.check_out else None,
        'total_amount': b.total_amount,
        'status': b.status,
        'payment_method': b.payment_method
    } for b in bookings])

# ===== GUESTS =====
@app.route('/api/guests/search', methods=['GET'])
def search_guests():
    db = Session()
    q = request.args.get('q','')
    guests = db.query(Guest).filter(
        (Guest.name.contains(q)) | (Guest.id_card.contains(q))
    ).all()
    db.close()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'id_card': g.id_card,
        'phone': g.phone,
        'visit_count': g.visit_count,
        'last_visit': g.last_visit.isoformat() if g.last_visit else None
    } for g in guests])

# ===== REPORTS =====
@app.route('/api/reports/revenue', methods=['GET'])
def revenue_report():
    db = Session()
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-01'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    bookings = db.query(Booking).filter(
        Booking.check_in >= date_from,
        Booking.check_in <= date_to,
        Booking.status != 'cancelled'
    ).all()
    total = sum(b.total_amount or 0 for b in bookings)
    db.close()
    return jsonify({
        'total_revenue': total,
        'booking_count': len(bookings),
        'from': date_from,
        'to': date_to
    })

# ===== HEALTH =====
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'vipat-hotel-api'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
