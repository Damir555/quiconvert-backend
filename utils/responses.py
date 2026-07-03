from flask import jsonify


def error_response(message, status=500):
    return jsonify({
        "success": False,
        "error": message
    }), status
