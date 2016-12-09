from flask import request, Response
import json

def jsonify(data):
    indent = None
    separators = (',', ':')

    if not request.is_xhr:
        indent = 2
        separators = (', ', ': ')

    return Response(
        (json.dumps(data, indent=indent, separators=separators, ensure_ascii=False), '\n'),
        mimetype='application/json'
    )