from database import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), )

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone
        }


class ExpenseGroup(db.Model):
    __tablename__ = 'expenses_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class GroupUser(db.Model):
    __tablename__ = 'groups_users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey(
        'expenses_groups.id'), nullable=False)

    user = db.relationship('User', backref=db.backref(
        'groups_users', lazy='dynamic'))
    group = db.relationship('ExpenseGroup', backref=db.backref(
        'groups_users', lazy='dynamic'))


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_settled = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey(
        'expenses_groups.id'), nullable=False)
    expense_operation = db.Column(db.Enum('equal', 'exact'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[paid_by])
    group = db.relationship('ExpenseGroup', foreign_keys=[group_id])


class ExpenseUserParticipant(db.Model):
    __tablename__ = 'expenses_users_participants'

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey(
        'expenses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref(
        'expenses_users_participants', lazy='dynamic'))
    expense = db.relationship('Expense', backref=db.backref(
        'expenses_users_participants', lazy='dynamic'))
