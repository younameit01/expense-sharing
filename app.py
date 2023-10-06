from flask import Flask, request, jsonify
from flask_migrate import Migrate
from database import db
from models import User, ExpenseGroup, GroupUser, Expense, ExpenseUserParticipant
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime

app = Flask(__name__)

app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/', methods=['GET'])
def health_check():
    return 'Application Running'


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(email=email, password=hashed_password,
                    name=name, phone=phone)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'data': new_user.serialize()}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        token = jwt.encode({"user_id": user.id},
                           app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"token": token, "data": user.serialize()}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401


@app.route('/groups', methods=['POST'])
def create_group():
    data = request.json
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({"message": "Name is required"}), 400

    user_id = get_user_from_token()
    user = User.query.get(user_id)

    group = ExpenseGroup(name=name, description=description)
    group_user = GroupUser(user=user, group=group)

    try:
        db.session.add(group)
        db.session.add(group_user)
        db.session.commit()
        return jsonify({"message": "Group created successfully", "data": group.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating group", "error": str(e)}), 500


@app.route('/groups/<int:group_id>/assign-user', methods=['POST'])
def assign_group_users(group_id):
    user_ids = request.json.get('user_ids', [])

    group = ExpenseGroup.query.get(group_id)

    if not group:
        return jsonify({'error': 'Group not found'}), 404

    users = User.query.filter(User.id.in_(user_ids)).all()

    if not users:
        return jsonify({'message': 'No valid users found'}), 400

    for user in users:
        existing_group_user = GroupUser.query.filter_by(
            user=user, group=group).first()

        if not existing_group_user:
            group_user = GroupUser(user=user, group=group)
            db.session.add(group_user)

    db.session.commit()
    return jsonify({'message': 'Users assigned to the group successfully'}), 200


@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()

    group_id = data['group_id']
    description = data['description']
    total_amount = data['total_amount']
    expense_opration = data['expense_operation']

    user_id = get_user_from_token()

    group = ExpenseGroup.query.get(group_id)
    if group is None:
        return jsonify({'message': 'Group not found'}), 404

    expense = Expense(
        group_id=group_id,
        description=description,
        paid_by=user_id,
        total_amount=total_amount,
        expense_operation=expense_opration
    )

    if expense_opration == 'equal':
        group_users = group.groups_users
        amount_per_user = total_amount / len(group_users.all())

        for group_user in group_users.filter(
                GroupUser.user_id != user_id):
            participant = ExpenseUserParticipant(
                expense=expense,
                user_id=group_user.user_id,
                amount=amount_per_user
            )
            db.session.add(participant)

    elif expense_opration == 'exact':
        exact_amounts_data = data.get('exact_amounts', [])
        total_exact_amount = sum(item.get('amount', 0)
                                 for item in exact_amounts_data)

        if total_exact_amount != total_amount:
            return jsonify({'message': 'Total specified amount does not match the expense total'}), 400

        users_in_group = group.groups_users.filter(
            GroupUser.user_id != user_id).all()
        users = [group_user.user for group_user in users_in_group]

        for item in exact_amounts_data:
            user_id = item.get('user_id')
            amount = item.get('amount')

            user = User.query.get(user_id)
            if user and user in users:
                participant = ExpenseUserParticipant(
                    expense=expense,
                    user=user,
                    amount=amount
                )
                db.session.add(participant)
            else:
                return jsonify({'message': f'Invalid user_id {user_id} or user not in the group'}), 400

    db.session.add(expense)
    db.session.commit()

    return jsonify({'message': 'Expense added successfully'}), 201


@app.route('/users/transactions', methods=['GET'])
def get_transactions():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    user_id = get_user_from_token()

    expenses = Expense.query.filter((Expense.paid_by == user_id) | (
        Expense.expenses_users_participants.any(user_id=user_id))).all()

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        expenses = expenses.filter(
            Expense.created_at.between(start_date, end_date))

    transactions = []

    for expense in expenses:
        participants = ExpenseUserParticipant.query.filter_by(
            expense_id=expense.id)
        pending_amounts = sum(
            participant.amount for participant in participants)

        transaction = {
            'expense_id': expense.id,
            'created_at': expense.created_at.strftime('%Y-%m-%d'),
            'description': expense.description,
            'total_amount': expense.total_amount,
            'group_name': expense.group.name,
            'pending_amounts': pending_amounts
        }
        transactions.append(transaction)

    return jsonify({"message": "Success", "data": transactions}), 200


def get_user_from_token():
    token = request.headers.get('Authorization')
    if not token:
        return None

    if token.startswith('Bearer '):
        token = token[7:]
    try:
        payload = jwt.decode(
            token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config["DEBUG"])
