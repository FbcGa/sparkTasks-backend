from flask import Flask, request, jsonify, Blueprint
from api.models import db, User, List, Task
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)

@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():
    return jsonify({"message": "Hello! I'm a message from the backend"}), 200

# Register
@api.route('/register', methods=['POST'])
def register():
    body = request.json
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({"error": "All fields must be filled out"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "This email is already taken"}), 400

    try:
        password_hash = generate_password_hash(password)
        new_user = User(email=email, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        auth_token = create_access_token({"user_id": new_user.id})
        return jsonify({"user": new_user.serialize(), "auth": auth_token}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

# Login
@api.route('/login', methods=['POST'])
def login():
    body = request.json
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({"error": "Complete all fields"}), 400

    try:
        old_user = User.query.filter_by(email=email).first()
        if not old_user or not check_password_hash(old_user.password, password):
            return jsonify({"error": "Wrong data!"}), 400
        
        auth_token = create_access_token({"user_id": old_user.id})
        return jsonify({"user": old_user.serialize(), "auth": auth_token}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

# Add List
@api.route('/list', methods=['POST'])
@jwt_required()
def add_list():
    current_user = get_jwt_identity()
    body = request.json
    title = body.get('title')

    if not title:
        return jsonify({"error": "Please provide a title for the list"}), 400

    try:
        max_position = db.session.query(db.func.max(List.position)).filter_by(user_id=current_user['user_id']).scalar()
        new_position = (max_position + 1) if max_position is not None else 0

        new_list = List(title=title, user_id=current_user['user_id'], position=new_position)
        db.session.add(new_list)
        db.session.commit()

        return jsonify({"message": "List created successfully", "list": new_list.serialize()}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

# Get All Lists
@api.route('/list', methods=['GET'])
@jwt_required()
def get_all_list():
    try:
        current_user = get_jwt_identity()
        lists = List.query.filter_by(user_id=current_user['user_id']).order_by(List.position).all()
        serialize_list = [list.serialize() for list in lists]
        return jsonify({"lists": serialize_list}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

# Delete List
@api.route('/list/delete', methods=['DELETE'])
@jwt_required()
def delete_list():
    body = request.json
    list_id = body.get("id")
    current_user = get_jwt_identity()

    if not list_id:
        return jsonify({"error": "List ID not provided"}), 400

    list_delete = List.query.filter_by(id=list_id, user_id=current_user['user_id']).first()
    if not list_delete:
        return jsonify({"error": "List doesn't exist"}), 404

    try:
        db.session.delete(list_delete)
        db.session.commit()
        return jsonify({"message": "List deleted successfully"}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

# Change List Title
@api.route('/list/change', methods=['PUT'])
@jwt_required()
def change_title_list():
    body = request.json
    list_id = body.get("list_id")
    title = body.get("title")
    current_user = get_jwt_identity()

    if not list_id or not title:
        return jsonify({"error": "Missing arguments"}), 400

    updatelist = List.query.filter_by(id=list_id, user_id=current_user['user_id']).first()
    if not updatelist:
        return jsonify({"error": "List doesn't exist"}), 404

    try:
        updatelist.title = title
        db.session.commit()
        return jsonify({"list": updatelist.serialize()}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

# Add Task
@api.route('/task', methods=['POST'])
@jwt_required()
def add_task():
    current_user = get_jwt_identity()
    body = request.json
    text = body.get("text")
    list_id = body.get("list_id")

    if not text or not list_id:
        return jsonify({"error": "Text and list_id are required"}), 400

    list_exists = List.query.filter_by(id=list_id, user_id=current_user['user_id']).first()
    if not list_exists:
        return jsonify({"error": "List doesn't exist"}), 404

    try:
        max_position = db.session.query(db.func.max(Task.position)).filter_by(list_id=list_id).scalar()
        new_position = (max_position + 1) if max_position is not None else 0

        new_task = Task(text=text, list_id=list_id, user_id=current_user['user_id'], position=new_position)
        db.session.add(new_task)
        db.session.commit()

        return jsonify({"message": "Task added successfully", "task": new_task.serialize()}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

# Delete Task
@api.route('/task/delete', methods=['DELETE'])
@jwt_required()
def delete_task():
    current_user = get_jwt_identity()
    body = request.json
    task_id = body.get("id")
    list_id = body.get("listId")

    if not task_id or not list_id:
        return jsonify({"error": "Parameters are missing"}), 400

    task = Task.query.filter_by(id=task_id, list_id=list_id, user_id=current_user['user_id']).first()
    if not task:
        return jsonify({"error": "Task doesn't exist"}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

@api.route('/task/change', methods=['PUT'])
@jwt_required()
def change_title_task():
    body = request.json
    task_id = body.get("taskId", None)
    list_id = body.get("listId",None)
    text = body.get("newTitle",None)
    current_user = get_jwt_identity()

    if not task_id or not list_id or not text:
        return jsonify({"error": "Missing arguments"}), 400

    task = Task.query.filter_by(id=task_id, list_id=list_id, user_id=current_user['user_id']).first()
    if not task:
        return jsonify({"error": "Task doesn't exist"}), 404

    try:
        task.text = text
        db.session.commit()
        return jsonify({"list": task.serialize()}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500
    
# Reorder Lists
@api.route('/list/reorder', methods=['PUT'])
@jwt_required()
def reorder_lists():
    current_user = get_jwt_identity()
    body = request.json
    new_order = body.get("new_order")

    if not new_order:
        return jsonify({"error": "No order provided"}), 400

    lists = List.query.filter_by(user_id=current_user['user_id']).all()
    list_ids = [lst.id for lst in lists]

    if set(new_order) != set(list_ids):
        return jsonify({"error": "Invalid list IDs in order"}), 400

    try:
        for position, list_id in enumerate(new_order):
            lst = List.query.filter_by(id=list_id, user_id=current_user['user_id']).first()
            if lst:
                lst.position = position

        db.session.commit()
        return jsonify({"message": "Lists reordered successfully"}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

@api.route('/tasks/reorder', methods=['PUT'])
@jwt_required()
def reorder_tasks():
    current_user = get_jwt_identity()
    body = request.json
    list_id = body.get("list_id")
    ordered_task_ids = body.get("ordered_task_ids")

    if list_id is None or ordered_task_ids is None:
        return jsonify({"error": "Missing parameters"}), 400

    task_list = List.query.filter_by(id=list_id, user_id=current_user['user_id']).first()
    if not task_list:
        return jsonify({"error": "List does not exist or unauthorized"}), 404

    try:
        tasks = Task.query.filter_by(list_id=list_id).all()
        task_dict = {task.id: task for task in tasks}

        for position, task_id in enumerate(ordered_task_ids):
            task = task_dict.get(task_id)
            if task:
                task.position = position

        db.session.commit()
        return jsonify({"message": "Tasks reordered successfully"}), 200

    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500

@api.route('/task/move', methods=['PUT'])
@jwt_required()
def move_task():
    current_user = get_jwt_identity()
    body = request.json
    from_list_id = body.get("fromListId")
    to_list_id = body.get("toListId")
    updated_from_tasks = body.get("updatedFromTasks")
    updated_to_tasks = body.get("updatedToTasks")

    if from_list_id is None or to_list_id is None or updated_from_tasks is None or updated_to_tasks is None:
        return jsonify({"error": "Faltan parámetros"}), 400

    from_list = List.query.filter_by(id=from_list_id, user_id=current_user['user_id']).first()
    to_list = List.query.filter_by(id=to_list_id, user_id=current_user['user_id']).first()

    if not from_list or not to_list:
        return jsonify({"error": "Lista de origen o destino no encontrada o sin autorización"}), 404

    try:
        for task_data in updated_from_tasks:
            task = Task.query.get(task_data["id"])
            task.position = task_data["position"]
            task.list_id = from_list_id

        for task_data in updated_to_tasks:
            task = Task.query.get(task_data["id"])
            task.position = task_data["position"]
            task.list_id = to_list_id

        db.session.commit()

        updated_lists = List.query.filter_by(user_id=current_user['user_id']).all()
        return jsonify({"updatedLists": [list.serialize() for list in updated_lists]}), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500
