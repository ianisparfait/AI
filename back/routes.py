from flask import Flask, jsonify, request
import json

import services.generate_image
import services.generate_sound
import services.generate_tags
import services.generate_video

generator_sound = services.generate_sound.MusicGenerator()
generator_image = services.generate_image.ImageGenerator()
generator_tags = services.generate_tags.TagsGenerator()
editor = services.generate_video.VideoEditor()

def get_document(reqt, field):
    request_json = reqt.get_json()
    data = request_json.get(field)

    return data

def get_documents(reqt, fields, required=True):
    try:
        request_json = reqt.get_json()

        if request_json is None:
            raise ValueError("The request body is not valid JSON")

        result = {}
        missing_fields = []

        for field in fields:
            value = request_json.get(field)
            if value is None and required:
                missing_fields.append(field)
            result[field] = value
        
        if missing_fields and required:
            raise ValueError(f"Missing required fields : {', '.join(missing_fields)}")
            
        return result
        
    except Exception as e:
        raise ValueError(f"Error reading JSON : {str(e)}")

def init_routes(app):

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"message": "pong"})

    @app.route("/generate/image/prompt", methods=["POST"])
    def generate_image_prompt():
        data = get_document(request, "prompt")
        if not data:
            return jsonify({f"error": "Missing data to run: Image generation from a prompt"})

        try:
            generation_id, output_path = generator_image.generate_image_from_prompt(data)

            return jsonify({
                'generation_id': generation_id,
                'file_path': str(output_path)
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/generate/image/image", methods=["POST"])
    def generate_image_image():
        data = get_document(request, "prompt")
        if not data:
            return jsonify({f"error": "Missing data to run: Image generation from an image"})

        #...

    @app.route("/generate/sound", methods=["POST"])
    def generate_sound():
        data = get_document(request, "description")
        if not data:
            return jsonify({f"error": "Missing data to run: Music generation"})

        try:             
            generation_id, output_path = generator_sound.generate_music(data)
            
            return jsonify({
                'generation_id': generation_id,
                'file_path': str(output_path)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/generate/tags", methods=["POST"])
    def generate_tags():
        data = get_documents(request, ["image_prompt", "sound_description"])
        image_prompt = data['image_prompt']
        sound_description = data['sound_description']

        try:             
            tags = generator_tags.generate_tags(image_prompt, sound_description)
            
            return jsonify({
                'tags': tags,
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
